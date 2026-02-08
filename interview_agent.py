"""Main Interview Agent - orchestrates STT, LLM, and TTS."""

import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import config
from stt_groq import stt
from llm_groq import llm
from tts_deepgram import tts
from audio_utils import recorder, player

console = Console()


class InterviewAgent:
    """Voice-powered interview agent using Groq + Deepgram."""

    def __init__(self, voice: str = "asteria"):
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.recorder = recorder
        self.player = player

        # Set TTS voice
        self.tts.set_voice(voice)

        self.running = False
        self.transcript = []

    def speak(self, text: str):
        """Convert text to speech and play it."""
        console.print(f"[bold blue]🤖 Interviewer:[/bold blue] {text}")
        self.transcript.append({"role": "interviewer", "content": text})

        # Synthesize and play
        audio = self.tts.synthesize(text)
        self.player.play_bytes(audio)

    def listen(self) -> str:
        """Record audio and transcribe it."""
        console.print("[dim]🎤 Listening...[/dim]")

        # Record with silence detection
        audio_bytes = self.recorder.record_with_silence_detection(
            max_duration=60.0,
            silence_threshold=0.01,
            silence_duration=2.0,
            min_duration=1.0,
        )

        if not audio_bytes:
            return ""

        # Transcribe
        text = self.stt.transcribe_bytes(audio_bytes, format="wav")

        console.print(f"[bold green]👤 Candidate:[/bold green] {text}")
        self.transcript.append({"role": "candidate", "content": text})

        return text

    def run_interview(
        self, candidate_name: str = "Candidate", role: str = "Software Engineer"
    ):
        """Run a complete interview session."""
        console.print(
            Panel.fit(
                f"[bold]🎯 Interview Session[/bold]\n"
                f"Candidate: {candidate_name}\n"
                f"Role: {role}",
                border_style="cyan",
            )
        )

        self.running = True
        self.transcript = []

        try:
            # Start the interview
            opening = self.llm.start_interview(candidate_name, role)
            self.speak(opening)

            # Interview loop
            while self.running and not self.llm.is_interview_complete:
                # Listen to candidate
                response = self.listen()

                if not response:
                    self.speak("I didn't catch that. Could you please repeat?")
                    continue

                # Check for exit commands
                if any(
                    word in response.lower()
                    for word in ["exit", "quit", "stop interview", "end interview"]
                ):
                    self.speak(
                        "Thank you for your time. The interview is now concluded."
                    )
                    break

                # Generate and speak response
                interviewer_response = self.llm.respond(response)
                self.speak(interviewer_response)

                # Small pause between turns
                time.sleep(0.5)

            self.running = False

            # Print summary
            console.print("\n")
            console.print(
                Panel.fit(
                    f"[bold green]✅ Interview Complete[/bold green]\n"
                    f"Questions asked: {self.llm.question_count}\n"
                    f"Total exchanges: {len(self.transcript)}",
                    border_style="green",
                )
            )

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ Interview interrupted by user[/yellow]")
            self.running = False
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            self.running = False
            raise

        return self.transcript

    def stop(self):
        """Stop the current interview."""
        self.running = False


def main():
    """Run the interview agent."""
    console.print(
        Panel.fit(
            "[bold cyan]🎙️ Voice Interview Agent[/bold cyan]\n"
            "Powered by Groq (STT + LLM) & Deepgram (TTS)",
            border_style="cyan",
        )
    )

    # Validate configuration
    if not config.validate():
        console.print("[red]Please set up your API keys in .env[/red]")
        return

    # Get interview details
    console.print("\n[bold]Interview Setup[/bold]")
    name = (
        console.input("Candidate name [dim](default: Candidate)[/dim]: ").strip()
        or "Candidate"
    )
    role = (
        console.input("Role [dim](default: Software Engineer)[/dim]: ").strip()
        or "Software Engineer"
    )

    # Select voice
    console.print(
        "\n[dim]Available voices: asteria, luna, stella, orion, arcas, perseus[/dim]"
    )
    voice = (
        console.input("Interviewer voice [dim](default: asteria)[/dim]: ").strip()
        or "asteria"
    )

    console.print("\n[yellow]Starting interview in 3 seconds...[/yellow]")
    time.sleep(3)

    # Run interview
    agent = InterviewAgent(voice=voice)
    transcript = agent.run_interview(name, role)

    # Save transcript
    if transcript:
        with open("interview_transcript.txt", "w") as f:
            for entry in transcript:
                f.write(f"{entry['role'].upper()}: {entry['content']}\n\n")
        console.print("[dim]Transcript saved to interview_transcript.txt[/dim]")


if __name__ == "__main__":
    main()
