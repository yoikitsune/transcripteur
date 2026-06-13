"""Transcrire tous les messages vocaux d'un dossier WhatsApp dans des fichiers .txt individuels."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from transcripteur.config import AppConfig
from transcripteur.preprocessing import denoise_and_normalize_audio, extract_audio
from transcripteur.transcription import WhisperTranscriber


def parse_timestamp(filename: str) -> str:
    """Extraire la date/heure du nom de fichier WhatsApp."""
    match = re.search(r"(\d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2})", filename)
    if match:
        return match.group(1).replace(".", ":")
    return filename


def transcribe_folder(input_dir: Path, output_dir: Path, model: str = "large-v2", device: str = "cpu") -> None:
    console = Console(stderr=False, highlight=False)
    config = AppConfig.load()
    config.whisper.model_name = model
    config.whisper.device = device

    files = sorted(input_dir.glob("*.ogg"))
    if not files:
        console.print("[red]Aucun fichier .ogg trouvé dans le dossier.[/red]")
        return

    console.print(f"[cyan]Transcription de {len(files)} message(s)…[/cyan]")
    output_dir.mkdir(parents=True, exist_ok=True)
    transcriber = WhisperTranscriber(config.whisper)

    with tempfile.TemporaryDirectory(prefix="transcripteur_batch_") as tmpdir:
        tmpdir_path = Path(tmpdir)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for idx, media_path in enumerate(files, 1):
                audio_raw = tmpdir_path / f"audio_{idx}.wav"
                audio_processed = tmpdir_path / f"audio_processed_{idx}.wav"
                timestamp = parse_timestamp(media_path.name)
                output_file = output_dir / f"{timestamp}.txt"

                task = progress.add_task(f"[{idx}/{len(files)}] {timestamp}", total=None)

                extract_audio(media_path, audio_raw, sample_rate=16000)
                if config.whisper.denoise or config.whisper.normalize:
                    denoise_and_normalize_audio(
                        audio_raw,
                        audio_processed,
                        sample_rate=16000,
                        highpass_freq=config.whisper.highpass_freq,
                        denoise=config.whisper.denoise,
                        normalize=config.whisper.normalize,
                    )
                    audio_input = audio_processed
                else:
                    audio_input = audio_raw

                result = transcriber.transcribe_file(audio_input)
                text = " ".join(seg.text.strip() for seg in result.segments).strip()

                with output_file.open("w", encoding="utf-8") as fp:
                    fp.write(f"[{timestamp}]\n\n{text}\n")

                progress.update(task, description=f"[{idx}/{len(files)}] {timestamp} ✓", completed=1)
                console.print(f"  [green]→ {output_file.name}[/green]")

    console.print(f"\n[green]Toutes les transcriptions sont dans {output_dir}[/green]")


if __name__ == "__main__":
    input_dir = Path("/home/julien/Documents/Julien-Ludo/WhatsApp Unknown 2026-06-12 at 21.33.45")
    output_dir = Path("/home/julien/Documents/Julien-Ludo/WhatsApp Unknown 2026-06-12 at 21.33.45_transcriptions")
    transcribe_folder(input_dir, output_dir, model="large-v2", device="cpu")
