# DesiQuip

[![CI](https://github.com/amankushwah555/DesiQuip/actions/workflows/ci.yml/badge.svg)](https://github.com/amankushwah555/DesiQuip/actions/workflows/ci.yml)

DesiQuip is an AI agent pipeline that makes funny Hindi YouTube Shorts every day. The owner's only task is
one Approve or Reject per video. Claude Code agents do the thinking, and Python and Remotion do the heavy work.

```
Trend finder -> Writer -> voice -> AI clips -> captions -> render -> finalize -> QA gate -> links -> Packager
     -> YOU approve (Telegram or CLI) -> Publisher (YouTube + Reels + X) -> Growth (09:00 next day) -> Trend finder
```

| Agent | File | What it does |
| --- | --- | --- |
| Trend finder | `.claude/agents/trend-finder.md` | Today's YouTube India trends and your topics become scored, original ideas |
| Writer | `.claude/agents/writer.md` | An idea becomes a 30–45 s Hindi script, checked against the spec rules by code |
| Video maker | code (`services/clips`, voice, captions, render) | AI hero clips (fal), voice, word-synced captions, render |
| QA reviewer | `.claude/agents/qa-reviewer.md` | Scores hook, humour and safety from the opening frames; code checks format and loudness |
| Packager | `.claude/agents/packager.md` | Title, description, tags, hashtags and 3 thumbnails |
| Publisher | code (`services/publish`) | Scheduled YouTube upload, thumbnail, playlist, Instagram/Facebook/X cross-posts |
| Growth | `.claude/agents/growth.md` | Analytics, comment replies, new learnings, best posting times |

The step order lives in `config.yaml` (`flow.produce`), so you change the flow there without touching code.

## Setup (Windows, run once)

```powershell
git clone https://github.com/amankushwah555/DesiQuip.git C:\dev\DesiQuip
cd C:\dev\DesiQuip
powershell -ExecutionPolicy Bypass -File .\setup.ps1     # installs everything, runs the tests
claude                                                   # log in to Claude Code once, then exit
```

## Daily use

```powershell
powershell -ExecutionPolicy Bypass -File .\schedule.ps1    # once: 09:00 growth, 14:00 daily run, approvals every 10 min
```

After this, the laptop works on its own:
1. At 14:00 the Trend finder picks today's ideas, and each one is written, produced and QA-checked.
2. You get each finished video (on Telegram, or as a log line) and approve or reject it.
3. Approved videos are published at the best time slot. Rejection notes become new rules in `growth/learnings.md`.
4. At 09:00 the Growth agent reviews yesterday's numbers and comments, and the system improves.

Manual commands (`.\.venv\Scripts\python -m desiquip <command>`):

| Command | What it does |
| --- | --- |
| `run-daily [--count N]` | The full daily run, now |
| `new <job> --topic "..."` then `produce <job>` | One video from your own idea, with QA retries and the approval request |
| `make <job>` | Run the steps without the orchestrator (for testing) |
| `approve <job>` / `reject <job> --note "why"` | Your decision, without Telegram |
| `status` | Every job and its state |
| `growth`, `summary`, `validate <job>`, `auth` | Growth review, daily summary, check a script, YouTube login |

## What works free, and what each key adds

Full steps and costs for each key are in `reports/DesiQuip API keys and costs.docx`. Keys go in `.env`.

| Without keys (works now) | Add this | You get |
| --- | --- | --- |
| Animated scenes + emoji or character image | `FAL_KEY`, then `clips.models: [veo3.1-fast, kling-v3-pro]` | AI hero video clips |
| Free Edge voice | `ELEVENLABS_API_KEY` + `VOICE_ID_UNCLE_JI`, `voice.engine: elevenlabs` | Production voice (safe for monetized use) |
| Ideas from `growth/topics.md` | `YT_API_KEY` (free) | Today's YouTube India trends |
| Approve with CLI commands | `TG_BOT_TOKEN` + `TG_CHAT_ID` (free) | Telegram video + Approve/Reject buttons + daily summary |
| YouTube only | `META_TOKEN` + `IG_USER_ID` / `FB_PAGE_ID`; `X_*` | Instagram/Facebook Reels, X posts |
| No product links | `AMZ_TAG` (+ `BITLY_TOKEN`) | Tagged Amazon links + deals page |
| — | `secrets/client_secret.json` + `auth` | YouTube upload, analytics and comments |

Add a picture of the character at `characters/uncle_ji.png` (a transparent PNG works best). Every scene without an AI clip
then shows him, which the QA hook check needs.

## Tests
```powershell
.\.venv\Scripts\python -m pytest -q        # 168 tests, about 5 s, no GPU or network needed
```
GitHub Actions runs them on every push, and renders a demo Short on pull requests into `main`.

## Layout
| Path | What it holds |
| --- | --- |
| `.claude/agents/` | The 5 Claude agents (prompts) |
| `desiquip/domain` | Pure rules: script, QA, packaging, schedule |
| `desiquip/ports.py` | Interfaces |
| `desiquip/adapters` | Real implementations of the interfaces |
| `desiquip/services` | Use cases, including the orchestrator |
| `desiquip/container.py` | Wiring, driven by `config.yaml` |
| `remotion/` | Shorts and thumbnail templates |
| `characters/` | Character sheets (and images) |
| `growth/` | Topics, hooks, learnings and best times. The system learns here |
| `data/` | SQLite (jobs, rights), trends, growth history (gitignored DB) |
| `reports/`, `research_notes/` | Research documents |
| `references/` | The original spec |
