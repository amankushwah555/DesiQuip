# Meta Graph API (Instagram + Facebook Reels) and X API video posting: setup, credentials, costs (as of 2026-11-19)

Scope: an automated pipeline that cross-posts 1-2 short comedy videos per day from India to Instagram Reels, Facebook Reels and X, plus TikTok India status.
Method note: Meta and X developer doc pages carry no "last updated" dates, so "current" means fetched on 2026-11-19. Where a claim rests only on third-party blogs, it is flagged.

## Meta: app setup, IG professional account + Page linking, permissions, App Review / Business Verification, tokens, IDs, limits, Reels specs, login options, cost

### Takeaway
Publishing Reels to your **own** Instagram professional account and your **own** Facebook Page is free and works at the default Standard Access level, as long as the accounts have a role on your app. App Review and Business Verification are formally required only for Advanced Access, which you need to serve accounts you don't own. Meta's app-creation guide does say to connect a business that has completed Business Verification "before publishing" the app; see Gaps. The simplest route that covers both IG and FB is "Instagram API with Facebook Login": one long-lived Page access token (no fixed expiry) can serve as META_TOKEN for both the IG `/media` and FB `/video_reels` calls. Limits are 100 IG API posts and 30 FB Reels per 24 h, far above 1-2 a day.

### Cited Findings

**Login/API options in 2026 (three configurations)**
- **Instagram API with Instagram Login**: no Facebook Page needed. The app user logs in with Instagram credentials and gets an Instagram User access token. Host is `graph.instagram.com`, and permissions are the `instagram_business_*` family. Hashtag search, product tagging and partnership ads are not supported. — [Meta Instagram Platform overview](https://developers.facebook.com/documentation/instagram-platform/overview)
- **Instagram API with Facebook Login**: a Facebook Page is "Required" and the IG account must be linked to it. The user logs in with Facebook and gets a Facebook User or Page access token. Host is `graph.facebook.com`, with `instagram_*` permissions plus Page permissions. The user "must also be able to perform admin-equivalent tasks on the linked Facebook Page." — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)
- **Instagram API with Unified Login**: the overview recommends it for new integrations. Users log in with Instagram or Facebook, and no Page is required. The content-publishing doc lists a "Business Integration System User token" for this mode, with `instagram_basic` and `instagram_content_publish`. — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview); [Content Publishing doc](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- Account type: "An Instagram professional account can represent a business or creator." Both Creator and Business accounts qualify. — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)

**Permissions for publishing**
- IG via Instagram Login: `instagram_business_basic` and `instagram_business_content_publish`. — [Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- IG via Facebook Login: `instagram_basic`, `instagram_content_publish` and `pages_read_engagement`. Add `ads_management` and `ads_read` if the user's role on the Page comes through Business Manager. Token is a Page access token. — [Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- FB Reels: `pages_show_list`, `pages_read_engagement` and `pages_manage_posts`, using a Page access token from a user who can perform the CREATE_CONTENT task on the Page. — [Reels Publishing guide](https://developers.facebook.com/docs/video-api/guides/reels-publishing)

**App creation steps (Meta's current guide)**
1. App Dashboard → **Create App**.
2. Use case: **Other**.
3. App type: **Business** (required to add the Instagram product).
4. Enter the app name and contact email.
5. Under **Instagram** → **Set up**, choose "API setup with Instagram login" (the default) or "API setup with Facebook login" if the IG account is linked to a Page.
6. In Step 7, "Assign an Instagram account to get access tokens for testing". The account "must be public". Manage these accounts later under **App Roles > Roles**.
- The guide also says you must connect "a business that has completed Business Verification" before publishing the app, under **App settings > Basic**.
- Source for all of the above: [Create a Meta App for Instagram Platform](https://developers.facebook.com/documentation/development/create-an-app/other-app-types/instagram-apis.md)

**App Review / Business Verification**
- "Standard Access is the default access level for all apps." Advanced Access "requires App Review and Business Verification." — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)
- Meta says you can build an app that serves only accounts you own or manage. Advanced Access (with App Review and Business Verification) is needed for professional accounts you don't own or manage. — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview); [Meta Instagram-only API overview](https://developers.secure.facebook.com/docs/instagram/instagram-only-api/overview); [Meta app review page](https://developers.facebook.com/documentation/instagram-platform/app-review)
- Standard Access only serves accounts that have a role on the app (admin, developer or tester). This detail comes from third-party blogs, not a Meta page I fetched. — [AdaptlyPost](https://adaptlypost.com/blog/instagram-business-content-publish-scope)

**Tokens (META_TOKEN)**
- Short-lived tokens last 1 hour. Long-lived tokens last 60 days and can be refreshed. — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)
- **Long-lived Facebook User token**: `GET https://graph.facebook.com/{ver}/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}`, called server-side. It "generally lasts about 60 days." — [Meta: Get long-lived tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/)
- **Long-lived Page token**: call `GET {app-scoped-user-id}/accounts` with the long-lived User token. "Long-lived Page access token do not have an expiration date" (they can still be invalidated under certain conditions). This call also lists your Pages, which gives FB_PAGE_ID. — [Meta: Get long-lived tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/)
- **Instagram Login token refresh**: `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=...`. The token must be at least 24 h old and unexpired, and the refreshed token is valid for 60 days. Requires `instagram_business_basic`. — [Meta refresh_access_token](https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token)
- **System User token**: by default it "Never expires". Setting `set_token_expires_in_60_days=true` makes it a refreshable 60-day token. Scopes include `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic` and `instagram_content_publish`. Generating one requires an `appsecret_proof`. The system user must install the app, and both must be in the same Business Manager. Only apps with "Ads Management API standard access and above" can be installed. — [Meta System Users: install apps and generate tokens](https://developers.facebook.com/docs/business-management-apis/system-users/install-apps-and-generate-tokens)

**Publishing flow and limits**
- IG Reels flow:
  1. `POST /<IG_ID>/media` with `media_type=REELS` and `video_url` (the video must be on a publicly accessible server), or `upload_type=resumable` plus an upload to `rupload.facebook.com/ig-api-upload/...`. Resumable upload works with Facebook Login only.
  2. Poll `GET /<container>?fields=status_code` about once a minute, for no more than 5 minutes, until it reads `FINISHED`.
  3. `POST /<IG_ID>/media_publish` with `creation_id`.
  - Unpublished containers expire after 24 h.
  - Source: [Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- IG limit: "Instagram accounts are limited to 100 API-published posts within a 24-hour moving period." Check usage with `GET /<IG_ID>/content_publishing_limit`. The same doc's carousel section says 50, which is an internal inconsistency. — [Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- Pages that require Page Publishing Authorization (PPA) must complete it before publishing. — [Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- FB Reels flow:
  1. `POST /{page-id}/video_reels` with `upload_phase=start`. This returns a video_id.
  2. Upload to `rupload.facebook.com/video-upload/{video-id}`, either as binary or with a `file_url` header.
  3. `POST /{page-id}/video_reels` with `upload_phase=finish` and `video_state=PUBLISHED` (DRAFT or SCHEDULED are also accepted).
  - Limit: "Reels API is limited to 30 API-published posts within a 24-hour moving period."
  - Source: [Reels Publishing guide](https://developers.facebook.com/docs/video-api/guides/reels-publishing)

**Reels specs**
- **IG Reels**:
  - MP4 or MOV with the moov atom at the front.
  - H.264 or HEVC, progressive, closed GOP, 4:2:0.
  - 23-60 fps, max 1920 px wide.
  - Aspect ratio between 0.01:1 and 10:1, with 9:16 recommended.
  - Max bitrate 25 Mbps VBR.
  - AAC audio, max 48 kHz, 128 kbps.
  - Length 3 s to 15 min, max file size 300 MB.
  - Optional parameters: `share_to_feed`, `thumb_offset`, `cover_url` (JPEG, ≤8 MB), and `trial_params` for trial reels.
  - Source: [IG User Media reference](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media)
- **FB Reels**:
  - .mp4 recommended, 9:16.
  - 1080x1920 recommended, 540x960 minimum.
  - 24-60 fps, 3-90 s (60 s max if published as a Page story).
  - Source: [Reels Publishing guide](https://developers.facebook.com/docs/video-api/guides/reels-publishing)
- The current Graph API version in Meta's examples is v27.0. — [IG User Media reference](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media)

**Cost**
- None of the Meta docs fetched mention any fee for the Graph API publishing endpoints. Usage is governed by rate limits, for example "Calls within 24 hours = 4800 * Number of Impressions". — [Meta overview](https://developers.facebook.com/documentation/instagram-platform/overview)

### Inferences
- **Recommended setup for DesiQuip**, combining the steps above:
  1. In the IG app, switch the account to Creator or Business.
  2. Link it to a Facebook Page you admin.
  3. Create a Business-type Meta app with "API setup with Facebook login".
  4. Your FB account is the app admin, so it has a role and Standard Access suffices.
  5. Get a short-lived user token with `instagram_basic, instagram_content_publish, pages_show_list, pages_read_engagement, pages_manage_posts`, for example from Graph API Explorer.
  6. Exchange it for a long-lived user token.
  7. Call `/me/accounts` to get FB_PAGE_ID and a non-expiring Page token, and use that token as META_TOKEN.
- That one Page token likely works for both IG publishing (the docs say "Facebook Page access token" for Facebook Login) and FB `/video_reels`.
- A comedy short of 3-90 s at 1080x1920 H.264/AAC MP4 under 300 MB meets both the IG and FB specs. **FB Reels caps length at 90 s**, so videos longer than 90 s must be trimmed or posted as a regular FB video.
- **IG_USER_ID**:
  - Facebook Login: likely `GET /{FB_PAGE_ID}?fields=instagram_business_account`.
  - Instagram Login: likely `GET graph.instagram.com/me?fields=user_id,username`.
  - These endpoints come from prior knowledge and were not re-fetched in this session.
- A System User token would need a Business Manager and an app with Ads Management standard access. That is more setup than needed for a single owner, and the Page token is simpler.
- At 1-2 posts a day, rate limits (100 IG / 30 FB per 24 h) are irrelevant.
- Cost: no API fee was found. A public HTTPS host for `video_url` or `file_url` is needed, unless you use resumable/binary upload.

### Gaps
- **Business Verification for an own-accounts app is unresolved.** The overview ties it only to Advanced Access, but the app-creation guide says to connect a verified business "before publishing" (switching the app to Live). It is unclear whether a Development-mode app with role-holding accounts can publish real public posts indefinitely without verification. Likely yes, but I found no explicit Meta statement.
- The Standard Access "role only" rule was confirmed only by third-party blogs.
- IG content-publishing doc says both 50 and 100 posts per 24 h. Unreconciled; irrelevant at 1-2 a day.
- The FB Reels doc parameter table and examples disagree on `upload_phase` ("complete" vs "finish"). Test both.
- No Meta doc page shows a last-updated date.
- No official Meta statement that the API is "free" was found (absence of any pricing page is the evidence).

## X API: tiers and prices (2026), video posting, caps, v2 media upload, getting X_API_KEY / X_API_SECRET / X_TOKEN

### Takeaway
X replaced fixed tiers with **pay-per-use prepaid credits** on 2026-02-06. Since 2026-04-20, `POST /2/tweets` costs **$0.015 per post**, or **$0.20 if the post contains a URL**. There is no monthly fee and no published monthly post cap for writes; the only stated cap is 3M post *reads* per month. Video posting uses the v2 chunked upload (`/2/media/upload/initialize|append|finalize`). At 1-2 video posts a day without links, the cost is roughly $0.45-$0.90 a month. If a link is included in every post, it rises to about $6-$12 a month. One-time promo credits ($20, plus a match of up to $50) may cover this for months. No INR price is published.

### Cited Findings

**Pricing model and rates**
- The model is pay-per-usage with prepaid credits bought in the Developer Console, with "no subscriptions, contracts, or minimum spend". You can set a spend cap per billing cycle. — [X API pricing docs](https://docs.x.com/x-api/getting-started/pricing)
- Write prices:

  | Action | Price |
  |---|---|
  | Post: Create | $0.015 |
  | Post: Create (with URL) | $0.200 |
  | Post: Create (summoned reply) | $0.010 |
  | Interaction: Delete | $0.010 |
  | Media Metadata | $0.005 |
  | Owned Reads | $0.001 per resource |

  There is **no separate media-upload line item**. Source: [X API pricing docs](https://docs.x.com/x-api/getting-started/pricing)
- "Pay-per-usage plans are capped at 3 million Post reads per monthly billing cycle." Above that, Enterprise (no public price) applies. — [X API pricing docs](https://docs.x.com/x-api/getting-started/pricing)
- Changelog 2026-02-06: pay-per-use launched as "a flexible credit-based model built for indie builders, startups, and hobbyists". "Basic and Pro plans remain available, and existing subscribers can opt in". Recently active legacy Free users got a one-time $10 voucher. — [X changelog](https://docs.x.com/changelog)
- Changelog 2026-04-16 (effective 2026-04-20): POST /2/tweets became $0.015, posts with a URL $0.20, and summoned replies stayed at $0.01. "Following, Likes, and Quote-Posts via the API have been removed from all self-serve tiers." — [X changelog](https://docs.x.com/changelog)
- Changelog 2026-10-02: a one-time $20 credit when you save your first eligible payment card, and a one-time match of the first auto-recharge up to $50. Credits are used first and expire after 3 months. — [X changelog](https://docs.x.com/changelog); [X pricing docs](https://docs.x.com/x-api/getting-started/pricing)
- **Legacy tiers (conflicting reports)**:
  - Secondary sources say a 2026-05-21 changelog entry deprecated legacy Basic, with auto-migration after 2026-06-01. They also say legacy Pro was deprecated around 2026-08-14, with migration after 2026-09-01. — [maxrave.dev](https://maxrave.dev/articles/x-legacy-basic-api-plans-moving-to-pay-per-use); [OpenTweet migration guide](https://opentweet.io/how-to/migrate-x-api-pro-to-pay-per-use)
  - **Conflict:** my fetch of the official changelog did not surface those entries, and the 2026-02-06 entry says Basic and Pro "remain available" to existing subscribers. Either way, **new sign-ups only get pay-per-use**. — [X changelog](https://docs.x.com/changelog); [Gigazine](https://gigazine.net/gsc_news/en/20260209-x-api-pay-per-use)
- No free self-serve posting tier for new developers is listed on the official pricing page. "Public Utility Apps" keep free access. — [X pricing docs](https://docs.x.com/x-api/getting-started/pricing); [X changelog](https://docs.x.com/changelog)

**Video upload (v2)**
- Endpoints:
  - `POST /2/media/upload/initialize` returns a media_id.
  - `POST /2/media/upload/{id}/append` sends chunks of 5 MB or less, indexed from 0.
  - `POST /2/media/upload/{id}/finalize`.
  - Poll `GET /2/media/upload?command=STATUS&media_id=...` until the state is `succeeded`.
  - Then `POST /2/tweets` with `media.media_ids`.
  - Use `media_category=tweet_video` (`amplify_video` is for ads).
  - The old `command=INIT/APPEND/FINALIZE` on `POST /2/media/upload` is the previous protocol.
  - Source: [X chunked media upload quickstart](https://docs.x.com/x-api/media/quickstart/media-upload-chunked)
- Video limits since 2026-09-01 follow the *posting user's* status, not the developer plan: 20 min / 8 GB by default, 125 min / 16 GB for Premium or verified accounts. Over-length video returns 403. — [X changelog](https://docs.x.com/changelog); [chunked upload quickstart](https://docs.x.com/x-api/media/quickstart/media-upload-chunked)
- Media upload auth: OAuth 2.0 user context with scope `media.write`, plus a `UserToken` "OAuth" scheme (presumably OAuth 1.0a user context; the page doesn't name the version). — [X Upload media reference](https://docs.x.com/x-api/media/upload-media)

**Credentials**
- **X_API_KEY and X_API_SECRET**:
  - "App Key === API Key === Consumer API Key" (`oauth_consumer_key`).
  - "App Key Secret === API Secret Key === Consumer Secret".
  - Both and the callback URLs are under the app's settings in the **Developer Console**.
  - OAuth 1.0a user access token and secret come from the 3-legged flow: `POST oauth/request_token` → `GET oauth/authorize` → `POST oauth/access_token`. "These tokens do not expire but can be revoked by the user at any time."
  - Source: [X OAuth 1.0a: obtaining user access tokens](https://docs.x.com/fundamentals/authentication/oauth-1-0a/obtaining-user-access-tokens)
- **OAuth 2.0 PKCE**:
  - Enable OAuth 2.0 in the app's authentication settings. Client ID and Secret are under Keys and Tokens (the secret appears only for confidential app types: Web App, Automated App or bot).
  - Authorize at `https://x.com/i/oauth2/authorize` with `code_challenge`. Exchange at `https://api.x.com/2/oauth2/token` within 30 s.
  - Access tokens last **2 hours**. Request `offline.access` to get a refresh token (`grant_type=refresh_token`).
  - Scopes needed: `tweet.write`, `users.read`, `tweet.read`, `media.write`, `offline.access`.
  - Source: [X OAuth 2.0 authorization code](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code)

### Inferences
- **For a single-account bot, OAuth 1.0a is simplest.** Set app permissions to "Read and write", then generate the Access Token and Secret for your own account in the Developer Console. These never expire. Use them as X_TOKEN (plus the token secret) alongside X_API_KEY and X_API_SECRET.
  - The "generate for own account in console" step is standard practice but was not confirmed on a fetched page.
  - Permissions must be set *before* generating the token, or it will be read-only (from prior knowledge).
- OAuth 2.0 PKCE needs refresh-token rotation every 2 hours, which is more moving parts for a cron pipeline.
- Cost per month at 1-2 posts a day (30-60 posts):
  - No link: $0.45-$0.90.
  - Link in every post: $6-$12.
  - Media upload calls appear unbilled; if they were billed as Media Metadata, that would be at most a few cents.
- **Keep links out of the post text, or put them in a reply**, to avoid the 13x URL price. Note that a reply is also a billed post.

### Gaps
- No INR pricing is published; X bills in USD credits. The INR equivalent and any GST on Indian cards are unverified.
- Whether media upload (`initialize/append/finalize`) requests are billed at all is not stated. The pricing page has no media-upload line.
- The legacy Basic/Pro deprecation dates (2026-05-21 / 2026-08-14) are not confirmed in my fetch of the official changelog. Treat them as unverified.
- No explicit monthly *post-write* cap for pay-per-use was found; only the 3M read cap. Platform rate limits per endpoint were not checked.
- The exact console UI steps (Developer Console app creation, use-case description, India-specific eligibility) were not fetched. No India restriction was found.

## TikTok in India: is the ban still in force (Nov 2026)?

### Takeaway
Yes, as far as reliable reporting shows. TikTok has been banned since June 2020 under Section 69A of the IT Act, the ban was made permanent in January 2021, and the government and TikTok have both reaffirmed it after repeated "comeback" rumours (August 2025, and a website glitch around July 2026). I found no report of the ban being lifted as of November 2026, but I also found no article dated October or November 2026.

### Cited Findings
- In June 2020 the IT Ministry ordered a ban on 59 apps including TikTok. — [Rolling Stone India](https://rollingstoneindia.com/government-of-india-bans-tiktok-more-malicious-apps/amp)
- In August 2025 TikTok denied an India comeback after its website became reachable. It said: "We have not restored access to TikTok in India and continue to comply with the Government of India's directive." — [TechCrunch, 2025-08-22](https://techcrunch.com/2025/08/22/tiktok-denies-india-comeback-after-reports-of-website-going-live); [Digiteye fact check](https://digiteye.in/has-india-revoked-ban-on-tiktok-amid-us-tariffs-pm-modis-china-visit-fact-check/)
- The government clarified the ban "continues to be in place", and Minister Ashwini Vaishnaw said there is no plan to lift it. — [OdishaBytes](https://odishabytes.com/ban-on-tiktok-and-other-chinese-apps-continues-to-be-in-place-government-clarifies/); [OdishaBytes](https://odishabytes.com/is-tiktok-making-a-comeback-in-india-no-plan-to-lift-ban-says-ashwini-vaishnaw/)
- A 2 February 2026 report says the ban was not lifted according to the Modi government. — [Patrika](https://www.patrika.com/en/national-news/tiktok-ban-in-india-not-lifted-says-modi-government-19886142)
- Around July 2026 there was a website-return rumour; the government addressed it, and ByteDance denied a relaunch, calling it a "glitch". — [NavbharatLive](https://navbharatlive.com/technology/government-breaks-silence-on-tiktok-return-to-india-what-is-the-truth-behind-this-1347291.html); [National Herald](https://www.nationalheraldindia.com/amp/story/science-tech/tiktok-isnt-back-just-a-glitch-in-the-system)

### Inferences
- TikTok should be excluded from an India-based pipeline. The official app is unavailable, and using the TikTok API from India would violate the government directive.

### Gaps
- No source dated October or November 2026 was found. The status "still banned" as of 2026-11-19 is inferred from the latest available reports (February and July 2026) plus the absence of any reversal news.
