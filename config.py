"""Configuration management for Voice Interview Agent."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # Groq Models
    GROQ_STT_MODEL: str = (
        "whisper-large-v3-turbo"  # Fast STT (distil-whisper decommissioned)
    )
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"  # Powerful LLM for interviews

    # Deepgram TTS Configuration
    DEEPGRAM_TTS_MODEL: str = "aura-asteria-en"  # Natural female voice
    DEEPGRAM_TTS_ENCODING: str = "linear16"
    DEEPGRAM_TTS_SAMPLE_RATE: int = 24000

    # Audio Configuration
    AUDIO_SAMPLE_RATE: int = 16000  # For recording/STT
    AUDIO_CHANNELS: int = 1

    # Interview Configuration
    MAX_QUESTIONS: int = int(os.getenv("MAX_QUESTIONS", "5"))
    INTERVIEW_TYPE: str = os.getenv("INTERVIEW_TYPE", "technical")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        errors = []

        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required")
        if not cls.DEEPGRAM_API_KEY:
            errors.append("DEEPGRAM_API_KEY is required")

        if errors:
            for error in errors:
                print(f"❌ Config Error: {error}")
            return False

        print("✅ Configuration validated successfully")
        return True


config = Config()
