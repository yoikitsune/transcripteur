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
    # --- Fiabilité ---
    best_of: int = 5
    patience: float = 1.0
    condition_on_previous_text: bool = True
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    # --- VAD (Silero via faster-whisper) ---
    vad_filter: bool = True
    vad_threshold: float = 0.5
    vad_min_silence_duration_ms: int = 500
    vad_speech_pad_ms: int = 200
    # --- Prétraitement audio ---
    denoise: bool = True
    normalize: bool = True
    highpass_freq: int = 80


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
    presets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_preset: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        whisper_data = data.get("whisper", {})
        export_data = data.get("export", {})
        if "output_dir" in export_data and not isinstance(export_data["output_dir"], Path):
            export_data["output_dir"] = Path(export_data["output_dir"])
        presets = data.get("presets", {})
        default_preset = data.get("default_preset")
        return cls(
            whisper=WhisperOptions(**whisper_data),
            export=ExportOptions(**export_data),
            presets=presets,
            default_preset=default_preset,
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
                "best_of": self.whisper.best_of,
                "patience": self.whisper.patience,
                "condition_on_previous_text": self.whisper.condition_on_previous_text,
                "compression_ratio_threshold": self.whisper.compression_ratio_threshold,
                "logprob_threshold": self.whisper.logprob_threshold,
                "no_speech_threshold": self.whisper.no_speech_threshold,
                "vad_filter": self.whisper.vad_filter,
                "vad_threshold": self.whisper.vad_threshold,
                "vad_min_silence_duration_ms": self.whisper.vad_min_silence_duration_ms,
                "vad_speech_pad_ms": self.whisper.vad_speech_pad_ms,
                "denoise": self.whisper.denoise,
                "normalize": self.whisper.normalize,
                "highpass_freq": self.whisper.highpass_freq,
            },
            "export": {
                "export_text": self.export.export_text,
                "export_json": self.export.export_json,
                "export_srt": self.export.export_srt,
                "output_dir": str(self.export.output_dir),
            },
            "presets": self.presets,
            "default_preset": self.default_preset,
        }

    def save(self, path: Optional[Path] = None) -> None:
        config_path = path or Path(DEFAULT_CONFIG_NAME)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as fp:
            json.dump(self.to_dict(), fp, indent=2)

    def apply_preset(self, name: str) -> bool:
        preset = self.presets.get(name)
        if not preset:
            return False

        whisper_data = preset.get("whisper", {})
        for key, value in whisper_data.items():
            if hasattr(self.whisper, key):
                setattr(self.whisper, key, value)

        export_data = preset.get("export", {})
        if "output_dir" in export_data and not isinstance(export_data["output_dir"], Path):
            export_data["output_dir"] = Path(export_data["output_dir"])
        for key, value in export_data.items():
            if hasattr(self.export, key):
                setattr(self.export, key, value)

        return True
