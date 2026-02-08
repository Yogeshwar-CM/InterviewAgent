"""Text-to-Speech using Deepgram's Aura model (HTTP API)."""

import httpx
from config import config


# Available Aura voices
AURA_VOICES = {
    "asteria": "aura-asteria-en",  # Female, American, warm
    "luna": "aura-luna-en",  # Female, American, soft
    "stella": "aura-stella-en",  # Female, American, professional
    "athena": "aura-athena-en",  # Female, British, refined
    "hera": "aura-hera-en",  # Female, American, mature
    "orion": "aura-orion-en",  # Male, American, deep
    "arcas": "aura-arcas-en",  # Male, American, conversational
    "perseus": "aura-perseus-en",  # Male, American, confident
    "angus": "aura-angus-en",  # Male, Irish, friendly
    "orpheus": "aura-orpheus-en",  # Male, American, warm
    "helios": "aura-helios-en",  # Male, British, authoritative
    "zeus": "aura-zeus-en",  # Male, American, powerful
}


class DeepgramTTS:
    """Text-to-Speech synthesis using Deepgram's Aura model."""

    BASE_URL = "https://api.deepgram.com/v1/speak"

    def __init__(self, voice: str = "asteria"):
        self.api_key = config.DEEPGRAM_API_KEY
        self.model = AURA_VOICES.get(voice, config.DEEPGRAM_TTS_MODEL)

    def set_voice(self, voice: str):
        """Change the TTS voice."""
        if voice in AURA_VOICES:
            self.model = AURA_VOICES[voice]
        else:
            raise ValueError(
                f"Unknown voice: {voice}. Available: {list(AURA_VOICES.keys())}"
            )

    def synthesize(
        self, text: str, encoding: str = "linear16", sample_rate: int = 24000
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to convert to speech
            encoding: Audio encoding (linear16, mp3, opus, flac, alaw, mulaw)
            sample_rate: Sample rate for audio

        Returns:
            Audio bytes
        """
        url = f"{self.BASE_URL}?model={self.model}&encoding={encoding}&sample_rate={sample_rate}"

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

        # Deepgram TTS API expects JSON body with "text" key
        payload = {"text": text}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.content

    async def synthesize_async(
        self, text: str, encoding: str = "linear16", sample_rate: int = 24000
    ) -> bytes:
        """
        Synthesize speech from text (asynchronous).

        Args:
            text: Text to convert to speech
            encoding: Audio encoding
            sample_rate: Sample rate

        Returns:
            Audio bytes
        """
        url = f"{self.BASE_URL}?model={self.model}&encoding={encoding}&sample_rate={sample_rate}"

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"text": text}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.content

    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        encoding: str = "linear16",
        sample_rate: int = 24000,
    ):
        """
        Synthesize speech and save to file.

        Args:
            text: Text to convert
            output_path: Path to save audio file
            encoding: Audio encoding
            sample_rate: Sample rate
        """
        audio_bytes = self.synthesize(text, encoding, sample_rate)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path


# Singleton instance
tts = DeepgramTTS(voice="asteria")


if __name__ == "__main__":
    print("🔊 Deepgram TTS Module")
    print(f"   Model: {tts.model}")
    print(f"   Available voices: {list(AURA_VOICES.keys())}")
    print("   Ready for synthesis!")
