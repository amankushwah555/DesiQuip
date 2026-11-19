"""MediaTool adapter backed by FFmpeg/ffprobe. Command builders are pure and unit-tested."""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

from ..ports import VideoSpec, VoicePlacement

log = logging.getLogger(__name__)

SAMPLE_RATE = 48000
LOUDNORM_KEYS = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
ENCODERS = ("libx264", "h264_nvenc")


def choose_encoder(requested: str, nvenc_ok: bool) -> str:
    """'auto' = NVIDIA NVENC when it actually works on this machine, else CPU x264."""
    if requested == "auto":
        return "h264_nvenc" if nvenc_ok else "libx264"
    if requested not in ENCODERS:
        raise ValueError(f"video.encoder must be auto, {' or '.join(ENCODERS)}; got '{requested}'")
    return requested


def build_mix_cmd(ffmpeg: str, placements: list[VoicePlacement], total_s: float, out: Path) -> list[str]:
    """One mono track with each voice clip delayed to its scene start, padded to total_s."""
    if not placements:
        return [ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi",
                "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono", "-t", str(total_s), str(out)]
    inputs: list[str] = []
    filters: list[str] = []
    labels = ""
    for n, p in enumerate(placements):
        inputs += ["-i", str(p.clip)]
        ms = int(round(p.start_s * 1000))
        filters.append(f"[{n}:a]aresample={SAMPLE_RATE},adelay={ms}|{ms}[a{n}]")
        labels += f"[a{n}]"
    filters.append(f"{labels}amix=inputs={len(placements)}:normalize=0,apad,atrim=0:{total_s}[out]")
    return [ffmpeg, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
            "-map", "[out]", "-ac", "1", "-ar", str(SAMPLE_RATE), str(out)]


def build_loudness_probe_cmd(ffmpeg: str, src: Path, lufs: float) -> list[str]:
    """Pass 1 of two-pass loudnorm: measure only."""
    return [ffmpeg, "-hide_banner", "-nostats", "-i", str(src),
            "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]


def parse_loudnorm(stderr: str) -> dict[str, str]:
    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr)
    if not match:
        raise ValueError("loudnorm measurement JSON not found in ffmpeg output")
    data = json.loads(match.group(0))
    return {k: data[k] for k in LOUDNORM_KEYS}


def build_finalize_cmd(ffmpeg: str, src: Path, out: Path, spec: VideoSpec, measured: dict[str, str]) -> list[str]:
    """Pass 2: exact Shorts format + loudness normalised to spec (-14 LUFS)."""
    w, h = spec.width, spec.height
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={spec.fps}")
    af = (f"loudnorm=I={spec.loudness_lufs}:TP=-1.5:LRA=11:"
          f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
          f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
          f"offset={measured['target_offset']}:linear=true")
    if spec.encoder == "h264_nvenc":
        vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
    else:
        vcodec = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]
    return [ffmpeg, "-y", "-loglevel", "error", "-i", str(src), "-vf", vf, "-af", af,
            *vcodec, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-ar", str(SAMPLE_RATE), "-movflags", "+faststart", str(out)]


class FFmpegMedia:
    def __init__(self) -> None:
        self.ffmpeg = _which("ffmpeg")
        self.ffprobe = _which("ffprobe")

    def duration(self, path: Path) -> float:
        out = subprocess.run([self.ffprobe, "-v", "error", "-show_entries", "format=duration",
                              "-of", "json", str(path)], check=True, capture_output=True, text=True).stdout
        return float(json.loads(out)["format"]["duration"])

    def mix_voice(self, placements: list[VoicePlacement], total_s: float, out: Path) -> None:
        subprocess.run(build_mix_cmd(self.ffmpeg, placements, total_s, out), check=True)

    def nvenc_works(self) -> bool:
        """Listing an encoder isn't enough (needs an NVIDIA driver), so try a tiny real encode."""
        r = subprocess.run([self.ffmpeg, "-v", "error", "-f", "lavfi", "-i", "color=s=256x256:d=0.1",
                            "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True)
        return r.returncode == 0

    def finalize(self, src: Path, out: Path, spec: VideoSpec) -> None:
        encoder = choose_encoder(spec.encoder, self.nvenc_works() if spec.encoder == "auto" else False)
        log.info("Encoder: %s", encoder)
        spec = replace(spec, encoder=encoder)
        probe = subprocess.run(build_loudness_probe_cmd(self.ffmpeg, src, spec.loudness_lufs),
                               check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        subprocess.run(build_finalize_cmd(self.ffmpeg, src, out, spec, parse_loudnorm(probe.stderr)), check=True)


def _which(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"'{name}' not found on PATH. Run setup.ps1 first.")
    return path
