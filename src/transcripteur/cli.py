"""Interface en ligne de commande pour Transcripteur."""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import typer

from transcripteur.config import AppConfig
from transcripteur.export import export_json, export_srt, export_text
from transcripteur.preprocessing import FFmpegError, extract_audio
from transcripteur.transcription import WhisperTranscriber

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="Transcrire des vidéos et fichiers audio en français avec Whisper.")

__version__ = "0.1.0"


@app.command(name="version")
def version_command() -> None:
    """Afficher la version du package."""
    typer.echo(f"Transcripteur v{__version__}")


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=True)


@app.command()
def doctor(
    model: str = typer.Option("tiny", help="Nom du modèle Whisper à charger pour la vérification."),
    skip_whisper: bool = typer.Option(False, help="Ne pas charger Whisper (diagnostic léger)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Afficher des informations détaillées."),
) -> None:
    """Vérifier l’environnement d’exécution (Python, FFmpeg, Torch, Whisper)."""

    console = Console(stderr=False, highlight=False, force_terminal=verbose)
    console.print("[bold cyan]Diagnostic de l’environnement Transcripteur[/bold cyan]")

    # Python
    console.print(f"Python : {platform.python_version()} ({platform.python_implementation()})")

    # FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        console.print(f"FFmpeg : {ffmpeg_path}")
        try:
            result = _run_command(["ffmpeg", "-version"])
            console.print(result.stdout.splitlines()[0])
        except subprocess.CalledProcessError as exc:
            console.print(f"[red]FFmpeg indisponible : {exc.stderr}[/red]")
    else:
        console.print("[red]FFmpeg introuvable dans le PATH.[/red]")

    # Torch
    try:
        console.print(f"PyTorch : {torch.__version__}")
        console.print(f"CUDA disponible : {torch.cuda.is_available()}")
    except Exception as exc:  # pragma: no cover - diagnostic uniquement
        console.print(f"[red]Échec import torch : {exc}[/red]")

    if skip_whisper:
        console.print("Vérification Whisper ignorée (skip_whisper).")
        return

    # Whisper
    try:
        import whisper

        console.print(f"Whisper : {whisper.__version__ if hasattr(whisper, '__version__') else 'inconnu'}")
        console.print(f"Chargement du modèle '{model}'...")
        whisper_model = whisper.load_model(model, device="cpu")
        console.print("Modèle chargé. Test de transcription sur un signal muet...")
        dummy_audio = np.zeros(whisper.audio.SAMPLE_RATE, dtype=np.float32)
        _ = whisper_model.transcribe(dummy_audio, language="fr", fp16=False)
        console.print("[green]Whisper opérationnel (transcription de test réussie).[/green]")
    except Exception as exc:  # pragma: no cover - diagnostic uniquement
        console.print(f"[red]Échec Whisper : {exc}[/red]")


@app.command()
def transcribe(
    media: Path = typer.Argument(..., exists=True, readable=True, help="Fichier média à transcrire."),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Chemin du fichier de configuration."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Répertoire des exports."),
    model: Optional[str] = typer.Option(None, help="Nom du modèle Whisper à utiliser."),
    device: Optional[str] = typer.Option(None, help="Périphérique d’exécution (cpu, cuda, etc.)."),
    language: Optional[str] = typer.Option(None, help="Code langue ISO à forcer (ex: fr)."),
    sample_rate: int = typer.Option(16000, help="Fréquence d’échantillonnage cible (Hz)."),
    export_text_flag: Optional[bool] = typer.Option(
        None,
        "--export-text/--no-export-text",
        help="Activer ou désactiver l’export texte.",
    ),
    export_json_flag: Optional[bool] = typer.Option(
        None,
        "--export-json/--no-export-json",
        help="Activer ou désactiver l’export JSON.",
    ),
    export_srt_flag: Optional[bool] = typer.Option(
        None,
        "--export-srt/--no-export-srt",
        help="Activer ou désactiver l’export SRT.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Afficher des logs détaillés."),
) -> None:
    """Transcrire un média et exporter les résultats."""

    console = Console(stderr=False, highlight=False, force_terminal=verbose)
    config = AppConfig.load(config_path)
    if output_dir:
        config.export.output_dir = output_dir
    if model:
        config.whisper.model_name = model
    if device:
        config.whisper.device = device
    if language:
        config.whisper.language = language
    if export_text_flag is not None:
        config.export.export_text = export_text_flag
    if export_json_flag is not None:
        config.export.export_json = export_json_flag
    if export_srt_flag is not None:
        config.export.export_srt = export_srt_flag

    console.print(
        f"Configuration Whisper : modèle={config.whisper.model_name}, device={config.whisper.device}, langue={config.whisper.language}"
    )

    exporter_funcs: List[str] = []
    if config.export.export_text:
        exporter_funcs.append("texte")
    if config.export.export_json:
        exporter_funcs.append("json")
    if config.export.export_srt:
        exporter_funcs.append("srt")
    console.print(f"Exports activés : {', '.join(exporter_funcs) if exporter_funcs else 'aucun'}")

    with tempfile.TemporaryDirectory(prefix="transcripteur_") as tmpdir:
        audio_path = Path(tmpdir) / "audio.wav"
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                extract_task = progress.add_task("Extraction audio", total=None)
                extract_audio(media, audio_path, sample_rate=sample_rate)
                progress.update(extract_task, description="Extraction audio terminée", completed=1)

                transcriber = WhisperTranscriber(config.whisper)
                transcribe_task = progress.add_task("Transcription Whisper", total=None)
                result = transcriber.transcribe_file(audio_path)
                progress.update(transcribe_task, description="Transcription terminée", completed=1)
        except FFmpegError as exc:
            console.print(f"[red]Erreur FFmpeg : {exc}[/red]")
            raise typer.Exit(code=1) from exc

    output_dir = config.export.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = media.stem

    exported_paths: List[Path] = []
    if config.export.export_text:
        exported_paths.append(export_text(result, output_dir / f"{basename}.txt"))
    if config.export.export_json:
        exported_paths.append(export_json(result, output_dir / f"{basename}.json"))
    if config.export.export_srt:
        exported_paths.append(export_srt(result, output_dir / f"{basename}.srt"))

    console.print("[bold green]Transcription terminée.[/bold green]")
    for path in exported_paths:
        console.print(f"- {path}")


def main(argv: Optional[list[str]] = None) -> None:
    """Point d’entrée principal."""
    app(prog_name="transcripteur", args=argv)
