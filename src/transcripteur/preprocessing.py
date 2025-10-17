"""Modules de prétraitement audio/vidéo pour Transcripteur."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Optional

import typer


class FFmpegError(RuntimeError):
    """Erreur élevée lors d'un appel FFmpeg."""


def extract_audio(
    input_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
    channels: int = 1,
    overwrite: bool = True,
    ffmpeg_bin: str = "ffmpeg",
    extra_args: Optional[Iterable[str]] = None,
) -> Path:
    """Extraire l'audio d'une vidéo en WAV PCM."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg_bin,
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-f",
        "wav",
    ]
    if overwrite:
        command.insert(1, "-y")
    if extra_args:
        command.extend(extra_args)
    command.append(str(output_path))

    typer.echo(f"Extraction audio : {' '.join(command)}")
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise FFmpegError(exc.stderr.decode("utf-8", errors="ignore")) from exc

    return output_path
