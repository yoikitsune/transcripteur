"""Transcription audio à l'aide de Whisper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from transcripteur.config import WhisperOptions


@dataclass(slots=True)
class Segment:
    """Segment de transcription avec horodatages."""

    start: float
    end: float
    text: str


@dataclass(slots=True)
class TranscriptionResult:
    """Résultat complet d'une transcription."""

    segments: List[Segment]
    language: Optional[str]
    raw: Dict[str, Any]


class WhisperTranscriber:
    """Enveloppe autour du modèle Whisper."""

    def __init__(self, options: WhisperOptions) -> None:
        self.options = options
        self._model = None

    def load(self) -> None:
        if self._model is None:
            import whisper

            self._model = whisper.load_model(self.options.model_name, device=self.options.device)

    def transcribe_file(self, audio_path: Path) -> TranscriptionResult:
        self.load()
        assert self._model is not None

        result = self._model.transcribe(
            str(audio_path),
            language=self.options.language,
            temperature=self.options.temperature,
            beam_size=self.options.beam_size,
            fp16=self.options.device != "cpu",
        )
        segments = [
            Segment(start=seg["start"], end=seg["end"], text=seg["text"]) for seg in result.get("segments", [])
        ]
        return TranscriptionResult(segments=segments, language=result.get("language"), raw=result)

    def transcribe_array(self, audio: np.ndarray) -> TranscriptionResult:
        self.load()
        assert self._model is not None

        result = self._model.transcribe(
            audio,
            language=self.options.language,
            temperature=self.options.temperature,
            beam_size=self.options.beam_size,
            fp16=self.options.device != "cpu",
        )
        segments = [
            Segment(start=seg["start"], end=seg["end"], text=seg["text"]) for seg in result.get("segments", [])
        ]
        return TranscriptionResult(segments=segments, language=result.get("language"), raw=result)
