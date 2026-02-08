"""Audio recording and playback utilities."""

import io
import wave
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from typing import Optional, Callable
from config import config


class AudioRecorder:
    """Record audio from microphone."""

    def __init__(self, sample_rate: int = None, channels: int = 1):
        self.sample_rate = sample_rate or config.AUDIO_SAMPLE_RATE
        self.channels = channels
        self.recording = False
        self.audio_data = []

    def record(self, duration: float = 5.0) -> bytes:
        """
        Record audio for a fixed duration.

        Args:
            duration: Recording duration in seconds

        Returns:
            WAV audio bytes
        """
        print(f"🎤 Recording for {duration}s...")

        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16,
        )
        sd.wait()

        print("✅ Recording complete")
        return self._to_wav_bytes(audio)

    def record_with_silence_detection(
        self,
        max_duration: float = 30.0,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        min_duration: float = 1.0,
    ) -> bytes:
        """
        Record until silence is detected.

        Args:
            max_duration: Maximum recording time
            silence_threshold: RMS threshold for silence
            silence_duration: How long silence must last to stop
            min_duration: Minimum recording duration

        Returns:
            WAV audio bytes
        """
        print("🎤 Recording (speak now, will stop after silence)...")

        audio_chunks = []
        silence_samples = 0
        required_silence_samples = int(silence_duration * self.sample_rate / 1024)
        min_samples = int(min_duration * self.sample_rate / 1024)

        def callback(indata, frames, time, status):
            nonlocal silence_samples

            audio_chunks.append(indata.copy())

            # Check for silence
            rms = np.sqrt(np.mean(indata**2))
            if rms < silence_threshold and len(audio_chunks) > min_samples:
                silence_samples += 1
            else:
                silence_samples = 0

            if silence_samples >= required_silence_samples:
                raise sd.CallbackStop()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16,
                blocksize=1024,
                callback=callback,
            ):
                sd.sleep(int(max_duration * 1000))
        except sd.CallbackStop:
            pass

        if audio_chunks:
            audio = np.concatenate(audio_chunks)
            print("✅ Recording complete")
            return self._to_wav_bytes(audio)

        return b""

    def _to_wav_bytes(self, audio: np.ndarray) -> bytes:
        """Convert numpy array to WAV bytes."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio.tobytes())
        buffer.seek(0)
        return buffer.read()


class AudioPlayer:
    """Play audio from bytes or file."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate

    def play_bytes(self, audio_bytes: bytes, sample_rate: int = None):
        """
        Play audio from bytes (assumes linear16/PCM format).

        Args:
            audio_bytes: Raw audio data
            sample_rate: Sample rate of audio
        """
        rate = sample_rate or self.sample_rate
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(audio, rate)
        sd.wait()

    def play_wav_bytes(self, wav_bytes: bytes):
        """
        Play WAV format audio bytes.

        Args:
            wav_bytes: WAV file bytes
        """
        buffer = io.BytesIO(wav_bytes)
        rate, audio = wavfile.read(buffer)
        sd.play(audio, rate)
        sd.wait()

    def play_file(self, file_path: str):
        """
        Play audio from file.

        Args:
            file_path: Path to audio file
        """
        rate, audio = wavfile.read(file_path)
        sd.play(audio, rate)
        sd.wait()


# Singleton instances
recorder = AudioRecorder()
player = AudioPlayer()


if __name__ == "__main__":
    print("🔈 Audio Utilities Module")
    print("   Recorder: Ready")
    print("   Player: Ready")
    print(f"   Recording Sample Rate: {config.AUDIO_SAMPLE_RATE}")
