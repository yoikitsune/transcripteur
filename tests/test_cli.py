"""Tests de base pour la CLI Transcripteur."""

from __future__ import annotations

import sys
from pathlib import Path

from typer.testing import CliRunner

# Ajouter src/ au PYTHONPATH pour les tests locaux
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from transcripteur.cli import app  # noqa: E402  # isort: skip
import transcripteur.commands.transcribe as transcribe_module  # noqa: E402  # isort: skip
from transcripteur.transcription import Segment, TranscriptionResult  # noqa: E402  # isort: skip

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Transcripteur v" in result.stdout


def test_doctor_skip_whisper() -> None:
    result = runner.invoke(app, ["doctor", "--skip-whisper"])
    assert result.exit_code == 0
    assert "Diagnostic de l'environnement Transcripteur" in result.stdout
    assert "Vérification Whisper ignorée" in result.stdout


def test_transcribe_integration_stub(tmp_path: Path, monkeypatch) -> None:
    media = ROOT / "sample_silence.wav"
    output_dir = tmp_path / "out"

    def fake_extract_audio(input_path: Path, output_path: Path, sample_rate: int = 16000, channels: int = 1, overwrite: bool = True, ffmpeg_bin: str = "ffmpeg", extra_args=None) -> Path:  # type: ignore[override]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"")
        return output_path

    def fake_transcribe_file(self, audio_path: Path):  # type: ignore[override]
        return TranscriptionResult(
            segments=[Segment(start=0.0, end=1.0, text="test")],
            language="fr",
            raw={},
        )

    monkeypatch.setattr(transcribe_module, "extract_audio", fake_extract_audio)
    monkeypatch.setattr(transcribe_module.WhisperTranscriber, "transcribe_file", fake_transcribe_file)
    monkeypatch.setattr(transcribe_module, "_export_text", lambda result, path: (path.write_text("test"), path)[1])
    monkeypatch.setattr(transcribe_module, "_export_json", lambda result, path: (path.write_text("{}"), path)[1])
    monkeypatch.setattr(transcribe_module, "_export_srt", lambda result, path: (path.write_text(""), path)[1])

    result = runner.invoke(
        app,
        [
            "transcribe",
            str(media),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Transcription terminée." in result.stdout
    txt_path = output_dir / f"{media.stem}.txt"
    json_path = output_dir / f"{media.stem}.json"
    srt_path = output_dir / f"{media.stem}.srt"
    assert txt_path.exists()
    assert json_path.exists()
    assert srt_path.exists()
