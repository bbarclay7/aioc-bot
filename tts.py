"""Text-to-speech via Qwen3-TTS voice clone (mlx-audio on Apple Silicon)."""

import json
import os
import logging

import numpy as np

logger = logging.getLogger(__name__)


class TTS:
    def __init__(self, config: dict):
        self.model_id = config["tts"]["model_id"]
        self.language = config["tts"]["language"]
        self.speed = config["tts"]["speed"]
        self.tone = config["tts"]["tone"]
        self.voice_dir = config["tts"]["voice_profile_dir"]
        self._model = None
        self._ref_audio_path = None
        self._ref_text = None
        self._load_voice_profile()

    def _load_voice_profile(self):
        """Load reference audio path and transcript from voice profile."""
        meta_path = os.path.join(self.voice_dir, "meta.json")
        with open(meta_path) as f:
            meta = json.load(f)
        self._ref_audio_path = os.path.join(self.voice_dir, "audio.wav")
        self._ref_text = meta["transcript"]
        logger.info(f"Voice profile loaded: {meta['name']}")

    def _ensure_model(self):
        if self._model is not None:
            return
        from mlx_audio.tts.utils import load_model

        logger.info(f"Loading TTS model: {self.model_id} ...")
        self._model = load_model(self.model_id)
        logger.info("TTS model loaded.")

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """
        Convert text to speech using voice clone.
        Returns (audio_float32, sample_rate).
        """
        self._ensure_model()

        temperature = 0.3 + (self.tone / 100.0) * 0.7
        top_p = 0.8 + (self.tone / 100.0) * 0.2

        audio_chunks = []
        sample_rate = None

        for result in self._model.generate(
            text=text.strip(),
            ref_audio=self._ref_audio_path,
            ref_text=self._ref_text,
            lang_code=self.language,
            temperature=temperature,
            top_p=top_p,
            speed=self.speed,
            verbose=False,
        ):
            audio_chunks.append(np.array(result.audio))
            if sample_rate is None:
                sample_rate = result.sample_rate

        if not audio_chunks:
            logger.error("TTS returned no audio")
            return np.array([], dtype=np.float32), 48000

        audio = np.concatenate(audio_chunks)
        logger.info(f"TTS: {len(audio)/sample_rate:.1f}s of audio for {len(text)} chars")
        return audio, sample_rate

    def synthesize_for_radio(self, text: str, target_sr: int = 48000) -> np.ndarray:
        """
        Synthesize and convert to radio-ready int16 at target sample rate.
        """
        audio, sr = self.synthesize(text)
        if len(audio) == 0:
            return np.array([], dtype=np.int16)

        # Resample if needed
        if sr != target_sr:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)

        # Normalize to 90% peak (avoid clipping on radio)
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.9

        return (audio * 32767).astype(np.int16)
