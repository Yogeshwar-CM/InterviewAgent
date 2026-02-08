"""Test script to verify all components are working."""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_config():
    """Test configuration loading."""
    console.print("\n[bold]1️⃣ Testing Configuration...[/bold]")
    try:
        from config import config

        table = Table(show_header=False, box=None)
        table.add_row("GROQ_API_KEY", "✅ Set" if config.GROQ_API_KEY else "❌ Missing")
        table.add_row(
            "DEEPGRAM_API_KEY", "✅ Set" if config.DEEPGRAM_API_KEY else "❌ Missing"
        )
        table.add_row("STT Model", config.GROQ_STT_MODEL)
        table.add_row("LLM Model", config.GROQ_LLM_MODEL)
        table.add_row("TTS Model", config.DEEPGRAM_TTS_MODEL)
        console.print(table)

        return config.validate()
    except Exception as e:
        console.print(f"[red]❌ Config Error: {e}[/red]")
        return False


def test_groq_stt():
    """Test Groq STT connection."""
    console.print("\n[bold]2️⃣ Testing Groq STT (Whisper)...[/bold]")
    try:
        from stt_groq import stt

        console.print(f"   [dim]Model: {stt.model}[/dim]")
        console.print("   [green]✅ Groq STT client initialized[/green]")
        return True
    except Exception as e:
        console.print(f"   [red]❌ STT Error: {e}[/red]")
        return False


def test_groq_llm():
    """Test Groq LLM connection with a quick call."""
    console.print("\n[bold]3️⃣ Testing Groq LLM...[/bold]")
    try:
        from llm_groq import llm

        console.print(f"   [dim]Model: {llm.model}[/dim]")

        # Quick test
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=[{"role": "user", "content": "Say 'Hello' only."}],
            max_tokens=10,
        )
        result = response.choices[0].message.content
        console.print(f"   [dim]Test response: {result}[/dim]")
        console.print("   [green]✅ Groq LLM working[/green]")
        return True
    except Exception as e:
        console.print(f"   [red]❌ LLM Error: {e}[/red]")
        return False


def test_deepgram_tts():
    """Test Deepgram TTS with a quick synthesis."""
    console.print("\n[bold]4️⃣ Testing Deepgram TTS (Aura)...[/bold]")
    try:
        from tts_deepgram import tts

        console.print(f"   [dim]Model: {tts.model}[/dim]")

        # Quick synthesis test - use default linear16 encoding
        audio = tts.synthesize("Test")
        console.print(f"   [dim]Audio generated: {len(audio)} bytes[/dim]")
        console.print("   [green]✅ Deepgram TTS working[/green]")
        return True
    except Exception as e:
        console.print(f"   [red]❌ TTS Error: {e}[/red]")
        return False


def test_audio():
    """Test audio device availability."""
    console.print("\n[bold]5️⃣ Testing Audio Devices...[/bold]")
    try:
        import sounddevice as sd

        # List devices
        devices = sd.query_devices()
        default_input = sd.query_devices(kind="input")
        default_output = sd.query_devices(kind="output")

        console.print(f"   [dim]Input: {default_input['name']}[/dim]")
        console.print(f"   [dim]Output: {default_output['name']}[/dim]")
        console.print("   [green]✅ Audio devices available[/green]")
        return True
    except Exception as e:
        console.print(f"   [red]❌ Audio Error: {e}[/red]")
        return False


def main():
    """Run all tests."""
    console.print(
        Panel.fit(
            "[bold cyan]🔧 Voice Interview Agent - Setup Test[/bold cyan]",
            border_style="cyan",
        )
    )

    results = {
        "Configuration": test_config(),
        "Groq STT": test_groq_stt(),
        "Groq LLM": test_groq_llm(),
        "Deepgram TTS": test_deepgram_tts(),
        "Audio Devices": test_audio(),
    }

    # Summary
    console.print("\n")
    passed = sum(results.values())
    total = len(results)

    if passed == total:
        console.print(
            Panel.fit(
                f"[bold green]✅ All {total} tests passed![/bold green]\n\n"
                "Run the interview agent with:\n"
                "[cyan]python interview_agent.py[/cyan]",
                border_style="green",
            )
        )
        return 0
    else:
        failed = [k for k, v in results.items() if not v]
        console.print(
            Panel.fit(
                f"[bold red]❌ {total - passed}/{total} tests failed[/bold red]\n\n"
                f"Failed: {', '.join(failed)}",
                border_style="red",
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
