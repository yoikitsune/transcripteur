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

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Transcripteur v" in result.stdout


def test_doctor_skip_whisper() -> None:
    result = runner.invoke(app, ["doctor", "--skip-whisper"])
    assert result.exit_code == 0
    assert "Diagnostic de l’environnement Transcripteur" in result.stdout
    assert "Vérification Whisper ignorée" in result.stdout
