"""Speech-to-Text using Groq's Whisper API."""

import io
import tempfile
from pathlib import Path
from groq import Groq
from config import config


class GroqSTT:
    """Speech-to-Text transcription using Groq's Whisper model."""

    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_STT_MODEL

    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe audio from a file path.

        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)

        Returns:
            Transcribed text
        """
        with open(audio_path, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                file=audio_file, model=self.model, response_format="text", language="en"
            )
        return transcription.strip()

    def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav") -> str:
        """
        Transcribe audio from bytes.

        Args:
            audio_bytes: Raw audio data
            format: Audio format (wav, mp3, etc.)

        Returns:
            Transcribed text
        """
        # Create a temp file since Groq SDK expects a file-like object with name
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            return self.transcribe_file(tmp.name)

    def transcribe_stream(self, audio_file) -> str:
        """
        Transcribe from a file-like object.

        Args:
            audio_file: File-like object with audio data

        Returns:
            Transcribed text
        """
        transcription = self.client.audio.transcriptions.create(
            file=audio_file, model=self.model, response_format="text", language="en"
        )
        return transcription.strip()


# Singleton instance
stt = GroqSTT()


if __name__ == "__main__":
    # Test the STT
    print("🎤 Groq STT Module")
    print(f"   Model: {config.GROQ_STT_MODEL}")
    print("   Ready for transcription!")
