"""LLM Interview Agent using Groq with AI-controlled interview completion."""

import json
import re
from typing import List, Dict, Optional
from groq import Groq
from config import config


INTERVIEW_SYSTEM_PROMPT = """You are an expert technical interviewer conducting a professional job interview via voice.

Your role:
- Conduct a natural, flowing conversation
- Ask clear questions and engage with their answers
- Ask follow-up questions when answers are interesting or need clarification
- Be professional but personable

Interview structure:
- Start with a warm greeting and introduce yourself briefly
- Ask about their background and experience (1 main question area)
- Ask 2-3 technical/behavioral questions based on the role
- Dig deeper with follow-ups when appropriate
- After covering 3-5 main topic areas with good discussion, naturally wrap up

Speaking style:
- Keep responses SHORT and conversational (2-3 sentences max)
- This is SPOKEN conversation, not written
- Respond with ONLY what you want to say - NO JSON, NO formatting
- Sound natural, like a real person talking"""


class GroqLLM:
    """LLM-powered interview agent using Groq with intelligent completion."""

    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_LLM_MODEL
        self.conversation_history: List[Dict[str, str]] = []
        self.question_count = 0
        self.main_questions_asked = 0
        self.max_questions = config.MAX_QUESTIONS
        self.interview_satisfied = False
        self.satisfaction_level = "gathering_info"

        # Initialize with system prompt
        self.system_prompt = INTERVIEW_SYSTEM_PROMPT

    def reset(self):
        """Reset the conversation for a new interview."""
        self.conversation_history = []
        self.question_count = 0
        self.main_questions_asked = 0
        self.interview_satisfied = False
        self.satisfaction_level = "gathering_info"

    def start_interview(
        self, candidate_name: str = "candidate", role: str = "Software Engineer"
    ) -> str:
        """
        Start a new interview session.

        Args:
            candidate_name: Name of the candidate
            role: Role being interviewed for

        Returns:
            Opening message from the interviewer
        """
        self.reset()

        # Create the opening prompt
        opening_prompt = f"""Start the interview. The candidate's name is {candidate_name} and they're interviewing for {role}. 
Give a warm, brief greeting and ask your first question about their background."""

        response = self._generate_response(opening_prompt)
        self.main_questions_asked = 1  # First main question area

        return response.strip()

    def respond(self, user_input: str) -> str:
        """
        Generate interviewer's response to candidate's answer.

        Args:
            user_input: Candidate's spoken response

        Returns:
            Interviewer's next response/question
        """
        # Add candidate's response to history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.question_count += 1

        # Build context for natural conversation
        if self.main_questions_asked >= 4:
            state_context = """The conversation is going well. You can start wrapping up soon.
If you feel you've learned enough about the candidate, thank them and conclude naturally.
Otherwise, ask one more question if needed."""
        elif self.main_questions_asked >= 2:
            state_context = """Continue the interview naturally. Acknowledge their answer briefly and either:
- Ask a follow-up if their answer needs clarification
- Move to a new main topic/question
Keep it conversational."""
        else:
            state_context = """Continue the interview. Acknowledge their response and ask your next question.
Build rapport and explore their experience."""

        response = self._generate_response(state_context)

        # Smarter question detection - look for substantive new topics
        # A new main question typically starts a new topic, not just a follow-up
        new_topic_indicators = [
            "tell me about",
            "can you describe",
            "what experience",
            "how would you",
            "walk me through",
            "what's your approach",
            "have you ever",
            "what do you think",
        ]

        response_lower = response.lower()
        is_new_main_question = any(
            ind in response_lower for ind in new_topic_indicators
        )

        if is_new_main_question and "?" in response:
            self.main_questions_asked += 1

        # Check for interview ending phrases
        ending_phrases = [
            "thank you for your time",
            "thank you for speaking",
            "best of luck",
            "pleasure speaking",
            "great talking",
            "enjoyed our conversation",
            "we'll be in touch",
        ]
        if any(phrase in response_lower for phrase in ending_phrases):
            self.interview_satisfied = True
            self.satisfaction_level = "satisfied"
        elif self.main_questions_asked >= 3:
            self.satisfaction_level = "almost_satisfied"

        return response.strip()

    def _generate_response(self, additional_instruction: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)

        if additional_instruction:
            messages.append({"role": "user", "content": additional_instruction})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )

        assistant_message = response.choices[0].message.content

        # Add to history (store raw for context)
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    def _parse_response(self, response: str) -> dict:
        """Parse the JSON response from the LLM."""
        # Method 1: Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Method 2: Try to find any JSON object in the response
        json_match = re.search(r"\{[^{}]*\"message\"[^{}]*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Method 3: Try to find JSON object with nested content
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                if "message" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass

        # Method 4: Try parsing the whole response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Method 5: Try to extract just the message field with regex
        message_match = re.search(r'"message"\s*:\s*"((?:[^"\\]|\\.)*)"', response)
        if message_match:
            # Unescape the message content
            msg = message_match.group(1)
            msg = msg.replace('\\"', '"').replace("\\n", "\n")
            return {"message": msg, "is_main_question": True}

        # Final fallback: use the raw response but clean it up
        clean = response.strip()
        # Remove any JSON-like prefixes/suffixes
        clean = re.sub(r"^```json\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
        clean = re.sub(
            r"^\s*\{[^}]*\}\s*$", "", clean
        )  # Remove if it's just a broken JSON
        clean = clean.strip()

        if clean:
            return {"message": clean, "is_main_question": False}
        else:
            return {
                "message": "Hello! Let's begin the interview.",
                "is_main_question": True,
            }

    @property
    def is_interview_complete(self) -> bool:
        """Check if interview has concluded."""
        return self.interview_satisfied

    @property
    def can_prompt_end(self) -> bool:
        """Check if we can prompt user to end (3+ main questions)."""
        return self.main_questions_asked >= 3

    def get_state(self) -> dict:
        """Get current interview state for frontend."""
        return {
            "question_count": self.question_count,
            "main_questions_asked": self.main_questions_asked,
            "satisfaction_level": self.satisfaction_level,
            "can_prompt_end": self.can_prompt_end,
            "is_complete": self.is_interview_complete,
        }


# Singleton instance
llm = GroqLLM()


if __name__ == "__main__":
    # Test the LLM
    print("🧠 Groq LLM Module")
    print(f"   Model: {config.GROQ_LLM_MODEL}")
    print(f"   Max Questions: {config.MAX_QUESTIONS}")

    # Quick test
    response = llm.start_interview("Alex", "Senior Software Engineer")
    print(f"\n📝 Opening:\n{response}")
    print(f"\n📊 State: {llm.get_state()}")
