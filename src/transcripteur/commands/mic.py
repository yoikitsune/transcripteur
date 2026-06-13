"""Commande mic : enregistrement micro puis transcription."""

import json
import sys
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import numpy as np
import torch
import typer

from rich.console import Console

from transcripteur.cli import app, format_timestamp
from transcripteur.config import AppConfig
from transcripteur.preprocessing import denoise_and_normalize_audio
from transcripteur.transcription import WhisperTranscriber


@app.command()
def mic(
    config_path: Annotated[Optional[Path], typer.Option("--config", "-c", help="Chemin du fichier de configuration.")] = None,
    model: Annotated[str, typer.Option(help="Nom du modèle Whisper à utiliser ('tiny', 'base', 'small', 'medium', 'large') ou 'auto'.")] = "auto",
    device: Annotated[str, typer.Option(help="Périphérique d'exécution (cpu, cuda, ou auto).")] = "auto",
    language: Annotated[Optional[str], typer.Option(help="Code langue ISO à forcer (ex: fr).")] = None,
    preset: Annotated[Optional[str], typer.Option("--preset", "-p", help="Nom d'un preset de configuration à appliquer (sinon preset par défaut).")] = None,
    sample_rate: Annotated[int, typer.Option(help="Fréquence d'échantillonnage cible (Hz) pour la capture micro.")] = 16000,
    max_seconds: Annotated[Optional[float], typer.Option(help="Durée maximale d'enregistrement en secondes (Ctrl+C pour arrêter plus tôt).")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Fichier texte où écrire la transcription.")] = None,
    timestamps: Annotated[bool, typer.Option(help="Afficher les horodatages au début des lignes.")] = False,
    save_wav: Annotated[Optional[Path], typer.Option("--save-wav", help="(Optionnel) Chemin personnalisé pour le WAV. Par défaut : outputs/mic_YYYYMMDD_HHMMSS.wav")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Afficher des logs détaillés.")] = False,
) -> None:
    """Enregistrer le microphone puis transcrire l'audio capturé (dictée)."""

    console = Console(stderr=False, highlight=False, force_terminal=verbose)

    try:
        import sounddevice as sd  # type: ignore[import]
    except Exception as exc:  # pragma: no cover - dépendance système externe
        console.print(
            "[red]La fonctionnalité micro (`mic`) nécessite la bibliothèque système PortAudio via le module Python 'sounddevice'.[/red]",
        )
        console.print(
            "Sur Ubuntu/Debian, installez par exemple : 'sudo apt install libportaudio2 portaudio19-dev' puis réinstallez les dépendances Python (sounddevice).",
        )
        console.print(f"Détail technique : {exc}")
        raise typer.Exit(code=1)

    config = AppConfig.load(config_path)
    preset_name = preset or config.default_preset
    if preset_name:
        if not config.apply_preset(preset_name):
            console.print(f"[red]Preset inconnu : {preset_name}[/red]")
            raise typer.Exit(code=1)

    # Device automatique ou explicite
    if device == "auto":
        config.whisper.device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        config.whisper.device = device

    # Sélection du modèle pour 'auto' en se basant sur les résultats de benchmark si possible
    if model == "auto":
        best_model: Optional[str] = None
        best_ratio: Optional[float] = None
        candidates = [
            Path("outputs") / "benchmark_youtube_30s.json",
            Path("outputs") / "benchmark.json",
        ]
        for path in candidates:
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                continue
            for result in data.get("results", []):
                if not result.get("success"):
                    continue
                ratio = result.get("sec_per_audio_second")
                name = result.get("model")
                if ratio is None or not name:
                    continue
                # Préférer 'small' si disponible, sinon prendre le meilleur ratio
                if name == "small":
                    best_model = "small"
                    best_ratio = float(ratio)
                    break
                elif best_ratio is None or ratio < best_ratio:
                    best_ratio = float(ratio)
                    best_model = str(name)
            if best_model == "small":
                break

        if best_model:
            console.print(
                f"Modèle 'auto' sélectionné : {best_model} (≈ {best_ratio:.3f} s par seconde d'audio)",
            )
            config.whisper.model_name = best_model
        else:
            console.print(
                "[yellow]Aucun résultat de benchmark exploitable, utilisation du modèle 'small' par défaut.[/yellow]",
            )
            config.whisper.model_name = "small"
    else:
        config.whisper.model_name = model

    if language:
        config.whisper.language = language

    console.print(
        f"Configuration Whisper : modèle={config.whisper.model_name}, device={config.whisper.device}, langue={config.whisper.language}",
    )
    if preset_name:
        console.print(f"Preset actif : {preset_name}")

    # --- Phase 1 : Enregistrement avec streaming WAV ---
    if max_seconds:
        console.print(
            f"[bold cyan]Enregistrement micro[/bold cyan] ({max_seconds:.0f} s max, Ctrl+C pour arrêter plus tôt)",
        )
    else:
        console.print(
            "[bold cyan]Enregistrement micro[/bold cyan] (Ctrl+C pour arrêter)",
        )

    # Déterminer le chemin WAV (automatique ou explicite)
    if save_wav is None:
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        save_wav = output_dir / f"mic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    # Préparer le fichier WAV pour streaming
    save_wav.parent.mkdir(parents=True, exist_ok=True)
    wf = wave.open(str(save_wav), "w")
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit
    wf.setframerate(sample_rate)

    chunks: list[np.ndarray] = []
    read_size = int(sample_rate * 0.5)  # lire par blocs de 0.5s
    start_time = time.monotonic()
    total_samples = 0

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
            while True:
                elapsed = time.monotonic() - start_time
                if max_seconds is not None and elapsed >= max_seconds:
                    console.print(
                        f"\r[green]Durée maximale atteinte ({max_seconds:.0f} s).[/green]",
                    )
                    break

                audio_block, _ = stream.read(read_size)
                audio_chunk = np.squeeze(audio_block).astype(np.float32)
                chunks.append(audio_chunk)

                # Écrire le chunk WAV immédiatement (streaming)
                wf.writeframes((audio_chunk * 32767).astype(np.int16).tobytes())
                total_samples += len(audio_chunk)

                # Affichage du compteur de durée
                secs = int(elapsed)
                sys.stdout.write(f"\r  Enregistrement en cours… {secs // 60:02d}:{secs % 60:02d}")
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        wf.close()

    recording_duration = time.monotonic() - start_time
    sys.stdout.write("\n")

    if not chunks:
        console.print("[red]Aucun audio capturé.[/red]")
        save_wav.unlink(missing_ok=True)
        raise typer.Exit(code=1)

    audio = np.concatenate(chunks)
    console.print(
        f"[green]Enregistrement terminé[/green] : {recording_duration:.1f} s ({len(audio)} échantillons)",
    )
    console.print(f"[green]Audio sauvegardé[/green] : {save_wav}")

    # --- Phase 2 : Prétraitement audio ---
    audio_input_path = save_wav
    if config.whisper.denoise or config.whisper.normalize:
        processed_path = save_wav.with_suffix(".processed.wav")
        console.print("[cyan]Prétraitement audio (débruitage + normalisation)…[/cyan]")
        denoise_and_normalize_audio(
            save_wav,
            processed_path,
            sample_rate=sample_rate,
            highpass_freq=config.whisper.highpass_freq,
            denoise=config.whisper.denoise,
            normalize=config.whisper.normalize,
        )
        audio_input_path = processed_path
        console.print(f"[green]Audio prétraité[/green] : {processed_path}")

    # --- Phase 3 : Transcription ---
    console.print("[cyan]Transcription en cours…[/cyan]")
    transcriber = WhisperTranscriber(config.whisper)

    t0 = time.perf_counter()
    result = transcriber.transcribe_file(audio_input_path)
    transcription_time = time.perf_counter() - t0

    text = " ".join(seg.text.strip() for seg in result.segments).strip()
    if not text:
        console.print("[yellow]Aucun texte détecté dans l'enregistrement.[/yellow]")
        raise typer.Exit(code=0)

    console.print(
        f"[green]Transcription terminée[/green] en {transcription_time:.1f} s "
        f"(ratio {transcription_time / recording_duration:.2f}×)",
    )

    # --- Phase 3 : Affichage et export ---
    console.print()
    if timestamps:
        for seg in result.segments:
            ts = format_timestamp(seg.start)
            console.print(f"[{ts}] {seg.text.strip()}")
    else:
        console.print(text)

    # Fichier de sortie par défaut si non spécifié
    if output is None:
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"mic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as fp:
            if timestamps:
                for seg in result.segments:
                    ts = format_timestamp(seg.start)
                    fp.write(f"[{ts}] {seg.text.strip()}\n")
            else:
                fp.write(text + "\n")
        console.print(f"\nTranscription écrite dans : {output}")

    console.print("[bold green]Session mic terminée.[/bold green]")
