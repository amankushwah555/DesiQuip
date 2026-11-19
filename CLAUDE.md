# DesiQuip — project rules (every agent reads this)

AI pipeline that makes 1–2 funny Hindi YouTube Shorts a day plus 1 long video a week, with one
human approval per video. The full spec is `references/AI YouTube Comedy Channel — Developer Spec.pdf`.
All 4 stages are built: the agents live in `.claude/agents/`, and the orchestrator in `desiquip/services/orchestrator.py`.
Paid services switch on with keys in `.env` (see README), and every one has a free fallback.

## Architecture: ports & adapters
- `desiquip/domain/`: pure rules (script contract, timeline, captions). No I/O, no third-party imports.
- `desiquip/ports.py`: interfaces (TextToSpeech, Transcriber, MediaTool, VideoRenderer, VideoUploader, JobStore).
- `desiquip/adapters/`: the real implementations (Edge-TTS/ElevenLabs, faster-whisper, FFmpeg, Remotion, YouTube, files).
- `desiquip/services/`: one use case per file. Services depend only on ports.
- `desiquip/container.py`: the only place that picks adapters, driven by `config.yaml`. Swap a model there, not in code.
- `desiquip/cli.py`: entry point, `python -m desiquip <step> <job_id>`.
- `remotion/src/`: the Shorts template. `types.ts` must match `services/render.py::build_render_props`.

## Contracts
- Each job is `jobs/<job_id>/`. Files are the contract between steps: `script.json` → `voice.wav` +
  `timeline.json` → `captions.json` → `render.mp4` → `final.mp4` → `upload.json`.
- Any step can be re-run alone (`--from <step>`). Writes are atomic.
- `script.json` follows spec §6. Invalid → stop and flag. Never invent `source_id`, prices or links.

## Rules
- TDD: write a failing test in `tests/` first, then the code. `pytest -q` must pass before every commit.
  Services are tested against `tests/fakes`, so tests need no FFmpeg, GPU or network.
- Output format (spec §7 QA): 30–45 s, 1080×1920, 30 fps, H.264/AAC, −14 LUFS ±2,
  captions on screen ≥90% of the runtime.
- Compliance (spec §8, blocking): only sources recorded in `rights`, only licensed music, YouTube's synthetic-media flag ON,
  the small on-screen AI tag, affiliate disclosure, Made for Kids = NO, never any fake engagement.
  Owner decision: no "AI generated" text in descriptions.
- Secrets live only in `.env` and `secrets/` (both gitignored). Never print or commit them.
- Dev happens on a PC without a GPU; runs happen on a Windows laptop with an RTX 4070 (`setup.ps1`).
  Keep paths relative and the code Windows-compatible.
