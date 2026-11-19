# DesiQuip

[![CI](https://github.com/amankushwah555/DesiQuip/actions/workflows/ci.yml/badge.svg)](https://github.com/amankushwah555/DesiQuip/actions/workflows/ci.yml)

An automated Hindi comedy Shorts pipeline: script → voice → word-synced captions → Remotion render → FFmpeg
finalize → YouTube upload. Claude Code agents do the thinking, and Python and Node do the heavy work.

**Status:** Week 1 of 4 (spec §10) is done. A hand-written script renders to a 9:16 Short with captions and
uploads as private.

## Setup (Windows, run once)

```powershell
git clone https://github.com/amankushwah555/DesiQuip.git
cd DesiQuip
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

`setup.ps1` does the following:
- Installs Python 3.13, Node.js 22 LTS, FFmpeg and Git if they're missing.
- Detects the NVIDIA GPU and adds the CUDA libraries for Whisper.
- Creates `.venv`, installs Remotion and creates `.env`.
- Runs the test suite.

## Make a Short

```powershell
.\.venv\Scripts\python -m desiquip new demo-001             # creates jobs\demo-001 from examples\demo-001
.\.venv\Scripts\python -m desiquip make demo-001            # -> jobs\demo-001\final.mp4
.\.venv\Scripts\python -m desiquip make demo-001 --upload   # also uploads (private)
.\.venv\Scripts\python -m desiquip make demo-001 --from render   # resume from a step
```

Single steps: `voice`, `captions`, `render`, `finalize`, `upload`.

Before the first upload, do the YouTube setup once:
1. Put your Google OAuth Desktop client at `secrets\client_secret.json`.
2. Run `.\.venv\Scripts\python -m desiquip auth`.

## Configuration
Everything you can swap is in `config.yaml`:

| Setting | Options |
| --- | --- |
| Voice engine | `edge` (free) or `elevenlabs` |
| Whisper model and device | any faster-whisper model; `auto`, `cuda` or `cpu` |
| Video encoder | `auto` (NVENC on an NVIDIA GPU, otherwise x264) |
| Render concurrency | e.g. `100%` |
| Characters | one entry per character, with its voice IDs |

API keys go in `.env`; `.env.example` lists them by build week.

## Measured on the dev PC (CPU only, no NVIDIA GPU), 42 s demo Short
| Step | Time |
| --- | --- |
| Voice (7 scenes in parallel, Edge-TTS) | ~3 s |
| Captions (Whisper small, CPU) | ~45–70 s |
| Render (Remotion) | ~216 s |
| Finalize (two-pass loudness, x264) | ~43 s |

The output passed the spec checks: 1080×1920, 30 fps, H.264/AAC, 42.2 s, −14.0 LUFS, captions on screen 97% of the time.
The GPU laptop should be much faster (Whisper large-v3 on CUDA and NVENC encoding), but we haven't measured it yet.

## Tests
```powershell
.\.venv\Scripts\python -m pytest -q
```

## Layout
| Path | What it holds |
| --- | --- |
| `desiquip/domain` | pure rules |
| `desiquip/ports.py` | interfaces |
| `desiquip/adapters` | real implementations of the interfaces |
| `desiquip/services` | use cases |
| `desiquip/container.py` | wiring, driven by `config.yaml` |
| `remotion/` | the Shorts video template |
| `examples/` | sample jobs |
| `tests/` | unit tests and test doubles |
| `references/` | spec PDF and diagrams |
| `reports/` | research reports (Markdown + Word), e.g. the API keys and costs guide |
| `research_notes/` | sourced notes behind each report |

`CLAUDE.md` holds the rules every agent follows.
