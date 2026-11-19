# Google/YouTube APIs, Telegram bot and Anthropic Claude: setup steps and costs for an automated Hindi Shorts pipeline (India), as of 2026-11-19

Scope: 1-2 Hindi comedy Shorts (30-45 s) per day + 1 long video (5-8 min) per week; Claude Code headless (`claude -p`) 1-2x/day running 6 agents; one Telegram approval message per video. All pages below were fetched on 2026-11-19 unless stated. Most Google pages show no "last updated" date; the YouTube revision history (dated entries up to 2026-11-16) is used to date changes.

## Q1. Google Cloud: project, APIs, OAuth consent screen, Desktop OAuth client, API key; is anything paid?

### Takeaway
All of it can be set up without paying. No Google page found says the YouTube Data API or the Analytics API charges money; usage is limited by a free daily quota, not billed. A Google OAuth doc does say "if prompted, enable billing", so a billing prompt is possible, but YouTube's own setup steps don't list billing. The biggest catch is that while the consent screen stays in **Testing**, refresh tokens die after **7 days**. An unattended pipeline therefore has to re-authorize every week, or publish the app to "In production".

### Cited Findings
**Overall steps (YouTube's "Before you start")**
- You need a Google Account, then "Create a project in the Google Cloud console and obtain authorization credentials". Check that YouTube Data API is enabled, and if it isn't, enable it from the API Library. Set up OAuth 2.0 for methods that need user permission. The page says nothing about cost or billing and treats quota as a usage limit, not a charge. — [YouTube Data API Getting Started](https://developers.google.com/youtube/v3/getting-started)

**Enable APIs (YouTube Data API v3 + YouTube Analytics API)**
- Open the API Library (console.developers.google.com/apis/library), select or create a project, search for the API, select it and click **Enable**. "If prompted, enable billing and accept the API's Terms of Service." — [Google OAuth for installed apps](https://developers.google.com/youtube/v3/guides/auth/installed-apps)
- Analytics API scopes: `https://www.googleapis.com/auth/yt-analytics.readonly` ("View YouTube Analytics reports for your YouTube content") and `https://www.googleapis.com/auth/yt-analytics-monetary.readonly` (adds estimated revenue and ad metrics). The reference page gives no quota figures for the Analytics API. — [YouTube Analytics API reference](https://developers.google.com/youtube/analytics/reference)
- Upload scopes accepted by videos.insert (any one of): `youtube.upload`, `youtube`, `youtubepartner`, `youtube.force-ssl`. — [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)

**OAuth consent screen (now in the "Google Auth Platform" pages: Branding / Audience / Clients / Data access)**
- User type **External** means "available to any user with a Google Account." — [Google Cloud Help: Manage app audience](https://support.google.com/cloud/answer/15549945)
- In **Testing**, a project is "limited to up to 100 test users listed in the OAuth consent screen", and only listed test users can authorize. Add your own channel's Google account as a test user. — [Manage app audience](https://support.google.com/cloud/answer/15549945)
- Moving to production: "A project's publishing status is considered In production after selecting the Publish app button." Projects that meet the verification criteria "should complete the verification process". Until they do, requesting sensitive or restricted scopes shows an "Unverified apps" warning. — [Manage app audience](https://support.google.com/cloud/answer/15549945)
- **Token expiry in Testing:** "Authorizations by a test user will expire seven days from the time of consent", and refresh tokens issued with offline access expire too. The only exception is requests limited to name, email, profile or openid scopes. — [Manage app audience](https://support.google.com/cloud/answer/15549945). The same rule appears in the OAuth 2.0 overview: an External + Testing project "is issued a refresh token expiring in 7 days." — [Using OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- Other ways a refresh token can be invalidated: the user revokes access; the token goes unused for 6 months; the 100-refresh-tokens-per-Google-Account-per-client limit is reached ("a new token silently invalidates the oldest one"). — [Using OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

**Create the OAuth client "Desktop app" (client_secret.json)**
- Go to the Clients page (console.developers.google.com/auth/clients), click **Create client**, choose application type **Desktop app**, enter a Name and click **Create**. The client ID and secret are then shown. Desktop apps are public clients, so use PKCE. — [OAuth for installed apps](https://developers.google.com/youtube/v3/guides/auth/installed-apps)
- Redirect method: loopback `http://127.0.0.1:<port>` is recommended for Windows/macOS/Linux desktop apps and is not deprecated for Desktop clients. Incremental authorization isn't supported for installed apps, so request every scope up front (upload + analytics). — [OAuth for installed apps](https://developers.google.com/youtube/v3/guides/auth/installed-apps)
- The fetched page doesn't spell out the JSON download button. Downloading the client as `client_secret.json` from the Clients list is standard practice but unverified in these notes.

**Create the API key (YT_API_KEY) with restrictions**
- Open **Credentials**, click **Create credentials > API key**. In the console "must add at least one API restriction to create an API key". Leave "Authenticate API calls through a service account" unchecked; that option is for authorization keys and is blocked by a default organization policy. Click **Create** and copy the key. — [Google Cloud: Manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)
- API restrictions: open the key, go to **API restrictions > Restrict key**, select YouTube Data API v3 (the API must already be enabled), then **Save**. — [Manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)
- Application restrictions (only one type per key): Websites (HTTP referrers), **IP addresses** (IPv4/IPv6/CIDR; internal IPs and localhost aren't supported), Android apps, or iOS apps. "Unrestricted API keys are insecure." There is a limit of 300 keys per project. — [Manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)
- The API key page has no pricing; it says keys tie requests to a project "for billing and quota purposes." — [Manage API keys](https://docs.cloud.google.com/docs/authentication/api-keys)

### Inferences
- Cost: INR 0 / USD 0. No fetched Google page lists a charge for the YouTube Data API or the Analytics API; they are quota-limited. Whether the console will insist on a billing account is "only if prompted" per Google. Most YouTube-only projects are not prompted, but that is unverified.
- For a home PC with a dynamic IP, an IP restriction on YT_API_KEY may break. Restricting the key to "YouTube Data API v3" only is the practical minimum.
- The 7-day Testing expiry is the main operational risk. Option A: re-run the OAuth flow weekly. Option B: click **Publish app**. Upload and analytics scopes are sensitive, so the consent page will show an "unverified app" warning that the owner can click through. Whether a single-user app must complete full verification after publishing is not confirmed (see Gaps).

### Gaps
- No page found states explicitly "YouTube Data API is free / no billing account required." The only evidence is the absence of pricing plus the quota model.
- Whether a published-but-unverified personal app (sensitive scopes, 1 user) is capped or forced into verification was not confirmed. The verification-exemption rules for personal-use apps were not fetched.
- The exact field names in the newer Google Auth Platform UI (Branding, Audience, Data access) were not walked through screen by screen.

## Q2. YouTube Data API quota (2026)

### Takeaway
The quota model changed in 2025-2026. Default quota is 10,000 units/day for general methods. **videos.insert and search.list now each have their own bucket of 100 calls/day**, and an upload now costs 1 unit in the uploads bucket. Before Dec 2025 an upload cost about 1,600 units of the shared 10,000. thumbnails.set costs 50 units. This pipeline (~2 uploads/day + thumbnails + some reads) uses well under 5% of the free quota.

### Cited Findings
- Quota costs: videos.insert = 1 unit, "separate 100-per-day bucket"; search.list = 1, separate 100/day bucket; videos.list = 1; thumbnails.set = 50; videos.update = 50; channels.list = 1; playlistItems.list = 1; commentThreads.list = 1; captions.insert = 400. Default 10,000 units/day "combined for all endpoints other than search.list and videos.insert". Quotas reset at midnight Pacific Time. — [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- videos.insert page: "A call to this method has a quota cost of 1 unit in the Video Uploads quota bucket", limit 100 calls/day; max file 256 GB; accepted MIME `video/*`, `application/octet-stream`; the error `uploadLimitExceeded` means the user hit a per-user upload count. — [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- History: Dec 4, 2025, upload cost cut "from approximately 1600 units to approximately 100 units". Jun 1, 2026, "API calls to the videos.insert and search.list methods will be charged to their own respective quota buckets." Jun 3, 2026, new `videos.batchGetStats` (1 unit, own bucket, 10,000/day). Nov 3, 2026, `thumbnails.set` supports custom thumbnails for **Shorts** after processing. Sep 14, 2026, max thumbnail upload size raised from 2 MB to 50 MB. — [YouTube Data API Revision History](https://developers.google.com/youtube/v3/revision_history)
- Conflict: the Dec 2025 revision note says "~100 units" per upload, but the current quota page and videos.insert page say 1 unit in a separate bucket. The current pages are taken as authoritative. The revision history excerpt did not state the 100/day figure itself; that comes from the quota calculator and getting-started pages. — [Revision History](https://developers.google.com/youtube/v3/revision_history) vs [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- More quota requires the quota extension form. — [Getting Started](https://developers.google.com/youtube/v3/getting-started)

### Inferences
- Estimated daily use: 2 videos.insert (2 of 100 in the uploads bucket) + 2 thumbnails.set (100 units) + about 20-50 list calls (20-50 units) + weekly long upload. That is roughly 150-200 of 10,000 units/day, so a quota increase is not needed.
- The Analytics API quota is separate and undocumented on the reference page. It is not an issue at this volume (inference).

### Gaps
- No per-second/per-minute rate limits are published on the quota page.
- The Analytics API default quota was not found.

## Q3. YouTube API Services compliance audit and the "private lock"

### Takeaway
As of **2 Nov 2026** the private lock is gone. Videos uploaded through unaudited (unverified) API projects are no longer forced to private, which reverses the July 28, 2020 policy. An audit is now only needed to get quota above the default. It is requested through a free Google form, and Google gives no turnaround time.

### Cited Findings
- Nov 2, 2026 revision: videos from unverified API projects "are no longer restricted to private viewing mode"; this "reverses the policy announced on July 28, 2020". If `privacyStatus` is unset, uploads default to public, though some account settings can still default them to private. — [Revision History](https://developers.google.com/youtube/v3/revision_history)
- videos.insert page now reads: "Videos uploaded from unverified API projects are not restricted to private viewing mode." — [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- Audit: "If you would like to request additional quota beyond the default allocation, you must first complete an audit." Apply via the "YouTube API Services - Audit and Quota Extension Form" at https://support.google.com/youtube/contact/yt_api_form. Timeline is only "as soon as possible", and no fee is mentioned. The audit checks compliance with the YouTube API Services Terms of Service. — [Quota and Compliance Audits](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits)

### Inferences
- An individual creator at 1-2 uploads/day doesn't need to apply for the audit. Set `privacyStatus` explicitly in code (e.g. `private` until Telegram approval, or `public`/scheduled `publishAt`).
- Older guides, blog posts and AI answers still say "unaudited uploads are locked private" and "an upload costs 1,600 units". Both are outdated as of Nov 2026.

### Gaps
- No official audit turnaround time. Third-party reports of weeks-long reviews were not checked.

## Q4. YouTube channel prerequisites: verification, YPP, Shopping affiliate (India)

### Takeaway
Phone verification unlocks **intermediate features**: videos over 15 min, custom thumbnails, live streaming. Custom thumbnails via `thumbnails.set` need this. YPP has two tiers: the expanded/fan-funding tier at 500 subs, and the ad-revenue tier at 1,000 subs plus 4,000 watch hours or 10M Shorts views in 90 days. The India Shopping affiliate threshold is disputed in news reports (10,000 vs 500 subs), so check it in YouTube Studio.

### Cited Findings
- Standard (no verification): upload videos/Shorts, playlists, Posts. **Intermediate (verify phone number)**: videos over 15 minutes, live streaming on computer, **custom thumbnails**, podcasts. **Advanced** (channel history, or ID/video verification): includes "Applying for monetization", clickable links in long-form descriptions, related video on Shorts, pinned comments, chapters, A/B testing, multi-language features. — [YouTube Help: Access features](https://support.google.com/youtube/answer/9890437)
- YPP ad tier: "1,000 subscribers with 4,000 qualified watch hours in the last 12 months" or "1,000 subscribers with 10 million qualified Shorts views in the last 90 days"; Shorts-feed watch hours don't count toward the 4,000. The channel must live in a country where YPP is available. — [YouTube Help: YPP overview](https://support.google.com/youtube/answer/72851)
- Expanded YPP (fan funding + Shopping): 500 subscribers, 3 valid public uploads in the last 90 days, and either 3,000 watch hours (12 months) or 3M Shorts views (90 days). — [YouTube Help: Expanded YPP overview](https://support.google.com/youtube/answer/13429240) (via search summary; the page was not fetched in full)
- Reported future change: from 1 Feb 2027, new ad-tier applicants would need 1,000 subs plus 8,000 watch hours/365 days or 20M Shorts views/90 days. **Unverified.** This comes only from third-party search results such as [Tella blog](https://www.tella.com/blog/how-to-join-youtube-partner-program) and [vidIQ](https://vidiq.com/tr/blog/post/youtube-relaxes-monetization-rules); no official Google page confirmed it.
- India eligibility for expanded YPP: claimed only by third-party blogs, so **unverified** against Google's country list.
- Shopping affiliate in India: launched Oct 2024 with Flipkart and Myntra, originally requiring YPP membership and more than 10,000 subscribers, no music channels and no made-for-kids channels. — [India TV News](https://www.indiatvnews.com/technology/news/indian-youtube-creators-can-earn-by-tagging-flipkart-and-myntra-products-in-videos-know-how-2024-10-25-958835); [Cuelinks](https://www.cuelinks.com/blog/youtube-shopping-affiliate-program-arrives-in-india/)
- Reported lowering to 500 subscribers (March 2026) and an expanded retailer list (Amazon, AJIO, Meesho, Snapdeal, Tata CLiQ added to Flipkart, Myntra, Nykaa, Purplle, Shopsy, Tira). — [exchange4media](https://www.exchange4media.com/digital-news/youtube-wants-a-share-of-indias-shopping-carts-will-ad-budgets-follow-159258.html). This contradicts [Indian Television](https://indiantelevision.com/iworld/youtube-shopping-expands-india-merchant-network-as-creator-payouts-soar/), which lists AJIO/Meesho/Snapdeal/Tata CLiQ as upcoming. **Unverified.**
- Enrollment: YouTube Studio > Earn > Programs (or Shopping) > Join Now; up to 30 products can be tagged per video, livestream or Short. — via search summary of the sources above (third-party)

### Inferences
- Before running the pipeline, verify the channel's phone number (free) so `thumbnails.set` works. Shorts thumbnails via the API are new as of Nov 3, 2026.
- Hindi comedy Shorts most plausibly reach YPP via the 10M Shorts views/90 days route.

### Gaps
- The official YouTube Help article for the Shopping affiliate program (answer 13785969 returned 404) could not be fetched, so the current India subscriber threshold and partner store list are unverified.
- No official confirmation of the Feb 2027 YPP threshold change.

## Q5. Telegram bot: TG_BOT_TOKEN, TG_CHAT_ID, cost, rate limits

### Takeaway
It's free. Create the bot with @BotFather `/newbot` to get the token. Send your bot any message, then call `getUpdates` and read `message.chat.id`. Keep sends to about 1 message/second per chat; uploads up to 50 MB, so a 30-45 s Short preview fits.

### Cited Findings
- Create the bot: send `/newbot` to @BotFather "and following the steps until you're given a new token". Token example `4839574812:AAFD39kkdpWt3ywyRZergyOLMaJhac60qc`. Treat it "like a password", store it in env vars or settings rather than code, and revoke it anytime via @BotFather. — [Telegram Bot tutorial](https://core.telegram.org/bots/tutorial)
- "The user **must** have contacted your bot first" before the bot can message them. — [Telegram Bot tutorial](https://core.telegram.org/bots/tutorial)
- `getUpdates`: updates "will not be kept longer than 24 hours", and the method "will not work if an outgoing webhook is set up". A chat id can exceed 32 bits ("at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe"). Latest Bot API version: 10.4 (9 Nov 2026). — [Telegram Bot API](https://core.telegram.org/bots/api)
- Cost: bots can "message their users at no cost". Paid broadcasts (0.1 Stars per message above the free allowance) only apply to mass bulk sending. — [Bots FAQ](https://core.telegram.org/bots/faq)
- Rate limits: avoid more than 1 message/second in a single chat (sustained excess leads to 429 errors); 20 messages/minute in groups; about 30 messages/second bulk. — [Bots FAQ](https://core.telegram.org/bots/faq)
- File limits: bots can send files up to 50 MB and download (getFile) files up to 20 MB; a local Bot API server allows uploads up to 2000 MB. — [Bots FAQ](https://core.telegram.org/bots/faq); [Bot API](https://core.telegram.org/bots/api)

### Inferences
- Reliable TG_CHAT_ID procedure: (1) open the bot in Telegram and press Start or send "hi". (2) Within 24 h, open `https://api.telegram.org/bot<TG_BOT_TOKEN>/getUpdates` in a browser. (3) Copy `result[].message.chat.id`. It is a positive number for a private chat and negative (often `-100…`) for groups/channels. (4) If you get an empty result, call `deleteWebhook` first or resend a message. The URL pattern is the standard Bot API form (inferred from the Bot API docs, not quoted).
- Approval flow: a sendMessage/sendVideo with an inline keyboard (Approve/Reject) plus handling of `callback_query` updates. The Bot API lists callback queries as an update type; parameter details were not fetched.
- A 5-8 min long video at 1080p will likely exceed 50 MB. Send a low-bitrate preview or a link instead.

### Gaps
- Exact text of BotFather's name/username rules (username must end in "bot") was not quoted from an official page.

## Q6. Anthropic: Pro/Max/Ultra subscriptions vs API key; prices, limits, estimated monthly cost, spend limits

### Takeaway
**Subscriptions:** Pro $20/mo ($17/mo annual), Max $100/mo (5x Pro), and a $200/mo tier now called **Ultra** (10x Pro weekly, no 5-hour limit when verified). All include Claude Code. Headless `claude -p` without `--bare` uses the subscription login, but `--bare` and any set `ANTHROPIC_API_KEY` switch to per-token API billing.

**API (USD per million tokens):** Opus 5.5 $4 in / $20 out; Sonnet 5.5 $2 / $10; Haiku 5.5 $0.10 / $0.50.

**Estimated monthly cost** for 12 agent runs/day: roughly **$30-95/month on Sonnet 5.5**, **$57-190 on Opus 5.5**, and **under $6 on Haiku 5.5**. These are estimates, not quotes. That puts a Pro or Max subscription in a similar range, as long as its usage limits fit.

### Cited Findings
**Subscription plans (claude.com/pricing)**
- Free $0; **Pro $17/month billed annually ($200 up front) or $20 monthly**; **Max $100/month** ("5x Pro usage" per 5 hours and per week; monthly only); the **$200/month tier is called Ultra**, "10x Pro usage" weekly, "No 5-hour limit" for verified accounts. Claude Code is included on Pro, Max and Ultra, not Free. No INR shown on the page as fetched. — [claude.com/pricing](https://claude.com/pricing)
- Footnote: "How fast you reach a limit depends on the model you use, how long your chats are, and how large your files are." No token or message counts are published. — [claude.com/pricing](https://claude.com/pricing)
- "Pro and Max plans have a five-hour session limit and a weekly limit." Claude and Claude Code share the limits. Max and Ultra also have a separate weekly Fable limit. Usage credits ("extra usage") can be enabled to continue past limits. **If `ANTHROPIC_API_KEY` is set, Claude Code "will use this API key for authentication instead of your Claude subscription."** — [Claude Help: Using Claude Code with Pro or Max](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- That help article says nothing about `claude -p` or scripted use and states no restriction on automated use. — same source
- Headless docs: `claude -p` works without `--bare` and loads the normal login. `--bare` "doesn't use your subscription login" and "never reads OAuth credentials", so it needs `ANTHROPIC_API_KEY` or an `apiKeyHelper`. `--output-format json` returns `total_cost_usd` (a client-side estimate). `--max-budget-usd` caps a run's spend. Docs say `--bare` "will become the default for `-p` in a future release." — [Claude Code: Run programmatically](https://code.claude.com/docs/en/headless)
- Unattended flags: `--permission-mode auto|dontAsk|acceptEdits`, `--allowedTools`, and `--permission-prompts none` for scheduled jobs (v2.1.259+). — [Run programmatically](https://code.claude.com/docs/en/headless)

**INR subscription prices (third-party press only, so not confirmed on an official Anthropic page)**
- Rupee pricing launched around 14 July 2026. Reported figures: Pro about ₹2,000/month annual or ₹2,033.05 monthly; Max 5x ₹11,999/month; "20x" ₹23,999/month; reported as GST-inclusive. — [Business Today](https://www.businesstoday.in/technology/news/story/anthropic-introduces-india-pricing-for-claude-ai-plans-pricing-starts-at-542742-2026-07-14); [Inc42](https://inc42.com/buzz/claude-rolls-out-india-pricing-as-anthropic-bets-big-on-its-second-largest-market/); [Outlook Business](https://www.outlookbusiness.com/deeptech/claude-pro-now-costs-2000-in-india-as-anthropic-localises-subscription-pricing)
- Conflicts: sources disagree on Pro (₹1,999 vs ₹2,000 vs ₹2,033.05) and on whether GST is included. A September 2026 third-party tracker lists Max at ₹12,900. The "Max 20x" name doesn't match the current official page, which calls the $200 tier "Ultra". **Treat all INR figures as unverified;** check the price shown at checkout in India.

**API prices (official, USD per million tokens; standard / 5-min cache write / 1-h cache write / cache hit / output)**
- Claude Opus 5.5: $4 / $5 / $8 / $0.20 / $20 — [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Claude Sonnet 5.5: $2 / $2.50 / $4 / $0.10 / $10 — [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Claude Haiku 5.5 (prompts up to 100K tokens): $0.10 / $0.125 / $0.20 / $0.01 / $0.50; over 100K tokens: $0.50 / $0.625 / $1 / $0.05 / $2.50 — [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Top tier for reference: Claude Fable 5.2 $8 in / $40 out. — [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)
- Batch API: 50% off input and output (Opus 5.5 $2/$10; Sonnet 5.5 $1/$5; Haiku 5.5 $0.05/$0.25). Not applicable to interactive `claude -p` runs. `inference_geo: "us"` adds a 1.1x multiplier; the default global routing is standard price. Thinking tokens are billed as output. — [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing); [Claude Code costs](https://code.claude.com/docs/en/costs)
- Prices are stated in USD only. — [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing)

**Benchmarks for Claude Code token use**
- "Across enterprise deployments, the average cost is around $13 per developer per active day and $150-250 per developer per month, with costs remaining below $30 per active day for 90% of users." That is for interactive developer use, not small scripted runs. — [Claude Code: Manage costs](https://code.claude.com/docs/en/costs)
- Cost levers: Sonnet over Opus; `model: haiku` for simple subagents; lower `/effort`; keep CLAUDE.md under 200 lines; prompt caching is automatic. — [Claude Code: Manage costs](https://code.claude.com/docs/en/costs)

**Spend limits / rate limits (API)**
- Monthly spend caps by tier: Start $500, Build $1,000, Scale $200,000. New orgs may start in a lower "Evaluation" tier. Set your own lower cap at platform.claude.com/settings/spend-limits: next to **Monthly spend limit** click **Adjust limit** / **Set limit** and enter the value. Once the cap is hit, requests return 400 "You have reached your specified API usage limits". Workspace-level spend and rate limits are also available. — [Anthropic rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- Start-tier rate limits for Opus/Sonnet/Haiku 5.5: 4,000 RPM, 2M ITPM, 400K OTPM, far above this workload. Cache reads don't count toward ITPM. — [Anthropic rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- On first Console login, Claude Code auto-creates a "Claude Code" workspace whose spend can be capped with workspace spend limits. — [Claude Code: Manage costs](https://code.claude.com/docs/en/costs)
- Subscriptions: usage-credit spend limits are set at claude.ai Settings > Usage (opened via `/usage-credits`). — [Claude Code: Manage costs](https://code.claude.com/docs/en/costs)

### Inferences (token and cost estimate; assumptions are mine, not Anthropic's)
- Workload: 6 agents × 2 jobs = **12 `claude -p` runs/day**, about 360 runs/month.
- **Heavy scenario** (default `claude -p`, which loads Claude Code's system prompt and tools): about 10 model requests per run at about 40K-token context, giving about 400K input tokens/run (about 85% cache hits) and about 8K output (including thinking). Per day: about 4.1M cache-read, 0.72M uncached/cache-write and 0.1M output tokens.
  - Sonnet 5.5: 4.08M×$0.10 + 0.72M×$2.50 + 0.096M×$10 ≈ **$3.2/day ≈ $95/month**
  - Opus 5.5: 4.08M×$0.20 + 0.72M×$5 + 0.096M×$20 ≈ **$6.3/day ≈ $190/month**
  - Haiku 5.5: ≈ $0.18/day ≈ **$5-6/month**
- **Lean scenario** (`--bare`, short prompts): about 4 requests at about 15K context, giving about 60K input/run (70% cached) and about 3K output. Per day: about 0.5M cache-read, 0.22M write and 0.036M output tokens.
  - Sonnet 5.5 ≈ **$0.95/day ≈ $29/month**
  - Opus 5.5 ≈ **$1.9/day ≈ $57/month**
- Recommendation logic:
  - Pro ($20) is likely to cover 12 short runs/day only if each run is small. Limits are unpublished and shared with chat, so hitting the 5-hour or weekly limit is a real risk on runs scheduled close together.
  - Max ($100) gives 5x headroom.
  - API + Sonnet 5.5 with a $50-100 Console spend limit gives predictable, capped spend, plus `--max-budget-usd` per run.
  - Mixing Haiku 5.5 for simple agents (e.g. metadata/caption formatting) cuts cost sharply.
- Key pitfall: if `ANTHROPIC_API_KEY` is present in the environment, Claude Code bills the API even when the user has a subscription.
- Converting USD to INR at a market rate gives a ballpark only. An API card charge from India may also attract GST and forex fees (unverified).

### Gaps
- No official statement found on whether Anthropic's consumer terms permit or limit fully automated, scheduled `claude -p` use on Pro/Max subscriptions. The help article is silent.
- Exact Pro/Max token allowances aren't published.
- INR prices are not confirmed on an official Anthropic page, and nothing official was found on whether API billing for Indian customers adds GST.
- Minimum API credit purchase amount wasn't found on the fetched pages.
- The token estimates above are modelled, not measured. Real numbers should come from `--output-format json` → `total_cost_usd` after the first few runs.
