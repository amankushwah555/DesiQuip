"""TextToSpeech adapters: Edge-TTS (free/budget) and ElevenLabs (production)."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any


def voice_for(characters: dict[str, Any], character: str, key: str) -> str:
    try:
        return characters[character][key]
    except KeyError:
        raise KeyError(f"Character '{character}' has no '{key}' in config.yaml characters") from None


class EdgeTTS:
    def __init__(self, characters: dict[str, Any]) -> None:
        self.characters = characters

    def synthesize(self, text: str, character: str, out: Path) -> None:
        import edge_tts

        voice = voice_for(self.characters, character, "edge_voice")
        asyncio.run(edge_tts.Communicate(text, voice).save(str(out)))


class ElevenLabsTTS:
    MODEL = "eleven_multilingual_v2"

    def __init__(self, characters: dict[str, Any]) -> None:
        self.characters = characters

    def synthesize(self, text: str, character: str, out: Path) -> None:
        from elevenlabs.client import ElevenLabs

        env_name = voice_for(self.characters, character, "elevenlabs_voice_env")
        voice_id = os.environ.get(env_name, "").strip()
        api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if not voice_id or not api_key:
            raise RuntimeError(f"Set ELEVENLABS_API_KEY and {env_name} in .env")
        audio = ElevenLabs(api_key=api_key).text_to_speech.convert(
            voice_id=voice_id, text=text, model_id=self.MODEL, output_format="mp3_44100_128")
        with open(out, "wb") as f:
            for chunk in audio:
                f.write(chunk)
