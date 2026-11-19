"""TextToSpeech adapters: Edge-TTS (free/budget) and ElevenLabs (production)."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Callable


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
    """Plain HTTPS client: one endpoint, no SDK (the SDK's deep file paths break pip on Windows)."""

    MODEL = "eleven_multilingual_v2"
    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"

    def __init__(self, characters: dict[str, Any], post: Callable[..., Any] | None = None) -> None:
        self.characters = characters
        self._post = post

    def synthesize(self, text: str, character: str, out: Path) -> None:
        env_name = voice_for(self.characters, character, "elevenlabs_voice_env")
        voice_id = os.environ.get(env_name, "").strip()
        api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if not voice_id or not api_key:
            raise RuntimeError(f"Set ELEVENLABS_API_KEY and {env_name} in .env")
        post = self._post
        if post is None:
            import requests
            post = requests.post
        resp = post(self.URL.format(voice_id=voice_id), timeout=120,
                    headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
                    json={"text": text, "model_id": self.MODEL})
        resp.raise_for_status()
        out.write_bytes(resp.content)
