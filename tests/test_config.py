"""Tests pour la configuration de Transcripteur."""

from __future__ import annotations

import json
from pathlib import Path

from transcripteur.config import AppConfig, ExportOptions, WhisperOptions


def test_app_config_defaults(tmp_path: Path) -> None:
    config = AppConfig()
    config_path = tmp_path / "config.json"
    config.save(config_path)

    loaded = AppConfig.load(config_path)
    assert loaded.whisper.model_name == "base"
    assert loaded.whisper.device == "cpu"
    assert loaded.export.export_json is True
    assert loaded.export.output_dir == Path("outputs")


def test_app_config_from_dict_override(tmp_path: Path) -> None:
    payload = {
        "whisper": {"model_name": "small", "device": "cpu", "beam_size": 3},
        "export": {"export_text": False, "output_dir": "custom"},
    }
    config_path = tmp_path / "cfg.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    config = AppConfig.load(config_path)
    assert config.whisper.model_name == "small"
    assert config.whisper.beam_size == 3
    assert config.export.export_text is False
    assert config.export.output_dir == Path("custom")
