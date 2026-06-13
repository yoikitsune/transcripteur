"""Commande benchmark : mesure des performances des modèles Whisper."""

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Annotated, Optional

import typer

from rich.console import Console

from transcripteur.cli import app
from transcripteur.config import AppConfig
from transcripteur.preprocessing import extract_audio
from transcripteur.transcription import WhisperTranscriber


def _run_command(command: "list[str]") -> "subprocess.CompletedProcess[str]":
    return subprocess.run(command, text=True, capture_output=True, check=True)


def _get_media_duration(path: Path) -> Optional[float]:
    """Retourner la durée en secondes d'un média audio/vidéo via ffprobe.

    Renvoie None si la durée ne peut pas être déterminée.
    """

    try:
        result = _run_command(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ]
        )
        return float(result.stdout.strip())
    except Exception:
        return None


@app.command()
def benchmark(
    media: Annotated[list[Path], typer.Argument(exists=True, readable=True, help="Fichiers média à utiliser comme échantillons de benchmark.")],
    models: Annotated[str, typer.Option("--models", "-m", help="Liste de modèles Whisper à tester, séparés par des virgules (ex: 'tiny,base').")] = "tiny,base",
    device: Annotated[str, typer.Option(help="Périphérique d'exécution (cpu, cuda, etc.).")] = "cpu",
    language: Annotated[Optional[str], typer.Option(help="Code langue ISO à forcer (ex: fr).")] = None,
    sample_rate: Annotated[int, typer.Option(help="Fréquence d'échantillonnage cible (Hz) pour l'extraction audio.")] = 16000,
    output_json: Annotated[Optional[Path], typer.Option("--output-json", help="Chemin du fichier JSON où écrire les résultats du benchmark (par défaut outputs/benchmark.json).")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Afficher des logs détaillés.")] = False,
) -> None:
    """Mesurer les performances de différents modèles Whisper sur un ou plusieurs médias."""

    console = Console(stderr=False, highlight=False, force_terminal=verbose)

    model_names = [m.strip() for m in models.split(",") if m.strip()]
    if not model_names:
        console.print("[red]Aucun modèle à benchmarker (option --models vide).[/red]")
        raise typer.Exit(code=1)

    console.print("[bold cyan]Benchmark des modèles Whisper[/bold cyan]")
    console.print(f"Modèles : {', '.join(model_names)}")
    console.print(f"Médias : {', '.join(str(m) for m in media)}")

    durations: list[Optional[float]] = []
    for path in media:
        durations.append(_get_media_duration(path))

    total_audio_seconds = sum(d for d in durations if d is not None)
    if total_audio_seconds > 0:
        console.print(f"Durée audio totale estimée : {total_audio_seconds:.1f} s")
    else:
        console.print("[yellow]Durée audio totale inconnue (ffprobe indisponible ou échec).[/yellow]")

    config = AppConfig.load()
    config.whisper.device = device
    if language:
        config.whisper.language = language

    results = []

    for model_name in model_names:
        console.print(f"[cyan]Modèle '{model_name}'[/cyan]")
        config.whisper.model_name = model_name
        transcriber = WhisperTranscriber(config.whisper)

        start = time.perf_counter()
        success = True
        error_msg: Optional[str] = None

        try:
            with tempfile.TemporaryDirectory(prefix="transcripteur_bench_") as tmpdir:
                tmpdir_path = Path(tmpdir)
                for idx, media_path in enumerate(media):
                    console.print(
                        f"  - Fichier {idx + 1}/{len(media)} : {media_path.name}",
                    )
                    audio_path = tmpdir_path / f"audio_{idx}.wav"
                    extract_audio(media_path, audio_path, sample_rate=sample_rate)
                    transcriber.transcribe_file(audio_path)
        except Exception as exc:  # pragma: no cover - comportement global benchmark uniquement
            success = False
            error_msg = str(exc)

        elapsed = time.perf_counter() - start
        sec_per_audio_second: Optional[float]
        if total_audio_seconds > 0:
            sec_per_audio_second = elapsed / total_audio_seconds
        else:
            sec_per_audio_second = None

        console.print(
            f"  -> Temps total : {elapsed:.2f} s"
            + (
                f", soit {sec_per_audio_second:.3f} s par seconde d'audio"
                if sec_per_audio_second is not None
                else ""
            )
            + (" (échec)" if not success else ""),
        )

        results.append(
            {
                "model": model_name,
                "device": device,
                "language": config.whisper.language,
                "wall_time_sec": elapsed,
                "audio_seconds": total_audio_seconds,
                "sec_per_audio_second": sec_per_audio_second,
                "success": success,
                "error": error_msg,
            }
        )

    output_path = output_json or Path("outputs") / "benchmark.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "media": [
            {
                "path": str(path),
                "duration_seconds": (dur if dur is not None else None),
            }
            for path, dur in zip(media, durations)
        ],
        "device": device,
        "language": config.whisper.language,
        "results": results,
    }
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)

    console.print(f"[green]Résultats du benchmark écrits dans {output_path}[/green]")
