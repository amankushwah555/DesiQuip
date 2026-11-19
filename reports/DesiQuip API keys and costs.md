# Unlock DesiQuip's pipeline for about $60-160 a month

Every key the DesiQuip pipeline needs can be created in four weeks without paying anything upfront for the "plumbing". Google's YouTube Data and Analytics APIs, Telegram, the Meta Graph API, Amazon Associates, EarnKaro and Cuelinks all cost **₹0 / $0** to sign up for and use at this volume. The money goes to the creative services and to Claude. At 1-2 Shorts a day (30-45 s, 2-3 AI hero clips each) plus one 5-8 minute video a week, a realistic monthly bill is **about $57 on a Budget setup, about $161 on a Typical setup, and about $680 on a Premium setup**. These figures are estimates built from published per-unit USD prices, not quotes. **AI hero video from fal.ai is the single biggest cost driver**: switching from Veo 3.1 Fast without audio to Veo 3.1 standard with audio quadruples the per-second price ($0.10 to $0.40). Seven findings change how you should build. Edge-TTS is a legal risk for a monetised channel. Google OAuth tokens die every 7 days while your consent screen is in "Testing". Since 2 November 2026, API uploads are no longer forced to private. Kling's built-in audio speaks only Chinese and English. Setting `ANTHROPIC_API_KEY` silently switches Claude Code from your subscription to pay-per-token billing. Amazon's Creators API needs 10 sales in 30 days, so you start with plain tagged links. EarnKaro has no public API, and Bitly's free plan is too small. None of the vendors publish prices in rupees except Anthropic's reported (unverified) INR subscription prices, so expect your card to be charged in USD plus any bank forex fee and GST (unverified).

## Seven findings that change how you build

**Edge-TTS is free but not clearly licensed for a monetised channel.** The Week 1 voice, edge-tts, calls the Edge browser's "Read Aloud" service, not a documented public API, so Microsoft can change or block it without notice and there is no SLA ([promptquorum](https://www.promptquorum.com/power-local-llm/openai-edge-tts-review)). A Microsoft Q&A answer says the code's GPL-3.0 licence allows commercial use of the *code*, but **"commercial use without a valid Azure subscription could be a violation of our terms of service"** and recommends Azure AI Speech for commercial work ([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use)). That is a community/moderator answer rather than a formal licence, but it is the best evidence available. Treat Edge-TTS as a Week 1 test voice and move to ElevenLabs (or a paid Azure Speech subscription, whose pricing was not researched) before the channel earns money.

**Google refresh tokens expire after 7 days while the consent screen is in Testing.** Google states that "authorizations by a test user will expire seven days from the time of consent", including offline refresh tokens ([Google Cloud Help](https://support.google.com/cloud/answer/15549945)), and the OAuth overview repeats that an External + Testing project "is issued a refresh token expiring in 7 days" ([Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)). An unattended uploader will therefore fail every week unless you either re-authorise weekly or click **Publish app** to move to "In production". Publishing shows an "unverified app" warning on the consent page that you, as the only user, can click through; whether Google later forces full verification on a one-user app with sensitive scopes is **unverified**.

**API uploads are no longer locked to private.** On **2 November 2026** YouTube reversed its July 2020 policy: videos uploaded through unaudited API projects "are no longer restricted to private viewing mode" ([YouTube revision history](https://developers.google.com/youtube/v3/revision_history); [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)). You no longer need the compliance audit just to publish publicly; the audit is now only for quota above the default ([Quota and compliance audits](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits)). The flip side is that **an upload with no `privacyStatus` defaults to public**, so the pipeline must set `private` explicitly until you tap Approve in Telegram. Older guides and AI answers that say "unaudited uploads are locked private" or "an upload costs 1,600 quota units" are out of date.

**Kling's default audio cannot speak Hindi.** On fal's Kling v3 Pro image-to-video endpoint, `generate_audio` defaults to **true** and supports only Chinese and English voice; other languages are translated to English ([fal Kling v3 API](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video/api)). Always send `generate_audio=false` and lay your Hindi TTS over the clip. Audio-off is also cheaper ($0.112/s versus $0.168/s on Kling v3 Pro) ([fal Kling v3 Pro](https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video)).

**`ANTHROPIC_API_KEY` overrides your Claude subscription.** If that variable is set, Claude Code "will use this API key for authentication instead of your Claude subscription" ([Claude Help](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)). The `--bare` flag does the same, because it "doesn't use your subscription login", and Anthropic says `--bare` "will become the default for `-p` in a future release" ([Claude Code headless docs](https://code.claude.com/docs/en/headless)). If you pay for Pro or Max, keep `ANTHROPIC_API_KEY` out of your `.env` and watch Claude Code release notes.

**Amazon's Creators API is locked until you make 10 sales in 30 days.** PA-API 5.0 now returns 403 and its replacement requires "at least 10 qualifying sales within the past 30 days" ([Amazon Creators API docs](https://affiliate-program.amazon.com/creatorsapi/docs/); [PA-API deprecation](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation)). Access also lapses after 30 days without referred sales ([API rates](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)). Start with plain tagged links (`https://www.amazon.in/dp/<ASIN>?tag=<AMZ_TAG>`), which earn the same commission; the API only supplies product data.

**EarnKaro has no public API, and Bitly Free is too small.** EarnKaro's FAQ describes only manual "Make Link" creation in the app, with no API or developer access ([EarnKaro FAQ](https://earnkaro.com/faq)), so `EARNKARO_KEY` may never exist for a small channel. Bitly Free allows **5 links and 1,000 API requests a month** with an ad interstitial; Core is $10/month billed annually ($120/yr) for 100 links ([Bitly pricing](https://bitly.com/pages/pricing)).

## Week 1: get uploads working with Google Cloud and a free voice

### Google Cloud project, YouTube Data API v3, YouTube Analytics API and the Desktop OAuth client

**Produces:** `client_secret.json` (a file, not an env var; point to it with a path variable such as `YT_CLIENT_SECRET_FILE`, a suggested name) plus a saved token file holding the refresh token after first login. The Analytics API uses the same OAuth client; no separate key.

**Setup steps:**

1. Sign in with the Google account that owns the DesiQuip channel and open the Google Cloud console. Create a project (for example "DesiQuip") ([YouTube Data API getting started](https://developers.google.com/youtube/v3/getting-started)).
2. Open the API Library, search for **YouTube Data API v3**, click **Enable**; repeat for **YouTube Analytics API**. "If prompted, enable billing and accept the API's Terms of Service" ([Google OAuth for installed apps](https://developers.google.com/youtube/v3/guides/auth/installed-apps)).
3. In the Google Auth Platform pages (Branding / Audience / Clients / Data access), fill in the app name and support email, and set the audience to **External** ([Manage app audience](https://support.google.com/cloud/answer/15549945)).
4. While in **Testing**, add the channel's Google account as a **test user** (up to 100 allowed; only listed users can authorise) ([Manage app audience](https://support.google.com/cloud/answer/15549945)).
5. Add the scopes the pipeline needs: `https://www.googleapis.com/auth/youtube.upload` for uploads, and `https://www.googleapis.com/auth/yt-analytics.readonly` (plus `yt-analytics-monetary.readonly` if you want revenue figures) ([videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert); [YouTube Analytics API](https://developers.google.com/youtube/analytics/reference)). If you will later call `thumbnails.set`, also include a scope that covers it (for example `youtube` or `youtube.force-ssl`; which scopes `thumbnails.set` accepts was not checked, so verify).
6. Go to **Clients** → **Create client** → application type **Desktop app** → name it → **Create**. The client ID and secret are shown ([Google OAuth for installed apps](https://developers.google.com/youtube/v3/guides/auth/installed-apps)). Download it as `client_secret.json` (the download button is standard practice but **unverified** in the notes).
7. Run the pipeline's first login on your PC. It opens a browser and returns to a loopback address (`http://127.0.0.1:<port>`). Request **all scopes at once**, because installed apps do not support incremental authorisation ([Google OAuth for installed apps](https://developers.google.com/youtube/v3/guides/auth/installed-apps)).
8. Decide how to handle the 7-day expiry: re-run step 7 weekly, or go to Audience and click **Publish app** ([Manage app audience](https://support.google.com/cloud/answer/15549945)).
9. In YouTube, verify the channel's phone number. This unlocks "intermediate features", including **custom thumbnails** ([YouTube Help: access features](https://support.google.com/youtube/answer/9890437)).

**Price:** **$0.** No Google page found lists a charge for the YouTube Data API or Analytics API; usage is limited by a free daily quota. The default is **10,000 units/day**, with **videos.insert and search.list each in their own 100-calls-per-day bucket**; an upload costs 1 unit in its bucket and `thumbnails.set` costs 50 units ([Quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost)). Two Shorts a day plus thumbnails and some reads use roughly 150-200 units, under 2% of the free quota.

**Gotchas:** The 7-day Testing expiry is the main operational risk. A refresh token also dies if unused for 6 months, if access is revoked, or when you exceed 100 refresh tokens per account per client, in which case "a new token silently invalidates the oldest one" ([Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)), so do not re-run the login in a loop. Set `privacyStatus` on every upload (see above). Custom thumbnails for **Shorts** via `thumbnails.set` only became possible on **3 November 2026**, and the thumbnail size limit rose to 50 MB on 14 September 2026 ([revision history](https://developers.google.com/youtube/v3/revision_history)). Whether the console will insist on a billing account is "only if prompted"; most YouTube-only projects are not prompted, but that is **unverified**.

### Edge-TTS as the temporary Week 1 voice

**Produces:** no key. **Price:** $0. **Gotchas:** unofficial endpoint, no SLA, custom SSML blocked server-side, and the commercial-use risk described above ([promptquorum](https://www.promptquorum.com/power-local-llm/openai-edge-tts-review); [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use)). Plan to replace it in Week 2.

## Week 2: paid voice, AI video and talking characters

### ElevenLabs (Hindi voice)

**Produces:** `ELEVENLABS_API_KEY`, and one `VOICE_ID_*` per character voice.

**Setup steps:**

1. Create an account at elevenlabs.io and choose a plan (Starter or Creator; see price).
2. Create an API key: profile/workspace menu → API Keys → Create key (dashboard wording **unverified**). Alternatively, the documented CLI shortcut `npx -y @elevenlabs/cli@latest onboard init` signs you in, creates a key and adds the SDK ([ElevenLabs auth docs](https://elevenlabs.io/docs/api-reference/authentication)).
3. On the key, set a **credit quota** (so a runaway loop cannot drain the plan) and optionally an IP allowlist; other IPs get a 403 ([ElevenLabs auth docs](https://elevenlabs.io/docs/api-reference/authentication)).
4. Save it as `ELEVENLABS_API_KEY`; the API reads it from the `xi-api-key` header.
5. Pick or design each character voice (Voice Library, Voice Design, or Instant Voice Cloning from Starter up) and copy its Voice ID into `VOICE_ID_<NAME>`; `GET /v1/voices` also lists IDs (route **unverified** this session) ([ElevenLabs pricing](https://elevenlabs.io/pricing)).

**Price:** Starter **$6/month** is the cheapest plan with a commercial licence (30k credits); Creator **$22/month** gives 121k credits and 1 Professional voice clone; Pro is $99/month ([ElevenLabs pricing](https://elevenlabs.io/pricing)). On the API pricing page, Multilingual v2 and v3 cost **$0.08 per 1K characters** and Flash/Turbo $0.04 ([ElevenLabs API pricing](https://elevenlabs.io/pricing/api)). A 40-second Hindi Short is roughly 600-700 credits, so 45 Shorts plus four long videos need about 52-64k credits a month before retries, which **fits Creator but not Starter** (an estimate).

**Gotchas:** ElevenLabs' two pricing pages disagree on allowances (the API page shows Starter at about 75,000 and Creator at 275,000), so check the live plan page at signup ([ElevenLabs API pricing](https://elevenlabs.io/pricing/api)). Hindi support per model was not confirmed on an official page this session (**unverified**, though Multilingual v2/v3 are generally understood to support it). The Free plan is not listed as including a commercial licence.

### fal.ai (Veo 3.1, Veo 3.1 Fast, Kling)

**Produces:** `FAL_KEY`.

**Setup steps:**

1. Sign in to fal.ai and add prepaid credits; model APIs are drawn from **prepaid credits**, and you are not charged for server errors or queue time ([fal pricing](https://fal.ai/pricing)).
2. Create an API key (the dashboard location, believed to be fal.ai/dashboard/keys, is **unverified**) ([fal Kling v3 API](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video/api)).
3. Save it as `FAL_KEY`; the fal client reads it from the environment.
4. In code, call `fal-ai/veo3.1/fast` (or `fal-ai/veo3.1`) with aspect ratio **9:16**, and for Kling always pass `generate_audio=false`.
5. For Kling 9:16, generate a 9:16 still first and run image-to-video, because Kling v3 Pro I2V has no `aspect_ratio` parameter and follows the input image ([fal Kling v3 API](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video/api)).

**Price (per second of output):**

| Model on fal | Audio off | Audio on | Notes |
|---|---|---|---|
| Veo 3.1 Fast (720p/1080p) | $0.10/s | $0.15/s | 5 s 1080p with audio = $0.75 ([fal Veo 3.1 Fast](https://fal.ai/models/fal-ai/veo3.1/fast)) |
| Veo 3.1 standard (720p/1080p) | $0.20/s | $0.40/s | 16:9 and 9:16, up to 8 s per generation ([fal Veo 3.1](https://fal.ai/models/fal-ai/veo3.1)) |
| Kling v3 Pro | $0.112/s | $0.168/s | $0.196/s with voice control ([fal Kling v3 Pro](https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video)) |
| Kling v2.6 Pro | $0.07/s | not stated | from fal's summary page ([fal pricing](https://fal.ai/pricing)) |

With 2-3 clips of 4-6 seconds (10-15 s of hero video per Short), a Short costs about **$1.00-1.50 on Veo 3.1 Fast** without audio, $0.70-1.05 on Kling v2.6 Pro, and $4.00-6.00 on Veo 3.1 standard with audio.

**Gotchas:** fal's summary page and model pages disagree (Kling v3 Pro shown as $0.14/s on the summary versus $0.112-0.196 on the model page); the model page is more specific, and each model's `llms.txt` holds the current price ([fal pricing](https://fal.ai/pricing)). No free signup credit was confirmed. Whether fal bills requested or delivered seconds (Veo usually offers 4/6/8 s clips) is **unverified**. Failed generations you retry are billed. Kling audio is Chinese/English only.

### Hedra (talking character)

**Produces:** `HEDRA_API_KEY` (suggested name).

**Setup steps:**

1. Create a Hedra account and open hedra.com/develop/api-keys (linked from "Get an API key") ([Hedra Character-3](https://www.hedra.com/models/video/hedra/character-3)).
2. Create a key and save it as `HEDRA_API_KEY`.
3. Top up the **API wallet**. API calls use "a prepaid USD wallet, separate from Play subscriptions", so you do not need a Hedra subscription for the pipeline ([Hedra pricing](https://www.hedra.com/pricing)).
4. Call Character-3 with 9:16 output.

**Price:** Character-3 costs **2.5¢/s at 540p, 5¢/s at 720p and 6.25¢/s at 1080p**, clips up to 10 minutes, 9:16 supported ([Hedra Character-3](https://www.hedra.com/models/video/hedra/character-3)). A 5-second 720p talking shot costs $0.25; 10 seconds at 1080p about $0.63.

**Gotchas:** Subscription plan prices could not be read (the plans page needed a sign-in), and the minimum wallet top-up is unknown. The model page claims "full multi-language support" but does not name Hindi, so Hindi lip-sync quality is **unverified**. The free fallback, LatentSync (Apache-2.0 code), runs locally and needs about 8 GB of VRAM for v1.5 or about 18 GB for v1.6; its weights licence was not checked ([LatentSync GitHub](https://github.com/bytedance/LatentSync)).

## Week 3: approvals, trend research and Claude

### Telegram approval bot

**Produces:** `TG_BOT_TOKEN`, `TG_CHAT_ID`.

**Setup steps:**

1. In Telegram, message **@BotFather**, send `/newbot`, and follow the prompts until you receive the token ([Telegram bot tutorial](https://core.telegram.org/bots/tutorial)). Save it as `TG_BOT_TOKEN` and treat it like a password; you can revoke it in BotFather.
2. Open your new bot and press **Start** or send "hi". The bot cannot message you until you have contacted it first ([Telegram bot tutorial](https://core.telegram.org/bots/tutorial)).
3. Within 24 hours, open `https://api.telegram.org/bot<TG_BOT_TOKEN>/getUpdates` in a browser and copy `result[].message.chat.id` into `TG_CHAT_ID`. Updates are kept only 24 hours and `getUpdates` does not work while a webhook is set ([Telegram Bot API](https://core.telegram.org/bots/api)). (The URL pattern is the standard Bot API form, inferred rather than quoted.)
4. Store the chat ID as a 64-bit number; IDs can exceed 32 bits, and group IDs are negative ([Telegram Bot API](https://core.telegram.org/bots/api)).

**Price:** **$0.** Bots "message their users at no cost"; paid broadcasts apply only to mass sending ([Telegram Bots FAQ](https://core.telegram.org/bots/faq)).

**Gotchas:** Bots can send files up to **50 MB**, so a 30-45 s Short preview fits, but a 5-8 minute 1080p video probably will not; send a low-bitrate preview or a link. Keep to about 1 message per second per chat to avoid 429 errors ([Telegram Bots FAQ](https://core.telegram.org/bots/faq)).

### YT_API_KEY for trend research

**Produces:** `YT_API_KEY` (in the same Google Cloud project as Week 1).

**Setup steps:**

1. In the Google Cloud console, open **Credentials** → **Create credentials** → **API key** ([Google Cloud: manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)).
2. Add at least one API restriction (the console now requires one): **API restrictions** → **Restrict key** → select **YouTube Data API v3** → **Save**.
3. Leave "Authenticate API calls through a service account" unchecked.
4. Copy the key into `YT_API_KEY`.

**Price:** $0 (shares the free quota above). `search.list` has its own **100-calls-per-day** bucket ([Quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost)), so design trend research around that limit.

**Gotchas:** An IP-address restriction is supported but breaks on a home connection with a changing IP, and localhost is not supported ([Google Cloud: manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)); restricting the key to YouTube Data API v3 is the practical minimum.

### Anthropic Claude for headless `claude -p` runs

**Produces:** either nothing (subscription login) or `ANTHROPIC_API_KEY` (API billing). Choose one.

**Setup steps, subscription route (Pro/Max/Ultra):**

1. Buy Pro, Max or Ultra at claude.com/pricing; Claude Code is included on all three, not on Free ([claude.com/pricing](https://claude.com/pricing)).
2. Log in to Claude Code once on the PC that runs the pipeline.
3. Make sure `ANTHROPIC_API_KEY` is **not** set anywhere (system env, `.env`, scheduler).
4. Run `claude -p` **without** `--bare`, with unattended flags such as `--permission-mode` and `--permission-prompts none` for scheduled jobs ([Claude Code headless docs](https://code.claude.com/docs/en/headless)).
5. Optionally set a usage-credit spend limit at claude.ai Settings → Usage ([Claude Code costs](https://code.claude.com/docs/en/costs)).

**Setup steps, API route:**

1. Sign in to the Claude Console at platform.claude.com, add billing, and create an API key (exact click path not captured in the notes).
2. Set a **Monthly spend limit** at platform.claude.com/settings/spend-limits (click **Adjust limit** / **Set limit**); once hit, requests return a 400 error ([Anthropic rate limits](https://platform.claude.com/docs/en/api/rate-limits)).
3. Save the key as `ANTHROPIC_API_KEY`, and add `--max-budget-usd` to each `claude -p` call to cap a single run ([Claude Code headless docs](https://code.claude.com/docs/en/headless)).
4. Use `--output-format json` and log `total_cost_usd` to measure real spend after the first runs.

**Price:** Subscriptions are **Pro $20/month** ($17/month billed annually), **Max $100/month** (5x Pro) and **Ultra $200/month** (10x Pro weekly, no 5-hour limit when verified) ([claude.com/pricing](https://claude.com/pricing)). Reported INR prices (Pro about ₹2,000/month, Max about ₹11,999) come only from press reports and conflict with each other, so they are **unverified** ([Business Today](https://www.businesstoday.in/technology/news/story/anthropic-introduces-india-pricing-for-claude-ai-plans-pricing-starts-at-542742-2026-07-14)). API prices per million tokens are **Sonnet 5.5 $2 in / $10 out, Opus 5.5 $4 / $20, Haiku 5.5 $0.10 / $0.50** ([Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)). A modelled estimate for 12 runs a day (6 agents × 2) gives **$29-95/month on Sonnet 5.5**, $57-190 on Opus 5.5 and under $6 on Haiku 5.5; these are estimates, not measured.

**Gotchas:** The `ANTHROPIC_API_KEY` override and the future `--bare` default described above. Pro and Max have a 5-hour and a weekly limit shared with your normal Claude chat, and token allowances are not published ([Claude Help](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)), so 12 scheduled runs a day can hit a limit on Pro. No official statement was found on whether consumer terms permit fully automated scheduled use on a subscription (**unverified**). Whether API charges from India attract GST is also **unverified**.

## Week 4: thumbnails, cross-posting and affiliate links

### Thumbnail image API (Ideogram or Gemini)

**Produces:** `IMAGE_API_KEY` (or `GEMINI_API_KEY` for the Gemini route).

**Setup steps, Ideogram (steps from prior knowledge, unverified):**

1. Sign in at ideogram.ai, open Settings → API, add a payment method.
2. Create an API key and save it as `IMAGE_API_KEY`; it is sent in the `Api-Key` header.

**Setup steps, Gemini (steps from prior knowledge, unverified):**

1. Open aistudio.google.com → **Get API key** → create a key in a Google Cloud project.
2. **Enable billing**, because the image models have no free tier.
3. Save the key as `IMAGE_API_KEY` / `GEMINI_API_KEY`.

**Price:** Ideogram 4.0 costs **$0.03 (Turbo), $0.06 (Default), $0.10 (Quality) per image** ([Ideogram API pricing](https://ideogram.ai/pricing/?pricing_tab=api)). Gemini 3.1 Flash Image costs $0.067 per 1K image, Gemini 3 Pro Image $0.134, and Gemini 2.5 Flash Image $0.039 ([Google AI Studio pricing](https://aistudio.google.com/docs/pricing)). Three thumbnails per Short cost about $0.09-0.40.

**Gotchas:** **None of these Gemini image models has free-tier API access**, and Gemini 2.5 Flash Image shuts down on **15 March 2027** ([Google AI Studio pricing](https://aistudio.google.com/docs/pricing)). Ideogram's minimum top-up and any free API credits are unknown. For Devanagari or Hinglish text, test both, or draw the text with code over a text-free image.

### Meta Graph API (Instagram Reels and Facebook Reels)

**Produces:** `META_TOKEN` (a long-lived Page access token), `FB_PAGE_ID`, `IG_USER_ID`.

**Setup steps:**

1. In the Instagram app, switch the DesiQuip account to a **Creator or Business** professional account; both qualify ([Meta Instagram Platform overview](https://developers.facebook.com/documentation/instagram-platform/overview)).
2. Link the Instagram account to a Facebook Page you administer.
3. In the Meta App Dashboard, click **Create App** → use case **Other** → app type **Business** → enter name and contact email ([Create a Meta app for Instagram](https://developers.facebook.com/documentation/development/create-an-app/other-app-types/instagram-apis.md)).
4. Under **Instagram** → **Set up**, choose **API setup with Facebook login** (the IG account is linked to a Page) ([Create a Meta app](https://developers.facebook.com/documentation/development/create-an-app/other-app-types/instagram-apis.md)).
5. Assign your Instagram account (it must be public) for testing; manage roles under **App Roles → Roles**.
6. Get a short-lived user token with `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement` and `pages_manage_posts` (for example in Graph API Explorer) ([Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/); [Reels publishing](https://developers.facebook.com/docs/video-api/guides/reels-publishing)).
7. Exchange it server-side for a long-lived user token via `oauth/access_token?grant_type=fb_exchange_token` ([Meta long-lived tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/)).
8. Call `GET /me/accounts` with the long-lived user token. This lists your Page, giving `FB_PAGE_ID` and a **Page access token with no expiration date**; save it as `META_TOKEN` ([Meta long-lived tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/)).
9. Get `IG_USER_ID`, most likely via `GET /{FB_PAGE_ID}?fields=instagram_business_account` (endpoint from prior knowledge, **unverified**).

**Price:** **$0.** No Meta page lists a fee for these publishing endpoints; usage is governed by rate limits ([Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)). Limits are **100 API posts per 24 h on Instagram and 30 Reels per 24 h on Facebook** ([Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/); [Reels publishing](https://developers.facebook.com/docs/video-api/guides/reels-publishing)).

**Gotchas:** Your own accounts work at the default **Standard Access**; App Review and Business Verification are formally required only for Advanced Access ([Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)). However, Meta's app-creation guide also says to connect a business that has completed Business Verification "before publishing" the app, so whether a Development-mode app can post indefinitely without verification is **unresolved** ([Create a Meta app](https://developers.facebook.com/documentation/development/create-an-app/other-app-types/instagram-apis.md)). Instagram fetches the video from a public `video_url`, so you need public HTTPS hosting or the resumable upload (Facebook Login only) ([Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)). **Facebook Reels are capped at 90 seconds**, so the weekly 5-8 minute video cannot go out as an FB Reel, while Instagram Reels allow up to 15 minutes and 300 MB ([Reels publishing](https://developers.facebook.com/docs/video-api/guides/reels-publishing); [IG media reference](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media)). TikTok is excluded: it remains banned in India as far as the latest reports show ([Patrika](https://www.patrika.com/en/national-news/tiktok-ban-in-india-not-lifted-says-modi-government-19886142)).

### X API

**Produces:** `X_API_KEY`, `X_API_SECRET`, `X_TOKEN` (plus its access-token secret; `X_TOKEN_SECRET` is a suggested name).

**Setup steps:**

1. Sign up in the X Developer Console and create an app; new sign-ups get **pay-per-use** only ([X changelog](https://docs.x.com/changelog)).
2. Save a payment card and buy prepaid credits; set a spend cap per billing cycle ([X API pricing](https://docs.x.com/x-api/getting-started/pricing)).
3. In the app settings, copy the **API Key** (`X_API_KEY`) and **API Key Secret** (`X_API_SECRET`) ([X OAuth 1.0a](https://docs.x.com/fundamentals/authentication/oauth-1-0a/obtaining-user-access-tokens)).
4. Set app permissions to **Read and write** *before* generating tokens (from prior knowledge; otherwise the token is read-only).
5. Generate the **Access Token and Secret** for your own account (`X_TOKEN` and its secret). OAuth 1.0a user tokens "do not expire but can be revoked" ([X OAuth 1.0a](https://docs.x.com/fundamentals/authentication/oauth-1-0a/obtaining-user-access-tokens)). The console "generate for own account" button is standard practice but was not confirmed on a fetched page.
6. Upload video with `POST /2/media/upload/initialize` → `append` (chunks ≤5 MB) → `finalize`, poll status, then `POST /2/tweets` with the media ID ([X chunked upload](https://docs.x.com/x-api/media/quickstart/media-upload-chunked)).

**Price:** **$0.015 per post, or $0.20 if the post contains a URL**, with no monthly fee ([X API pricing](https://docs.x.com/x-api/getting-started/pricing)). At 30-60 posts a month that is **$0.45-0.90 without links** or $6-12 with a link in every post. A one-time $20 credit for your first card plus a match of your first auto-recharge up to $50 may cover months of use, but credits expire after 3 months ([X changelog](https://docs.x.com/changelog)).

**Gotchas:** Keep links out of the post text; a link reply is itself a billed post. OAuth 2.0 PKCE tokens last only 2 hours, which is why OAuth 1.0a is simpler for one account ([X OAuth 2.0](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code)). Whether media-upload calls are billed is not stated.

### Amazon Associates India and the Creators API

**Produces:** `AMZ_TAG` now; `AMZ_CREATORS_KEY` later (in practice a Credential ID + Credential Secret + Version).

**Setup steps, Associates (signup steps from third-party guides):**

1. Sign up free at affiliate-program.amazon.in, add the YouTube channel URL, and choose a store ID; it becomes your tracking ID, e.g. `name-21` ([fluxnote India join guide](https://fluxnote.io/guides/amazon-associates-india-how-to-join-2026)).
2. Save it as `AMZ_TAG` and build links as `https://www.amazon.in/dp/<ASIN>?tag=<AMZ_TAG>`, or use SiteStripe / amzn.to. Links must use Amazon's tagged formats or they earn nothing ([Amazon.in Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)).
3. Add the required disclosure: **"As an Amazon Associate I earn from qualifying purchases."** plus a link-level label such as "#ad" ([Amazon.in Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)).

**Setup steps, Creators API (after 10 sales in 30 days):**

1. In Associates Central, open **Tools → CreatorsAPI** → **Create Application** ([Creators API migration guide](https://affiliate-program.amazon.in/creatorsapi/docs/en-us/migrating-to-creatorsapi-from-paapi)).
2. Click **Create Credential** and save the Credential ID, Credential Secret and Version. The secret is shown only once.

**Price:** $0. Payout needs at least **INR 1,000 by NEFT**, paid about 60 days after month end ([Amazon.in Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)). The API starts at 1 request/second and 8,640/day ([API rates](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)).

**Gotchas:** The "3 qualified sales within 180 days or the account closes" rule is confirmed on Amazon's US and Canada pages ([Amazon US help](https://affiliate-program.amazon.com/gp/associates/help/t21)) but not on an Amazon India page (**unverified for India**); personal orders do not count. Whether Bitly-shortened Amazon links are allowed is not addressed; amzn.to is the safe choice.

### EarnKaro

**Produces:** none in practice (`EARNKARO_KEY` likely unavailable).

**Setup steps:**

1. Click **Get Started** at earnkaro.com and register with email, mobile number and password ([EarnKaro FAQ](https://earnkaro.com/faq)).
2. Create each Flipkart/Myntra/etc. link with **Make Link** in the app, and paste it into the pipeline's per-video config.
3. Add your bank account for NEFT payouts under Profile → My Payments.

**Price:** free; withdraw from **₹10** confirmed profit by free NEFT, with confirmation taking 30-90 days ([EarnKaro FAQ](https://earnkaro.com/faq)). EarnKaro keeps part of the retailer commission (share **unverified**).

**Gotchas:** No public API; a Telegram bot via an account manager is offered only to accounts "with good traffic" ([EarnKaro Magic Tool](https://earnkaro.com/profitshala/magic-tool/what-is-magic-tool)). Community endpoints have no official documentation; do not rely on them.

### Cuelinks

**Produces:** a Cuelinks API key (`CUELINKS_API_KEY`, suggested name).

**Setup steps:**

1. Join free at cuelinks.com ([Cuelinks publishers](https://www.cuelinks.com/publishers)).
2. Go to **Resource Center → API Key** (cuelinks.com/api-key) → **Create new key** → choose scopes; send it as `Authorization: Token <key>` ([Cuelinks developer docs](https://developers.cuelinks.com/)).
3. To convert links automatically (`POST /pub_api/v3/links/convert`), request the `write:links` scope, which appears to require the sales-assisted Publisher Plus tier.

**Price:** free to join; minimum payout **₹500** to Indian banks; Cuelinks keeps "a small portion" of commission ([Cuelinks publishers](https://www.cuelinks.com/publishers)). Publisher Plus pricing is **unverified**.

**Gotchas:** The free Starter tier gets only `read:campaigns`, so the key alone may not convert links ([Cuelinks developer docs](https://developers.cuelinks.com/)).

### Bitly

**Produces:** `BITLY_TOKEN`.

**Setup steps:**

1. Sign in to Bitly and choose a plan (Core or above).
2. Open **app.bitly.com/settings/api/** and generate a token; send it as `Authorization: Bearer <token>` ([Bitly authentication](https://dev.bitly.com/docs/getting-started/authentication/)).
3. Generate the token once and reuse it; repeated calls to `/oauth/access_token` get rate-limited.

**Price:** Free: 5 links/month, 1,000 API requests, ads. **Core $10/month billed annually ($120/yr), 100 links.** Growth $29/month with a free custom domain ([Bitly pricing](https://bitly.com/pages/pricing)). At 2-3 links per video and roughly 8-12 videos with links a month (an assumption), you need about 16-36 links, which fits Core.

**Gotchas:** The free alternative is self-hosted Shlink or YOURLS (MIT-licensed), but you must run a server and domain ([selfhostyourself: Shlink](https://selfhostyourself.com/services/shlink)). For Amazon links, amzn.to is free and Amazon-sanctioned.

### YouTube Shopping affiliate (India)

**Produces:** no key; enrollment happens in YouTube Studio (Earn → Shopping/Programs → Join Now; third-party description).

**Price:** free. **Gotchas:** the programme launched in India in October 2024 with Flipkart and Myntra and required YPP membership and more than 10,000 subscribers ([India TV News](https://www.indiatvnews.com/technology/news/indian-youtube-creators-can-earn-by-tagging-flipkart-and-myntra-products-in-videos-know-how-2024-10-25-958835)). A March 2026 report says the bar fell to 500 subscribers and more retailers were added ([exchange4media](https://www.exchange4media.com/digital-news/youtube-wants-a-share-of-indias-shopping-carts-will-ad-budgets-follow-159258.html)), but another source contradicts it, so the current threshold is **unverified**; check YouTube Studio. YPP's ad tier needs 1,000 subscribers plus 4,000 watch hours in 12 months or 10 million Shorts views in 90 days ([YouTube Help: YPP](https://support.google.com/youtube/answer/72851)).

Whichever affiliate you use, India's ASCI rules require a permitted label such as **#Ad** (not "#affiliate"), visible for at least a third of a video under 2 minutes, and for the whole of any product segment in longer videos ([ASCI FAQs](https://www.ascionline.in/social/faqs/)).

## All keys at a glance

| Service | Env var(s) produced | Build week | Cost |
|---|---|---|---|
| Google Cloud: YouTube Data API v3 + Analytics API + Desktop OAuth client | `client_secret.json` + saved refresh-token file | 1 | $0 (quota-limited) |
| Edge-TTS (temporary voice) | none | 1 | $0 (commercial-use risk) |
| ElevenLabs | `ELEVENLABS_API_KEY`, `VOICE_ID_*` | 2 | $6 Starter / $22 Creator per month |
| fal.ai (Veo 3.1, Kling) | `FAL_KEY` | 2 | prepaid, $0.07-0.40 per second of video |
| Hedra Character-3 | `HEDRA_API_KEY` | 2 | prepaid wallet, 2.5-6.25¢ per second |
| Telegram bot | `TG_BOT_TOKEN`, `TG_CHAT_ID` | 3 | $0 |
| YouTube trend research | `YT_API_KEY` | 3 | $0 |
| Anthropic Claude | none (subscription) or `ANTHROPIC_API_KEY` | 3 | $20 Pro / $100 Max, or ~$29-95 API on Sonnet 5.5 (estimate) |
| Ideogram or Gemini image | `IMAGE_API_KEY` / `GEMINI_API_KEY` | 4 | $0.03-0.134 per image |
| Meta Graph API | `META_TOKEN`, `FB_PAGE_ID`, `IG_USER_ID` | 4 | $0 |
| X API | `X_API_KEY`, `X_API_SECRET`, `X_TOKEN` (+ token secret) | 4 | $0.015/post, $0.20 with a URL |
| Amazon Associates India | `AMZ_TAG` | 4 | $0 |
| Amazon Creators API | `AMZ_CREATORS_KEY` (Credential ID + Secret + Version) | after 10 sales/30 days | $0 |
| EarnKaro | none in practice (`EARNKARO_KEY` likely unavailable) | 4 | $0 |
| Cuelinks | `CUELINKS_API_KEY` (suggested name) | 4 | $0; write scope may need paid tier (price unverified) |
| Bitly | `BITLY_TOKEN` | 4 | $10/month billed annually (Core) |
| YouTube Shopping India | none (Studio enrollment) | 4 / when eligible | $0 |

## Monthly cost lands between $57 and $680, driven by AI video

The table below is an estimate built from the per-unit prices above. Assumptions: **Budget** = 30 Shorts/month (1 a day); **Typical** = 45 Shorts/month (1.5 a day); **Premium** = 60 Shorts/month (2 a day). Each Short uses 2-3 hero clips totalling 12 s (Budget, Typical) or 15 s (Premium), and 3 thumbnails. Each of the 4 long videos a month uses 30-60 s of AI hero footage (my assumption; the notes do not define it) plus 3 thumbnails, and its voice is covered by the ElevenLabs plan. Retries are not included except within the ElevenLabs allowance.

| Line item | Budget (30 Shorts) | Typical (45 Shorts) | Premium (60 Shorts) |
|---|---|---|---|
| Google Cloud, Telegram, Meta, Amazon, EarnKaro, Cuelinks | $0 | $0 | $0 |
| Voice | Edge-TTS $0 (ToS risk) | ElevenLabs Creator $22 | ElevenLabs Creator $22 |
| Shorts hero video (fal) | Kling v2.6 Pro, 12 s × $0.07 × 30 = $25.20 | Veo 3.1 Fast, audio off, 12 s × $0.10 × 45 = $54.00 | Veo 3.1, audio on, 15 s × $0.40 × 60 = $360.00 |
| Talking shot | LatentSync local $0 | Hedra 720p, 5 s × 45 = $11.25 | Hedra 1080p, 10 s × 60 = $37.50 |
| Shorts thumbnails (3 each) | Ideogram 4.0 Turbo $0.09 × 30 = $2.70 | Ideogram 4.0 Default $0.18 × 45 = $8.10 | Gemini 3 Pro Image $0.40 × 60 = $24.12 |
| Long videos (4/month): hero footage + thumbnails | 30 s Kling v2.6 + Turbo thumbs = $8.76 | 60 s Veo 3.1 Fast + Default thumbs = $24.72 | 60 s Veo 3.1 with audio + Pro thumbs = $97.61 |
| Claude | Pro $20 | API Sonnet 5.5, lean runs ≈ $30 (range $29-95) | Max $100 |
| X posts | 30 × $0.015 = $0.45 | 45 × $0.015 = $0.68 | 60 × $0.20 (with link) = $12.00 |
| Link shortener | amzn.to / self-hosted $0 | Bitly Core $10 | Bitly Growth $29 |
| **Estimated total per month** | **≈ $57** | **≈ $161** | **≈ $682** |

Three things stand out. First, **AI hero video (Shorts plus long videos) is about 59% of the Budget bill, 49% of Typical and 67% of Premium**, so the cheapest lever is clip length and model choice, not dropping any free service. Paying for Veo 3.1's own audio makes little sense for a Hindi channel whose voice comes from ElevenLabs anyway; Premium with audio-off Veo 3.1 standard ($0.20/s) would cut the Shorts video line from $360 to $180. Second, the **Budget column carries hidden risk**: Edge-TTS's licensing doubt, and Claude Pro's unpublished usage limits that 12 scheduled runs a day may exceed. Moving Budget to ElevenLabs Starter ($6) is cheap insurance, although its 30k credits will not cover long-video narration, so Creator ($22) is the honest floor for a fully legitimate voice. Third, **some charges come as lump sums**: Bitly Core is billed annually ($120 upfront), and fal, Hedra and X all need prepaid credits before the first call. All figures are in USD; no vendor except Anthropic (via unverified press reports) publishes INR prices, and GST or forex fees on Indian cards are **unverified**.

## Conclusion

The four-week plan is sound, but its order hides a trap: the Week 1 uploader will appear to work and then fail silently on day 8 unless the OAuth app is published or re-authorised, and it will publish videos publicly unless `privacyStatus` is set, because the November 2026 policy change removed the private lock that older tutorials rely on. Build both safeguards on day one, before any paid key exists.

Financially, DesiQuip is a video-generation business with a free distribution layer. Every platform API (YouTube, Meta, Telegram, Amazon) costs nothing, and X costs pennies if links stay out of posts, so the decisions that matter are three: which fal model and clip length to use, whether Claude runs on a capped API key or a subscription (never both at once), and when to pay for a commercially licensed voice. A sensible path is to launch on the Typical setup at roughly $160 a month, measure real `total_cost_usd` and fal spend for two weeks, and only then decide whether Premium visuals earn their fourfold price.

## Sources

- [YouTube Data API: Getting started](https://developers.google.com/youtube/v3/getting-started)
- [Google: OAuth 2.0 for installed apps (YouTube)](https://developers.google.com/youtube/v3/guides/auth/installed-apps)
- [Google Cloud Help: Manage app audience](https://support.google.com/cloud/answer/15549945)
- [Google: Using OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [YouTube Analytics API reference](https://developers.google.com/youtube/analytics/reference)
- [YouTube Data API: videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- [YouTube Data API: Quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [YouTube Data API: Revision history](https://developers.google.com/youtube/v3/revision_history)
- [YouTube: Quota and compliance audits](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits)
- [Google Cloud: Manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)
- [YouTube Help: Access features](https://support.google.com/youtube/answer/9890437)
- [YouTube Help: YPP overview](https://support.google.com/youtube/answer/72851)
- [India TV News: YouTube Shopping affiliate in India](https://www.indiatvnews.com/technology/news/indian-youtube-creators-can-earn-by-tagging-flipkart-and-myntra-products-in-videos-know-how-2024-10-25-958835)
- [exchange4media: YouTube Shopping India expansion](https://www.exchange4media.com/digital-news/youtube-wants-a-share-of-indias-shopping-carts-will-ad-budgets-follow-159258.html)
- [Telegram: Bot tutorial](https://core.telegram.org/bots/tutorial)
- [Telegram: Bot API](https://core.telegram.org/bots/api)
- [Telegram: Bots FAQ](https://core.telegram.org/bots/faq)
- [Claude pricing](https://claude.com/pricing)
- [Claude Help: Using Claude Code with Pro or Max](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- [Claude Code: Run programmatically (headless)](https://code.claude.com/docs/en/headless)
- [Claude Code: Manage costs](https://code.claude.com/docs/en/costs)
- [Anthropic API pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Anthropic API rate and spend limits](https://platform.claude.com/docs/en/api/rate-limits)
- [Business Today: Claude India pricing](https://www.businesstoday.in/technology/news/story/anthropic-introduces-india-pricing-for-claude-ai-plans-pricing-starts-at-542742-2026-07-14)
- [ElevenLabs: API authentication](https://elevenlabs.io/docs/api-reference/authentication)
- [ElevenLabs: Pricing](https://elevenlabs.io/pricing)
- [ElevenLabs: API pricing](https://elevenlabs.io/pricing/api)
- [fal: Pricing](https://fal.ai/pricing)
- [fal: Veo 3.1](https://fal.ai/models/fal-ai/veo3.1)
- [fal: Veo 3.1 Fast](https://fal.ai/models/fal-ai/veo3.1/fast)
- [fal: Kling v3 Pro text-to-video](https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video)
- [fal: Kling v3 Pro image-to-video API](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video/api)
- [Hedra: Character-3](https://www.hedra.com/models/video/hedra/character-3)
- [Hedra: Pricing](https://www.hedra.com/pricing)
- [Ideogram: API pricing](https://ideogram.ai/pricing/?pricing_tab=api)
- [Google AI Studio: Pricing](https://aistudio.google.com/docs/pricing)
- [promptquorum: Edge-TTS review](https://www.promptquorum.com/power-local-llm/openai-edge-tts-review)
- [Microsoft Q&A: Edge-TTS commercial use](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use)
- [LatentSync on GitHub](https://github.com/bytedance/LatentSync)
- [Meta: Instagram Platform overview](https://developers.facebook.com/documentation/instagram-platform/overview)
- [Meta: Create an app for Instagram Platform](https://developers.facebook.com/documentation/development/create-an-app/other-app-types/instagram-apis.md)
- [Meta: Instagram content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- [Meta: Facebook Reels publishing](https://developers.facebook.com/docs/video-api/guides/reels-publishing)
- [Meta: Get long-lived tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/)
- [Meta: IG User media reference](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media)
- [X API: Pricing](https://docs.x.com/x-api/getting-started/pricing)
- [X: Changelog](https://docs.x.com/changelog)
- [X: Chunked media upload](https://docs.x.com/x-api/media/quickstart/media-upload-chunked)
- [X: OAuth 1.0a user access tokens](https://docs.x.com/fundamentals/authentication/oauth-1-0a/obtaining-user-access-tokens)
- [X: OAuth 2.0 authorization code](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code)
- [Patrika: TikTok ban in India not lifted (Feb 2026)](https://www.patrika.com/en/national-news/tiktok-ban-in-india-not-lifted-says-modi-government-19886142)
- [Amazon Creators API docs](https://affiliate-program.amazon.com/creatorsapi/docs/)
- [Amazon Creators API migration guide (amazon.in)](https://affiliate-program.amazon.in/creatorsapi/docs/en-us/migrating-to-creatorsapi-from-paapi)
- [Amazon Creators API: API rates](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)
- [Amazon PA-API v5 deprecation](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation)
- [Amazon.in Associates Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)
- [Amazon US Associates help: application review](https://affiliate-program.amazon.com/gp/associates/help/t21)
- [fluxnote: Amazon Associates India join guide](https://fluxnote.io/guides/amazon-associates-india-how-to-join-2026)
- [EarnKaro FAQ](https://earnkaro.com/faq)
- [EarnKaro: Magic Tool](https://earnkaro.com/profitshala/magic-tool/what-is-magic-tool)
- [Cuelinks: Publishers](https://www.cuelinks.com/publishers)
- [Cuelinks developer docs](https://developers.cuelinks.com/)
- [Bitly: Pricing](https://bitly.com/pages/pricing)
- [Bitly: API authentication](https://dev.bitly.com/docs/getting-started/authentication/)
- [selfhostyourself: Shlink](https://selfhostyourself.com/services/shlink)
- [ASCI: Influencer FAQs](https://www.ascionline.in/social/faqs/)
