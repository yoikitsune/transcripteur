"""Commande transcribe : transcription d'un fichier média."""

import tempfile
from pathlib import Path
from typing import Annotated, Optional

import typer

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from transcripteur.cli import app
from transcripteur.config import AppConfig
from transcripteur.export import export_json as _export_json, export_srt as _export_srt, export_text as _export_text
from transcripteur.preprocessing import FFmpegError, denoise_and_normalize_audio, extract_audio
from transcripteur.transcription import WhisperTranscriber


@app.command()
def transcribe(
    media: Annotated[Path, typer.Argument(exists=True, readable=True, help="Fichier média à transcrire.")],
    config_path: Annotated[Optional[Path], typer.Option("--config", "-c", help="Chemin du fichier de configuration.")] = None,
    output_dir: Annotated[Optional[Path], typer.Option("--output-dir", "-o", help="Répertoire des exports.")] = None,
    model: Annotated[Optional[str], typer.Option(help="Nom du modèle Whisper à utiliser.")] = None,
    device: Annotated[Optional[str], typer.Option(help="Périphérique d'exécution (cpu, cuda, etc.).")] = None,
    language: Annotated[Optional[str], typer.Option(help="Code langue ISO à forcer (ex: fr).")] = None,
    preset: Annotated[Optional[str], typer.Option("--preset", "-p", help="Nom d'un preset de configuration à appliquer (sinon preset par défaut).")] = None,
    sample_rate: Annotated[int, typer.Option(help="Fréquence d'échantillonnage cible (Hz).")] = 16000,
    export_text: Annotated[Optional[bool], typer.Option("--export-text/--no-export-text", help="Activer ou désactiver l'export texte.")] = None,
    export_json: Annotated[Optional[bool], typer.Option("--export-json/--no-export-json", help="Activer ou désactiver l'export JSON.")] = None,
    export_srt: Annotated[Optional[bool], typer.Option("--export-srt/--no-export-srt", help="Activer ou désactiver l'export SRT.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Afficher des logs détaillés.")] = False,
) -> None:
    """Transcrire un média et exporter les résultats."""

    console = Console(stderr=False, highlight=False, force_terminal=verbose)
    config = AppConfig.load(config_path)
    preset_name = preset or config.default_preset
    if preset_name:
        if not config.apply_preset(preset_name):
            console.print(f"[red]Preset inconnu : {preset_name}[/red]")
            raise typer.Exit(code=1)
    if output_dir:
        config.export.output_dir = output_dir
    if model:
        config.whisper.model_name = model
    if device:
        config.whisper.device = device
    if language:
        config.whisper.language = language
    if export_text is not None:
        config.export.export_text = export_text
    if export_json is not None:
        config.export.export_json = export_json
    if export_srt is not None:
        config.export.export_srt = export_srt

    console.print(
        f"Configuration Whisper : modèle={config.whisper.model_name}, device={config.whisper.device}, langue={config.whisper.language}"
    )
    if preset_name:
        console.print(f"Preset actif : {preset_name}")

    exporter_funcs: list[str] = []
    if config.export.export_text:
        exporter_funcs.append("texte")
    if config.export.export_json:
        exporter_funcs.append("json")
    if config.export.export_srt:
        exporter_funcs.append("srt")
    console.print(f"Exports activés : {', '.join(exporter_funcs) if exporter_funcs else 'aucun'}")

    with tempfile.TemporaryDirectory(prefix="transcripteur_") as tmpdir:
        audio_raw = Path(tmpdir) / "audio.wav"
        audio_processed = Path(tmpdir) / "audio_processed.wav"
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                console.print("[cyan]Étape 1/3 : extraction audio[/cyan]")
                extract_task = progress.add_task("Extraction audio", total=None)
                extract_audio(media, audio_raw, sample_rate=sample_rate)
                progress.update(extract_task, description="Extraction audio terminée", completed=1)
                console.print("[green]Étape 1/3 : extraction audio terminée[/green]")

                if config.whisper.denoise or config.whisper.normalize:
                    console.print("[cyan]Étape 2/3 : prétraitement audio (débruitage + normalisation)[/cyan]")
                    preprocess_task = progress.add_task("Prétraitement audio", total=None)
                    denoise_and_normalize_audio(
                        audio_raw,
                        audio_processed,
                        sample_rate=sample_rate,
                        highpass_freq=config.whisper.highpass_freq,
                        denoise=config.whisper.denoise,
                        normalize=config.whisper.normalize,
                    )
                    progress.update(preprocess_task, description="Prétraitement terminé", completed=1)
                    console.print("[green]Étape 2/3 : prétraitement audio terminé[/green]")
                else:
                    audio_processed = audio_raw

                console.print("[cyan]Étape 3/3 : transcription Whisper[/cyan]")
                transcriber = WhisperTranscriber(config.whisper)
                transcribe_task = progress.add_task("Transcription Whisper", total=None)
                result = transcriber.transcribe_file(audio_processed)
                progress.update(transcribe_task, description="Transcription terminée", completed=1)
                console.print("[green]Étape 3/3 : transcription terminée[/green]")
        except FFmpegError as exc:
            console.print(f"[red]Erreur FFmpeg : {exc}[/red]")
            raise typer.Exit(code=1) from exc
        except Exception as exc:  # pragma: no cover - garde-fou pour erreurs inattendues
            console.print(f"[red]Erreur pendant la transcription : {exc}[/red]")
            raise typer.Exit(code=1) from exc

    output_dir = config.export.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = media.stem

    exported_paths: list[Path] = []
    if config.export.export_text:
        exported_paths.append(_export_text(result, output_dir / f"{basename}.txt"))
    if config.export.export_json:
        exported_paths.append(_export_json(result, output_dir / f"{basename}.json"))
    if config.export.export_srt:
        exported_paths.append(_export_srt(result, output_dir / f"{basename}.srt"))

    console.print("[bold green]Transcription terminée.[/bold green]")
    for path in exported_paths:
        console.print(f"- {path}")
