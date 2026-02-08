"""FastAPI server for Voice Interview Agent."""

import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from config import config
from stt_groq import stt
from llm_groq import GroqLLM
from tts_deepgram import DeepgramTTS


# Request/Response models
class InterviewStartRequest(BaseModel):
    candidate_name: str = "Candidate"
    role: str = "Software Engineer"
    voice: str = "asteria"


class InterviewStartResponse(BaseModel):
    session_id: str
    opening_message: str
    opening_audio_base64: str
    state: dict


class InterviewState(BaseModel):
    question_count: int
    main_questions_asked: int
    satisfaction_level: str
    can_prompt_end: bool
    is_complete: bool


# Session management
sessions: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the app."""
    # Startup
    print("🚀 Voice Interview Server starting...")
    if not config.validate():
        print("⚠️ Warning: Configuration incomplete!")
    yield
    # Shutdown
    print("👋 Server shutting down...")
    sessions.clear()


app = FastAPI(
    title="Voice Interview Agent",
    description="AI-powered voice interview system using Groq + Deepgram",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Voice Interview Agent",
        "version": "1.0.0",
    }


@app.get("/api/voices")
async def get_voices():
    """Get available TTS voices."""
    from tts_deepgram import AURA_VOICES

    return {"voices": list(AURA_VOICES.keys())}


@app.post("/api/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    """Start a new interview session."""
    import uuid

    session_id = str(uuid.uuid4())

    # Create new LLM instance for this session
    llm = GroqLLM()
    tts = DeepgramTTS(voice=request.voice)

    # Start interview
    opening_message = llm.start_interview(request.candidate_name, request.role)

    # Generate opening audio
    audio_bytes = tts.synthesize(opening_message)
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Store session
    sessions[session_id] = {
        "llm": llm,
        "tts": tts,
        "candidate_name": request.candidate_name,
        "role": request.role,
        "transcript": [{"role": "interviewer", "content": opening_message}],
    }

    return InterviewStartResponse(
        session_id=session_id,
        opening_message=opening_message,
        opening_audio_base64=audio_base64,
        state=llm.get_state(),
    )


@app.get("/api/interview/{session_id}/state")
async def get_interview_state(session_id: str):
    """Get current interview state."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "state": session["llm"].get_state(),
        "transcript": session["transcript"],
    }


@app.post("/api/interview/{session_id}/end")
async def end_interview(session_id: str):
    """End an interview session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    return {
        "message": "Interview ended",
        "transcript": session["transcript"],
        "state": session["llm"].get_state(),
    }


@app.post("/api/interview/{session_id}/analyze")
async def analyze_interview(session_id: str):
    """Generate AI analysis of the interview."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    transcript = session["transcript"]
    role = session.get("role", "Software Engineer")
    candidate_name = session.get("candidate_name", "Candidate")

    # Format transcript for analysis
    transcript_text = "\n".join(
        [f"{entry['role'].upper()}: {entry['content']}" for entry in transcript]
    )

    from groq import Groq
    import json
    import re

    client = Groq(api_key=config.GROQ_API_KEY)

    analysis_prompt = f"""Analyze this interview transcript and provide a comprehensive assessment.

CANDIDATE: {candidate_name}
ROLE: {role}

TRANSCRIPT:
{transcript_text}

Provide your analysis in this exact JSON format:
{{
    "overall_score": <number 0-100>,
    "recommendation": "<strong_hire|hire|maybe|no_hire>",
    "suitability": "<detailed 2-3 sentence assessment of whether this candidate is suited for the {role} position>",
    "summary": "<2-3 sentence overall summary of the interview>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "improvements": ["<area 1>", "<area 2>", "<area 3>"],
    "skills": {{
        "communication": <number 0-100>,
        "technical": <number 0-100>,
        "problem_solving": <number 0-100>,
        "confidence": <number 0-100>
    }},
    "detailed_feedback": "<paragraph with specific examples from the interview and actionable advice>",
    "hiring_rationale": "<clear explanation of why this candidate should or should not be hired for this specific role>"
}}

Be specific, reference actual responses from the interview, and provide constructive feedback.
Return ONLY the JSON object, no other text."""

    try:
        response = client.chat.completions.create(
            model=config.GROQ_LLM_MODEL,
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        analysis_text = response.choices[0].message.content

        # Parse JSON from response
        json_match = re.search(r"\{.*\}", analysis_text, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            analysis = json.loads(analysis_text)

        return {"analysis": analysis}

    except Exception as e:
        print(f"Analysis error: {e}")
        # Return default analysis on error
        return {
            "analysis": {
                "overall_score": 70,
                "recommendation": "maybe",
                "suitability": f"Unable to fully assess suitability for {role} due to analysis error.",
                "summary": "Interview completed but detailed analysis unavailable.",
                "strengths": ["Participated in interview", "Answered questions"],
                "improvements": ["Unable to determine specific improvements"],
                "skills": {
                    "communication": 70,
                    "technical": 70,
                    "problem_solving": 70,
                    "confidence": 70,
                },
                "detailed_feedback": "Analysis processing error occurred.",
                "hiring_rationale": "Further evaluation recommended.",
            }
        }


class RespondRequest(BaseModel):
    audio: str  # base64-encoded webm audio


@app.post("/api/interview/{session_id}/respond")
async def respond_to_audio(session_id: str, request: RespondRequest):
    """Process candidate audio and return interviewer response with audio."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    llm = session["llm"]
    tts = session["tts"]

    # Decode base64 audio
    audio_bytes = base64.b64decode(request.audio)

    # Transcribe
    transcript = stt.transcribe_bytes(audio_bytes, format="webm")

    if not transcript:
        raise HTTPException(status_code=422, detail="Could not transcribe audio")

    # Add candidate message to transcript
    session["transcript"].append({"role": "candidate", "content": transcript})

    # Generate interviewer response
    response = llm.respond(transcript)
    session["transcript"].append({"role": "interviewer", "content": response})

    # Synthesize audio
    response_audio = tts.synthesize(response)
    audio_base64 = base64.b64encode(response_audio).decode("utf-8")

    state = llm.get_state()

    return {
        "candidate_transcript": transcript,
        "interviewer_response": response,
        "audio": audio_base64,
        "state": state,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)
