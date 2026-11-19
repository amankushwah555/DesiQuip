# AI Generation APIs for an Automated Hindi Comedy YouTube Shorts Pipeline: Setup and Costs (checked 2026-11-19)

Scope: ElevenLabs (TTS, dubbing), fal.ai (Veo 3.1, Veo 3.1 Fast, Kling), Hedra (talking character), thumbnail images (Ideogram API, Gemini image models through a Google AI Studio key), and free fallbacks (Edge-TTS, LatentSync). All prices are USD unless stated. **No vendor in this list publishes INR prices on the pages fetched.** Pages were fetched on 2026-11-19 unless noted. Some pages were only partly readable (garbled tables or truncated text), and those cases are flagged.

## ElevenLabs: API key, voice ID, cheapest commercial plan, credits per model, Hindi, overage, dubbing

### Takeaway
Starter ($6/mo) is the cheapest plan with a commercial licence. At this pipeline's volume (about 60-70k characters a month), Creator ($22/mo) gives real headroom. On the API price page, Multilingual v2 and v3 cost $0.08 per 1K characters and Flash/Turbo cost $0.04 per 1K. Dubbing costs $0.33-0.50/min (v1) or $2.20/min (v2). ElevenLabs' two pricing pages give different monthly credit allowances, so check the plan page at signup.

### Cited Findings
**Setup (ELEVENLABS_API_KEY)**
- Authentication uses the HTTP header `xi-api-key`. Each key can be limited to certain endpoints (scope), given its own credit quota, and restricted to an IP allowlist (other IPs get a 403). Keep keys server-side. — [ElevenLabs API auth docs](https://elevenlabs.io/docs/api-reference/authentication)
- The docs offer a CLI shortcut, `npx -y @elevenlabs/cli@latest onboard init`, which signs in or creates an account, creates a key and adds the SDK. The auth page does not give click-by-click dashboard steps; it points to the quickstart. — [ElevenLabs API auth docs](https://elevenlabs.io/docs/api-reference/authentication)
- Suggested steps (dashboard wording **unverified** this session): sign in at elevenlabs.io → profile/workspace menu → API Keys → Create key. Set a credit quota on the key so a runaway loop cannot drain the plan. Store the key as `ELEVENLABS_API_KEY`.
- VOICE_ID_*: the fetched auth page does not cover voice IDs. The usual route (**unverified** this session) is Voices / Voice Library → pick or design a voice → copy its Voice ID, or call `GET /v1/voices`. Voice Design (create a voice from a text prompt) and Instant Voice Cloning give one fixed character voice. The pricing page lists Instant cloning from Starter up and 1 Professional clone on Creator. — [ElevenLabs pricing](https://elevenlabs.io/pricing)

**Plans (from elevenlabs.io/pricing; the table was partly garbled)**

| Plan | Price | Credits/mo | ~TTS min | Extra minute (overage) | Commercial licence | Voice cloning |
|---|---|---|---|---|---|---|
| Free | $0 | 10k | ~10 | ~$0.36 | Not listed (no) | 3 custom voice slots |
| Starter | $6/mo ($1 first month) | 30k | ~30 | ~$0.20 | Yes | Instant |
| Creator | $22/mo ($11 first month) | 121k | ~121 | ~$0.18 | Yes | Instant + 1 Professional |
| Pro | $99/mo | 600k | ~600 | ~$0.17 | Yes | Instant + 1 Professional; 44.1 kHz PCM via API |
| Scale | $299/mo | 1.8M | ~1,800 | ~$0.17 | Yes | 3 Professional |
| Business | $990/mo | 6M | ~6,000 | ~$0.17 | Yes | 10 Professional |

Source: [ElevenLabs pricing](https://elevenlabs.io/pricing)

- **Conflict:** the API pricing page shows different allowances. It lists Starter at about 75,000 and Creator at 275,000 ("stated for TTS v4"), plus Pro 1.238M, Scale 3.738M and Business 12.375M (inferred from the table layout). It also shows a "Pay as you go" option with no commitment. — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api); contradicted by [ElevenLabs pricing](https://elevenlabs.io/pricing). These may be characters versus credits, or different models (a "v4" model is mentioned). Treat the exact monthly allowance as **unverified** until checked on the live plan page at signup.
- The "$1 first month" Starter offer is said to end "September 30", with no year given, so it may be stale. — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)
- On the API price page, per 1K characters: Multilingual v2 is $0.08, v3 is $0.08 and Flash/Turbo is $0.04. The table shows the same rate on every tier, with no separate overage rate. — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)
- Credits per character: "For V2 Multilingual models, 1 text character equals 1 credit." Flash/Turbo (V2 Flash/Turbo English, V2.5 Flash/Turbo Multilingual) are discounted for API use, "costing between 0.5 and 1 credit per character." The pricing page gives no credit rate for v3. — [ElevenLabs pricing](https://elevenlabs.io/pricing)
- An "Eleven v4 model" row appears in the plan comparison table, with no details on cost or availability. — [ElevenLabs pricing](https://elevenlabs.io/pricing). **Unverified:** what v4 is, its Hindi support and its price.
- Overage: the pricing page lists only the "Extra minute" rates above. Top-up credits are mentioned without a price. — [ElevenLabs pricing](https://elevenlabs.io/pricing)
- Dubbing API: v1 is $0.33/min with a watermark and $0.50/min without; v2 is $2.20/min. — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)
- API access per plan: neither pricing page says which plans include API access. The API page's PAYG tier offers "Access to all ElevenLabs products and models". — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)

### Inferences
- About 40 s of Hindi speech is roughly 600-700 credits (the pricing page's ratio is about 1k credits per minute). At $0.08/1K that is about $0.05-0.06 per Short, or about $0.15 with 2 retries.
- Monthly use is about 45 Shorts × ~0.7k = ~32k credits, plus 4 long videos × 5-8 min (≈5-8k each) = ~20-32k. The total of about 52-64k a month (more with retries) fits Creator's 121k but exceeds Starter's 30k. If the API page's 75k Starter figure is right, Starter might just fit.
- Use eleven_multilingual_v2 or v3 for Hindi comedy delivery. Flash/Turbo v2.5 Multilingual costs half as much but usually sounds less expressive (opinion; not tested).

### Gaps
- Hindi support per model was not confirmed from an official page this session. From prior knowledge, Multilingual v2, v3 and Flash v2.5 support Hindi, but this is **unverified**.
- No INR pricing was found. Whether the Free plan includes API access was not confirmed on the fetched pages.
- The credit allowances differ between the two ElevenLabs pages (see conflict above).

## fal.ai: FAL_KEY, Veo 3.1 and Veo 3.1 Fast, Kling (latest), billing, free credits

### Takeaway
fal.ai bills per second of output from prepaid credits. Veo 3.1 Fast costs $0.10/s without audio and $0.15/s with audio at 720p/1080p. Veo 3.1 standard costs $0.20/s and $0.40/s, and both support 9:16. The latest Kling on fal is v3 / O3: Kling v3 Pro is $0.112/s without audio. Kling v2.6 Pro is listed at $0.07/s. Kling's built-in audio speaks only Chinese and English, so Hindi audio should come from the pipeline's own TTS.

### Cited Findings
**Setup (FAL_KEY)**
- Sign in to fal, create an API key, then `export FAL_KEY="YOUR_API_KEY"`, or call `fal.config({ credentials: "YOUR_FAL_KEY" })`. Keep the key server-side. The model API page does not describe the exact dashboard location. — [fal Kling v3 API page](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video/api). From prior knowledge, keys are at fal.ai/dashboard/keys (**unverified**).
- Billing: model APIs are priced per output and drawn from **prepaid credits**. There is no charge for server errors or for time spent in the queue. — [fal pricing](https://fal.ai/pricing)
- Free credits: the pricing page does not mention any. — [fal pricing](https://fal.ai/pricing). Any signup credit is **unverified**.
- Exact current prices are in each model's `https://fal.ai/models/<endpoint-id>/llms.txt`. — [fal pricing](https://fal.ai/pricing)

**Veo 3.1 (`fal-ai/veo3.1`)**
- Price per second at 720p/1080p: $0.20 without audio, $0.40 with audio. At 4K: $0.40 and $0.60. Example: a 5 s 1080p clip with audio costs $2.00. — [fal Veo 3.1](https://fal.ai/models/fal-ai/veo3.1)
- Aspect ratios 16:9 and **9:16**, 24 fps. Each generation is up to 8 s. The `extend-video` endpoint adds up to 7 s per step, for up to 20 steps (~148 s). — [fal Veo 3.1](https://fal.ai/models/fal-ai/veo3.1)

**Veo 3.1 Fast (`fal-ai/veo3.1/fast`, plus `/image-to-video` and `/first-last-frame-to-video`)**
- Price per second at 720p/1080p: $0.10 without audio, $0.15 with audio. At 4K: $0.30 and $0.35. A 5 s 1080p clip with audio costs $0.75. — [fal Veo 3.1 Fast](https://fal.ai/models/fal-ai/veo3.1/fast); [fal Veo 3.1](https://fal.ai/models/fal-ai/veo3.1)
- fal's pricing page lists all Fast endpoints (T2V, I2V, first-last-frame) at $0.15/s, which is the with-audio rate. — [fal pricing](https://fal.ai/pricing)
- 9:16 is not stated on the Fast page itself. The Veo 3.1 page lists 16:9 and 9:16 for the family. — [fal Veo 3.1](https://fal.ai/models/fal-ai/veo3.1)

**Kling**
- Kling v3 Pro text-to-video costs $0.112/s with audio off, $0.168/s with audio on and $0.196/s with audio plus voice control. — [fal Kling v3 Pro T2V](https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video)
- fal's pricing page shows a different summary figure: Kling v3 Pro and v3 Standard (I2V/T2V) at $0.14/s, Kling O3 Pro/Standard at $0.14/s, Kling v2.6 Pro at $0.07/s and Kling v2.5 Turbo Pro I2V at $0.07/s. — [fal pricing](https://fal.ai/pricing); differs from the $0.112-0.196 on the [model page](https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video). The model page is more specific.
- Kling v3 Pro I2V takes `duration` of 3-15 s (default 5) and has no `aspect_ratio` parameter, so the output follows the input image. Its `generate_audio` defaults to **true** and supports Chinese and English voice only; other languages are translated to English. — [fal Kling v3 I2V API](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video/api)

### Inferences
- For 10-15 s of hero video a Short, with audio off (Hindi TTS is laid over in the edit):
  - Veo 3.1 Fast: $1.00-1.50
  - Kling v3 Pro: $1.12-1.68
  - Kling v2.6 Pro: $0.70-1.05
  - Veo 3.1 standard: $2.00-3.00
  - Veo 3.1 standard with audio: $4.00-6.00
- Set `generate_audio=false` explicitly on Kling, because it defaults to true and only produces Chinese or English speech.
- For Kling 9:16, generate a 9:16 still first, then run I2V.
- Billing may round to fixed clip lengths (Veo usually offers 4/6/8 s). Whether fal bills requested seconds or delivered seconds is **unverified**.

### Gaps
- 9:16 support for Kling v3 T2V was not confirmed.
- fal free signup credits were not confirmed.
- Hindi lip-synced speech quality of Veo 3.1's native audio was not tested or documented.

## Hedra: API access, plans and price for talking-character video

### Takeaway
Hedra has an API. Character-3 is priced in USD at 2.5¢/s (540p), 5¢/s (720p) and 6.25¢/s (1080p), and supports 9:16. API calls draw on a prepaid USD wallet that is separate from Hedra's subscription credits. Subscription plan prices could not be read from an official page.

### Cited Findings
- Character-3 API pricing is 540p at 2.5¢/s, 720p at 5¢/s and 1080p at 6.25¢/s. Clips can run up to 10 minutes. Aspect ratios include 9:16, 1:1, 4:3, 3:4, 16:9, 9:21 and 21:9. The page claims "full multi-language support" but does not name Hindi. — [Hedra Character-3 model page](https://www.hedra.com/models/video/hedra/character-3)
- API key: the "Get an API key" link goes to hedra.com/develop/api-keys. Store the key as e.g. `HEDRA_API_KEY`. — [Hedra Character-3 model page](https://www.hedra.com/models/video/hedra/character-3)
- "Play subscription credits and the API wallet are separate." Model API calls use "a prepaid USD wallet, separate from Play subscriptions." — [Hedra pricing](https://www.hedra.com/pricing)
- Plan prices and credits per second: hedra.com/plans returned a sign-in page, and the docs credit pages returned 404. Third-party sources cite 3 credits/s at 540p and 6 credits/s at 720p (some older snapshots say 7). — [usagepricing.com](https://usagepricing.com/blueprint/hedra), [dailyaifixs.com](https://dailyaifixs.com/blog/hedra-pricing-2026-credits-burn-by-the-second). These are **unverified**.

### Inferences
- A 5 s talking shot costs $0.25 at 720p or about $0.31 at 1080p. A 10 s shot costs $0.50 or $0.63.
- For an automated pipeline, the API wallet is the right billing route; no subscription is needed according to Hedra's statement above.

### Gaps
- Subscription plan prices, credit counts and watermark/commercial terms per plan could not be fetched.
- Hindi lip-sync quality is not confirmed.
- The minimum wallet top-up is unknown.

## Thumbnail images: Ideogram API and Gemini image models (IMAGE_API_KEY)

### Takeaway
3 thumbnails cost about $0.09-0.30 per Short. Ideogram 4.0 costs $0.03/$0.06/$0.10 per image (Turbo/Default/Quality); Ideogram is strong at rendering text in images. Gemini 3.1 Flash Image costs $0.067 per 1K image, and Gemini 2.5 Flash Image costs $0.039 but is deprecated. The Gemini API has **no free tier** for these image models.

### Cited Findings
**Ideogram**
- Per image: Ideogram 4.0 costs $0.03 (Turbo), $0.06 (Default) and $0.10 (Quality). Ideogram 3.0 costs $0.03 (Flash/Turbo), $0.06 (Default) and $0.09 (Quality). 3.0 with Character Reference costs $0.10/$0.15/$0.20. "Billed per generated image." — [Ideogram API pricing](https://ideogram.ai/pricing/?pricing_tab=api)
- The minimum top-up, free API credits and key-creation steps were not stated on the pricing page. Free accounts get weekly web credits, but these may not apply to the API. — [Ideogram API pricing](https://ideogram.ai/pricing/?pricing_tab=api)
- Key creation (prior knowledge, **unverified**): ideogram.ai → Settings/API → add a payment method → create an API key, then send it in the `Api-Key` header.

**Gemini (Google AI Studio key)**
- Paid-tier prices:
  - Gemini 2.5 Flash Image ("Nano Banana"): $0.039/image (up to 1024²), $0.0195 in batch mode.
  - Gemini 3 Pro Image ("Nano Banana Pro"): $0.134 per 1K/2K image, $0.24 per 4K.
  - Gemini 3.1 Flash Image ("Nano Banana 2"): $0.045 (0.5K), $0.067 (1K), $0.101 (2K), $0.151 (4K).
  - **None of the three has Free Tier access** on the API.
  
  — [Google AI Studio pricing](https://aistudio.google.com/docs/pricing) (the old ai.google.dev/gemini-api/docs/pricing URL now 301-redirects here)
- Gemini 2.5 Flash Image is deprecated and shuts down on **March 15, 2027**; Google recommends migrating to Gemini 3.1 Flash Lite Image. — [Google AI Studio pricing](https://aistudio.google.com/docs/pricing)
- The same Nano Banana models are also on fal: Nano Banana at $0.0398, Nano Banana 2 at $0.08 and Nano Banana Pro at $0.15 per image. fal also lists FLUX.1 [schnell] at $0.003/MP. — [fal pricing](https://fal.ai/pricing)
- Key creation (prior knowledge, **unverified**): aistudio.google.com → "Get API key" → create a key in a Google Cloud project → enable billing (required, since images have no free tier). Store it as `IMAGE_API_KEY` / `GEMINI_API_KEY`.

### Inferences
- 3 thumbnails per Short cost:
  - Ideogram 4.0 Turbo: $0.09; Default: $0.18
  - Gemini 3.1 Flash Image 1K: ~$0.20
  - Gemini 2.5 Flash Image: ~$0.12 (until it shuts down)
- For Devanagari or Hinglish text on thumbnails, test both. A common approach is to render the text overlay with code (PIL) rather than in the model.

### Gaps
- Imagen 4 and Gemini 3.1 Flash Lite Image prices were not found in the readable part of the pricing page.
- Ideogram's minimum top-up and any free API credits are unknown.

## Free and budget fallbacks: Edge-TTS and LatentSync

### Takeaway
Edge-TTS costs nothing to call, but it uses an unofficial endpoint. A Microsoft Q&A answer says commercial use without an Azure subscription could violate Microsoft's terms, so it is a legal and availability risk for a monetised channel. LatentSync's code is Apache-2.0; its weights licence was not confirmed. v1.6 needs about 18 GB of VRAM and v1.5 about 8 GB.

### Cited Findings
- edge-tts calls the Edge browser's "Read Aloud" service, not a documented public API. Microsoft can change or restrict it without notice, and there is no SLA. Microsoft has also blocked custom SSML on the server side. — [promptquorum review](https://www.promptquorum.com/power-local-llm/openai-edge-tts-review); [wikidocs blog](https://wikidocs.net/blog/@jaehong/9554/)
- A Microsoft Q&A answer says the GPL-3.0 code licence allows commercial use of the code, but "commercial use without a valid Azure subscription could be a violation of our terms of service." It recommends Azure AI Speech for commercial work. This is a community or moderator answer, not a formal licence. — [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use)
- LatentSync's repository is Apache-2.0, and no separate weights licence is stated on the README. The latest release is v1.6 (2025-06-11, trained at 512×512); v1.5 came out 2025-03-14. Inference needs about 8 GB of VRAM for v1.5 and about 18 GB for v1.6. — [LatentSync GitHub](https://github.com/bytedance/LatentSync)

### Inferences
- The safer budget voice is Azure AI Speech (it has the same hi-IN-MadhurNeural voice, under a paid or free-tier Azure subscription). Its pricing was not researched here.
- LatentSync 1.5 suits an 8 GB consumer GPU; 1.6 needs a 24 GB-class card.

### Gaps
- No official Microsoft licence text specific to edge-tts or Read Aloud was found.
- Azure Speech pricing was not checked.
- The LatentSync weights licence on Hugging Face was not checked.

## Per-Short and monthly cost estimate (derived from the prices above)

### Takeaway
A typical Short costs about **$1.4-1.8**: 12 s of Veo 3.1 Fast or Kling v3 with audio off, ElevenLabs TTS, a 5 s Hedra shot and 3 Ideogram thumbnails. A budget build costs about **$0.8-1.1**, and a premium build (Veo 3.1 standard with audio) about $6-6.5. At 45 Shorts a month that is about $65-80, plus the ElevenLabs plan and the long videos.

### Cited Findings
- Unit prices are taken from the sections above: [fal Veo 3.1](https://fal.ai/models/fal-ai/veo3.1), [fal Kling v3](https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video), [fal pricing](https://fal.ai/pricing), [ElevenLabs API pricing](https://elevenlabs.io/pricing/api), [Hedra Character-3](https://www.hedra.com/models/video/hedra/character-3), [Ideogram API pricing](https://ideogram.ai/pricing/?pricing_tab=api), [Google AI Studio pricing](https://aistudio.google.com/docs/pricing)

### Inferences
| Item | Budget | Typical | Premium |
|---|---|---|---|
| Hero video (10-15 s) | Kling v2.6 Pro 12 s × $0.07 = $0.84 | Veo 3.1 Fast, no audio, 12 s × $0.10 = $1.20 (Kling v3 Pro, no audio: $1.34) | Veo 3.1, audio, 15 s × $0.40 = $6.00 |
| Hindi TTS (~700 chars) | Edge-TTS $0 (ToS risk) | ElevenLabs Multilingual v2/v3 ≈ $0.06 (≈$0.15 with retries) | same |
| Talking shot | LatentSync local $0 | Hedra 720p 5 s = $0.25 | Hedra 1080p 10 s = $0.63 |
| 3 thumbnails | Ideogram 4.0 Turbo $0.09 | Ideogram 4.0 Default $0.18 | Gemini 3 Pro Image $0.40 |
| **Per Short** | **≈ $0.93** | **≈ $1.70** | **≈ $7.2** |

- Monthly Shorts at 1-2 a day (30-60 a month), typical build: about $51-102 of pay-per-use spend (fal plus Hedra plus Ideogram). Prepay fal and Hedra separately.
- ElevenLabs subscription: Creator at $22/mo covers about 121k credits (Shorts ~32k plus long videos ~20-32k plus retries). This is a cheaper way to pay for TTS than the PAYG rate if the plan allowance holds.
- Long video (5-8 min a week): TTS is about 5-8k credits each. Hero-clip use for long videos is undefined; at the Veo Fast rate without audio, each 60 s of AI footage costs $6.
- The rough monthly total for the typical setup is about **$90-140/month (≈ ₹ unverified; no official INR prices)**.
- Caveats:
  - Retries and failed generations are billed except server errors (fal).
  - Veo clips are capped at 8 s, so 2-3 clips are needed.
  - All estimates assume audio-off video with TTS dubbed on top.

### Gaps
- The ElevenLabs credit allowance per plan is inconsistent between its own pages.
- The Hindi characters per second of speech is an estimate, about 15 chars/s.
- Real retry rates are unknown.
- None of the totals are converted to INR, since no vendor publishes INR prices.
