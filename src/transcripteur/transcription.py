"""Transcription audio à l'aide de faster-whisper."""

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
    """Enveloppe autour du modèle faster-whisper."""

    def __init__(self, options: WhisperOptions) -> None:
        self.options = options
        self._model: Any = None

    def _compute_type(self) -> str:
        if self.options.device == "cpu":
            return "int8"
        return "float16"

    def load(self) -> None:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.options.model_name,
                device=self.options.device,
                compute_type=self._compute_type(),
            )

    def _transcribe(self, audio: str | np.ndarray) -> TranscriptionResult:
        self.load()
        assert self._model is not None

        vad_params: Optional[Dict[str, Any]] = None
        if self.options.vad_filter:
            vad_params = {
                "threshold": self.options.vad_threshold,
                "min_silence_duration_ms": self.options.vad_min_silence_duration_ms,
                "speech_pad_ms": self.options.vad_speech_pad_ms,
            }

        segments_gen, info = self._model.transcribe(
            audio,
            language=self.options.language,
            beam_size=self.options.beam_size,
            best_of=self.options.best_of,
            patience=self.options.patience,
            temperature=self.options.temperature,
            condition_on_previous_text=self.options.condition_on_previous_text,
            compression_ratio_threshold=self.options.compression_ratio_threshold,
            log_prob_threshold=self.options.logprob_threshold,
            no_speech_threshold=self.options.no_speech_threshold,
            vad_filter=self.options.vad_filter,
            vad_parameters=vad_params,
        )

        segments = [
            Segment(start=seg.start, end=seg.end, text=seg.text)
            for seg in segments_gen
        ]
        info_dict = {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "duration_after_vad": getattr(info, "duration_after_vad", None),
            "all_language_probs": getattr(info, "all_language_probs", None),
        }
        return TranscriptionResult(
            segments=segments,
            language=info.language,
            raw={"info": info_dict, "segments": [
                {"start": s.start, "end": s.end, "text": s.text} for s in segments
            ]},
        )

    def transcribe_file(self, audio_path: Path) -> TranscriptionResult:
        return self._transcribe(str(audio_path))

    def transcribe_array(self, audio: np.ndarray) -> TranscriptionResult:
        return self._transcribe(audio)
