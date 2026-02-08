# 🎙️ GroqVOICE - AI Voice Interview Agent

A real-time voice-powered AI interview agent using **Groq** for STT/LLM and **Deepgram** for TTS, with a modern Next.js frontend.

## ✨ Features

- 🎤 **Real-time voice interviews** - Natural conversation flow with AI interviewer
- 🧠 **Intelligent responses** - Powered by Groq's Llama 3.3 70B
- 🗣️ **Natural speech synthesis** - High-quality TTS via Deepgram Aura
- 📊 **AI-powered analysis** - Get detailed feedback and hiring recommendations
- 🌐 **Modern web interface** - Built with Next.js, TypeScript, and Tailwind CSS

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🎤 Browser    │───▶│   Groq STT      │───▶│   Groq LLM      │
│   (WebAudio)    │    │   (Whisper)     │    │  (Llama 3.3)    │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐             │
│   🔊 Browser    │◀───│  Deepgram TTS   │◀────────────┘
│   (Playback)    │    │    (Aura)       │
└─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology | Details |
|-------|------------|---------|
| **Frontend** | Next.js 15 | React, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI | Python async server |
| **STT** | Groq | `whisper-large-v3-turbo` |
| **LLM** | Groq | `llama-3.3-70b-versatile` |
| **TTS** | Deepgram | `aura-asteria-en` |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Groq API Key](https://console.groq.com)
- [Deepgram API Key](https://deepgram.com)

### 1. Clone & Setup Backend

```bash
# Clone the repo
git clone https://github.com/yourusername/GroqVOICE.git
cd GroqVOICE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
```

### 3. Setup Frontend

```bash
cd frontend
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
GroqVOICE/
├── main.py              # FastAPI server
├── config.py            # Configuration management
├── stt_groq.py          # Speech-to-Text (Groq Whisper)
├── llm_groq.py          # Interview LLM agent (Groq Llama)
├── tts_deepgram.py      # Text-to-Speech (Deepgram Aura)
├── audio_utils.py       # Audio recording and playback
├── interview_agent.py   # CLI orchestrator
├── test_setup.py        # Setup verification script
├── requirements.txt     # Python dependencies
└── frontend/            # Next.js frontend
    ├── src/
    │   ├── app/         # App router pages
    │   └── components/  # React components
    └── package.json
```

## 🎤 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/voices` | List available TTS voices |
| `POST` | `/api/interview/start` | Start new interview |
| `GET` | `/api/interview/{id}/state` | Get interview state |
| `POST` | `/api/interview/{id}/respond` | Send audio response |
| `POST` | `/api/interview/{id}/end` | End interview |
| `POST` | `/api/interview/{id}/analyze` | Generate AI analysis |

## 🔊 Available TTS Voices

| Voice | Gender | Accent | Style |
|-------|--------|--------|-------|
| `asteria` | Female | American | Warm |
| `luna` | Female | American | Soft |
| `stella` | Female | American | Professional |
| `athena` | Female | British | Refined |
| `orion` | Male | American | Deep |
| `arcas` | Male | American | Conversational |
| `perseus` | Male | American | Confident |

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔑 API Keys

- **Groq**: Free tier at [console.groq.com](https://console.groq.com)
- **Deepgram**: $200 free credits at [deepgram.com](https://deepgram.com)
