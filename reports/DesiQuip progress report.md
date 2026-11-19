# DesiQuip progress report

As of 19 November 2026 · Branch `week1-pipeline` · Repo github.com/amankushwah555/DesiQuip

## Summary

**Stage 1 of the 4-stage build plan is complete and verified.** The video "factory" works end to end: a written Hindi script becomes a finished 9:16 YouTube Short with voice, word-synced captions, animation and correct loudness, and the system can upload it to YouTube as private. It was tested on this PC, in a fresh copy of the repo, and on GitHub's servers.

**The AI agents themselves are not built yet (0 of 6).** What exists are the tools the agents will use, the "hands". The "brains" (Writer, Trend finder, and the rest) start in Stage 2. Right now a person writes the script and the system makes the video.

| Measure | Status |
| --- | --- |
| Build stages (spec section 10) | **1 of 4 complete** (about 25%) |
| AI agents | **0 of 6** built |
| Pipeline tools | **5 of about 14** built (voice, captions, render, finalize, upload) |
| Automated tests | **71 passing** |
| Verified on GitHub's servers (CI) | **Passing** on Windows and Ubuntu |
| Monthly running cost so far | **$0** (free voice, no paid APIs yet) |

## What is built and working

### The video pipeline (Stage 1)

| Step | What it does | Status |
| --- | --- | --- |
| **New job** | Creates a job folder from a template | Built, tested |
| **Voice** | Speaks each Hindi line, all scenes at once in parallel | Built, verified (free Edge voice; ElevenLabs ready to switch on) |
| **Captions** | Times every word with Whisper and keeps the exact script spelling | Built, verified |
| **Render** | Animates scenes in Remotion: hook text, zoom punches, word-by-word captions, AI tag, loop ending | Built, verified |
| **Finalize** | Exports to the exact Shorts format with loudness set to the YouTube standard | Built, verified |
| **Upload** | Uploads to YouTube as private with the AI-content flag set | Built, unit-tested; **not yet tried live** (needs Google login) |

### Verified result (demo Short, "Uncle Ji vs the electricity bill")

| Spec QA rule | Required | Achieved |
| --- | --- | --- |
| Length | 30–45 s | **42.2 s** |
| Resolution | 1080×1920 | **1080×1920** |
| Frame rate | 30 fps | **30 fps** |
| Codecs | H.264 + AAC | **H.264 + AAC** |
| Loudness | −14 LUFS ± 2 | **−14.0 LUFS** |
| Captions on screen | 90% or more | **97%** |
| AI label | on-screen tag + platform flag | **Both present** |

### Speed (measured on this PC, which has no NVIDIA GPU)

| Step | Time |
| --- | --- |
| Voice | about 5 s |
| Captions | about 50 s |
| Render | about 150–215 s |
| Finalize | about 23–43 s |
| **Total per Short** | **about 4–5 minutes** |

The RTX 4070 laptop should be much faster (GPU Whisper and GPU encoding), but it hasn't been measured yet.

### Engineering foundation

- **Ports & adapters architecture:** business rules, interfaces and external services are kept apart. Any model (voice, video, Whisper) is swapped by changing one line in `config.yaml`.
- **Test-driven development:** every feature was written test-first. The 71 tests run in about 2 seconds with no GPU or internet needed.
- **One-command setup:** `setup.ps1` installs everything on a new Windows laptop and checks itself.
- **Continuous integration:** every push is tested on GitHub automatically. A full demo render runs on pull requests into `main`.
- **Security:** keys stay out of git, and the public-repo CI uses no secrets.

### Documents delivered

| Document | Where |
| --- | --- |
| API keys, secrets and costs guide (Word + Markdown) | `reports/DesiQuip API keys and costs.docx` |
| Research notes behind that guide (4 topics, with sources) | `research_notes/` |
| Project rules for every agent | `CLAUDE.md` |
| Setup and usage instructions | `README.md` |
| This progress report | `reports/DesiQuip progress report.docx` |

## Problems found and fixed during testing

Real end-to-end runs found five problems that unit tests alone would have missed. All are fixed.

| Problem | Effect | Fix |
| --- | --- | --- |
| Whisper misspelled Hindi words | Wrong captions on screen | Caption text now comes from the script, and Whisper is used only for timing |
| Captions vanished during pauses | Only 73% coverage (spec needs 90%) | Captions stay on screen until the next line: 97% |
| A video library update broke Whisper | Captions step crashed | Library version pinned |
| Windows 260-character path limit | Install failed in deep folders | Removed the heavy ElevenLabs package; setup now checks the path length |
| README copy command failed on a fresh copy | Demo couldn't start | Added a proper `new` command |

## Decisions made

| Decision | Reason |
| --- | --- |
| 6-agent design (not 14) | Simpler, as in the second reference image |
| No n8n | One codebase is easier to test, version and hand over |
| Build on this PC, run on the GPU laptop | Matches the available hardware |
| No "AI generated" text in descriptions (owner's decision) | The platform flag and the small on-screen tag are kept, as required |
| Repo is public; CI uses no secrets | Safe for public visibility |
| Flow-specific parts wait | The flow may change soon |

## What is not built yet

| Agent / part | Tools | Agent | Planned stage |
| --- | --- | --- | --- |
| Writer (script, hook, titles) | n/a (uses Claude) | Not built | Stage 2 (next) |
| Video maker (AI clips + tools) | Mostly built; AI clips (fal) missing | Not built | Stage 2 |
| Trend finder | Not built | Not built | Stage 3 |
| QA gate (auto-check before approval) | Format checks proven in CI; not wired in | Not built | Stage 3 |
| Human approval (Telegram) | Not built | n/a | Stage 3 |
| Orchestrator + daily schedule | Not built | Not built | Stage 3 |
| Packager (titles, thumbnails) | Not built | Not built | Stage 4 |
| Publisher extras (timing, playlists, cross-posting) | Upload only | Not built | Stage 4 |
| Growth (analytics, comments, learning) | Not built | Not built | Stage 4 |

## Can the full spec be achieved?

**Mostly yes.** Almost all of the workflow can be automated, with these exceptions:

- **Likely manual in YouTube Studio:** pinning comments, YouTube Shopping product tags and "Test & Compare" thumbnail tests. These still need checking against current docs.
- **Not possible yet:** automatic affiliate links. Shorts description links aren't clickable, YouTube Shopping and the Amazon API need eligibility first, and EarnKaro has no API. Until then, use a hand-picked product list.
- **Partly achievable:**
  - **Character consistency:** AI video drifts between clips.
  - **Hindi lip-sync:** quality not confirmed.
  - **Google Trends:** no official public API.
- **Not guaranteed by any code:** view duration, click-through rate and growth targets. The system will measure them and improve toward them.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Free Edge voice may break Microsoft's terms for commercial use | Legal risk once monetized | Switch to ElevenLabs (about $22/month) before earning |
| YouTube login expires every 7 days while the Google app is in "Testing" | Uploads stop weekly | Set the Google app to "Published" once |
| The flow may change | Rework | Agents are small files; flow-specific parts deliberately held back |
| Laptop must be on at run time | Missed daily runs | Run on a schedule with alerts (Stage 3) |
| Humour quality is uncertain | Weak videos | Owner feedback on the first videos; prompt iteration |

## Next steps

1. **Run the demo on the GPU laptop:** clone to `C:\dev\DesiQuip`, then run `setup.ps1`, `new demo-001` and `make demo-001`. This gives real GPU timings.
2. **Build the Writer agent** (Stage 2). It needs no paid keys. Claude will write full Hindi scripts by itself.
3. **Create the ElevenLabs and fal accounts** (steps are in the API keys guide). They're needed for the Video maker agent.
4. **Confirm the final flow**, then build Stage 3: Trend finder, QA gate, approval and scheduling.
5. **Hand off to the partner after Stage 3.** From then on his daily job is just tapping Approve or Reject in Telegram.

## What the owner needs to provide

| Item | Needed for | Cost |
| --- | --- | --- |
| Google Cloud project + OAuth client | YouTube upload (Stage 1 live test) | Free |
| ElevenLabs account | Production voice (Stage 2) | about $22/month |
| fal.ai account with credit | AI video clips (Stage 2) | about $1–2 per Short |
| Telegram bot | Approval (Stage 3) | Free |
| Claude Pro/Max login on the laptop | Running the agents | Existing plan |
| Feedback on the first videos | Comedy quality | Time |
