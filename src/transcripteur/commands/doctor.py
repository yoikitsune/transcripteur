"""Commande doctor : diagnostic de l'environnement."""

import platform
import shutil
import subprocess
from typing import Annotated

import numpy as np
import torch
import typer

from rich.console import Console

from transcripteur.cli import app


def _run_command(command: "list[str]") -> "subprocess.CompletedProcess[str]":
    return subprocess.run(command, text=True, capture_output=True, check=True)


@app.command()
def doctor(
    model: Annotated[str, typer.Option(help="Nom du modèle Whisper à charger pour la vérification.")] = "tiny",
    skip_whisper: Annotated[bool, typer.Option(help="Ne pas charger Whisper (diagnostic léger).")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Afficher des informations détaillées.")] = False,
) -> None:
    """Vérifier l'environnement d'exécution (Python, FFmpeg, Torch, Whisper)."""

    console = Console(stderr=False, highlight=False, force_terminal=verbose)
    console.print("[bold cyan]Diagnostic de l'environnement Transcripteur[/bold cyan]")

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

    # faster-whisper
    try:
        from faster_whisper import WhisperModel

        console.print("faster-whisper : import OK")
        console.print(f"Chargement du modèle '{model}'...")
        whisper_model = WhisperModel(model, device="cpu", compute_type="int8")
        console.print("Modèle chargé. Test de transcription sur un signal muet...")
        dummy_audio = np.zeros(16000, dtype=np.float32)
        segments, info = whisper_model.transcribe(dummy_audio, language="fr", beam_size=5)
        list(segments)  # force l'évaluation du générateur
        console.print("[green]faster-whisper opérationnel (transcription de test réussie).[/green]")
    except Exception as exc:  # pragma: no cover - diagnostic uniquement
        console.print(f"[red]Échec faster-whisper : {exc}[/red]")
