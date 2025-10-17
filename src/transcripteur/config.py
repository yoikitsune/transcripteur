"""Gestion de la configuration de Transcripteur."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import json

DEFAULT_CONFIG_NAME = "transcripteur.json"


@dataclass(slots=True)
class WhisperOptions:
    """Options de base pour le modèle Whisper."""

    model_name: str = "base"
    device: str = "cpu"
    language: str = "fr"
    beam_size: int = 5
    temperature: float = 0.0


@dataclass(slots=True)
class ExportOptions:
    """Options relatives aux formats d'export."""

    export_text: bool = True
    export_json: bool = True
    export_srt: bool = True
    output_dir: Path = Path("outputs")


@dataclass(slots=True)
class AppConfig:
    """Configuration principale de l'application."""

    whisper: WhisperOptions = field(default_factory=WhisperOptions)
    export: ExportOptions = field(default_factory=ExportOptions)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        whisper_data = data.get("whisper", {})
        export_data = data.get("export", {})
        if "output_dir" in export_data and not isinstance(export_data["output_dir"], Path):
            export_data["output_dir"] = Path(export_data["output_dir"])
        return cls(
            whisper=WhisperOptions(**whisper_data),
            export=ExportOptions(**export_data),
        )

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AppConfig":
        """Charger la configuration depuis un fichier JSON."""

        config_path = path or Path(DEFAULT_CONFIG_NAME)
        if not config_path.exists():
            return cls()

        with config_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "whisper": {
                "model_name": self.whisper.model_name,
                "device": self.whisper.device,
                "language": self.whisper.language,
                "beam_size": self.whisper.beam_size,
                "temperature": self.whisper.temperature,
            },
            "export": {
                "export_text": self.export.export_text,
                "export_json": self.export.export_json,
                "export_srt": self.export.export_srt,
                "output_dir": str(self.export.output_dir),
            },
        }

    def save(self, path: Optional[Path] = None) -> None:
        config_path = path or Path(DEFAULT_CONFIG_NAME)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as fp:
            json.dump(self.to_dict(), fp, indent=2)
