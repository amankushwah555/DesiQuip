# Affiliate and link-tracking services for an Indian YouTube comedy channel (Amazon Associates India, EarnKaro, Cuelinks/vCommission, Bitly, ASCI disclosure)

Research date: 2026-11-19. Pages were fetched live on that date unless noted. "Unverified" means no official source confirmed the point.

## Amazon Associates India: signup, tracking ID, 180-day rule, PA-API retirement, Creators API, disclosure

### Takeaway
You can join Amazon Associates India for free at affiliate-program.amazon.in. Plain tagged links (SiteStripe or a `?tag=` link) work from day one, with no API. The current India Operating Agreement fixes the disclosure wording, the INR 1,000 NEFT payout threshold and the roughly 60-day payment lag. PA-API 5.0 is retired: calls now return 403. Its replacement, the Creators API, needs at least 10 qualifying sales in the past 30 days. Each account starts at 1 TPS / 8,640 requests per day and loses API access after 30 days without referred sales. The "3 sales in 180 days or the account closes" rule appears only on Amazon's US and Canada help pages. I did not find it on an India page.

### Cited Findings
**Creators API: what it is, eligibility, credentials**
- The Creators API replaces PA-API 5.0. It "provides the same functionality as PA-API 5.0" but uses OAuth 2.0 authentication and improved credential management — [Amazon Creators API migration guide (amazon.in host)](https://affiliate-program.amazon.in/creatorsapi/docs/en-us/migrating-to-creatorsapi-from-paapi)
- Eligibility: you must be enrolled in Associates for the target marketplace and "Have at least 10 qualifying sales within the past 30 days to access the PA API through the Creators API". **This confirms the project spec's 10-sales-in-30-days figure.** — [Creators API docs home](https://affiliate-program.amazon.com/creatorsapi/docs/)
- Registration flow: enroll in Associates, meet the sales requirement, register for API access in Associates Central, then generate credentials — [Creators API docs home](https://affiliate-program.amazon.com/creatorsapi/docs/)
- Credential creation steps:
  1. In Associates Central, open Tools > CreatorsAPI.
  2. Click "Create Application" and enter a name.
  3. Click "Create Credential" and save the **Credential ID** (replaces the AWS Access Key), the **Credential Secret** (replaces the AWS Secret Key) and the **Version** (assigned by region).
  - The secret "will only be displayed once during creation". If you lose it, you must create a new credential. — [Migration guide (amazon.in)](https://affiliate-program.amazon.in/creatorsapi/docs/en-us/migrating-to-creatorsapi-from-paapi)
  - So AMZ_CREATORS_KEY in practice means a Credential ID plus Secret plus Version, not a single key.
- India (amazon.in) is one of the 22 locales in the Creators API Locale Reference — [Locale reference](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/locale-reference)
- API operations: SearchItems, GetItems, GetVariations, GetBrowseNodes — [Creators API docs home](https://affiliate-program.amazon.com/creatorsapi/docs/)

**Creators API rate limits**
- Initial limit: "one request per second (one TPS)" and "a cumulative daily maximum of 8640 requests per day (8640 TPD) for the first 30-day period" — [API Rates page](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)
- Scaling: "one TPD for every five cents or one TPS (up to a maximum of ten TPS) for every $4320 of shipped item revenue". The limit is based on the previous 30 days and recalculated daily. — [API Rates page](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)
- An account that "has not generated qualified referring sales" in 30 days loses access. Access returns "within two days" after referred sales ship. SiteStripe and other linking tools stay available meanwhile. — [API Rates page](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)
- Requests over the limit return `429 TooManyRequests` — [API Rates page](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)

**PA-API 5.0 retirement**
- Amazon's deprecation page says PA-API 5 "has been deprecated and is being replaced by the Creators API". Calls now return **HTTP 403 Forbidden with AccessDeniedException**, pointing to the migration guide. — [PA-API v5 deprecation page](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation)
- Date: the PA-API 5 documentation reportedly said it "will be deprecated on May 15th, 2026" (search snippet; I did not re-fetch the page) — [webservices.amazon.com PA-API 5 docs](https://webservices.amazon.com/paapi5/documentation/)
  - A third-party article gives April 30, 2026 as the deprecation/migration cutoff and May 15, 2026 as endpoint retirement — [DEV Community](https://dev.to/th3nate/amazon-pa-api-v5-is-shutting-down-april-30-2026-here-is-what-changes-at-the-auth-layer-22ek); [affiliate-toolkit](https://www.affiliate-toolkit.com/affiliate-toolkit-3-8-5-amazon-creators-api-support-why-you-need-to-migrate-before-may-15-2026/)
  - Treat May 15, 2026 as the probable date. The fetched official deprecation page itself states no date.

**Signup, tracking ID, payout, operating agreement (India)**
- India Operating Agreement (page says "Updated: November, 2021"):
  - Payment requires "at least INR1000 in case of NEFT transfers".
  - Payment is made "approximately 60 days following the end of each calendar month".
  - NEFT is the only payment method named.
  - [Amazon.in Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)
- Links must "properly utilize the special 'tagged' link formats" (Section 3). Improperly formatted links are not tracked and earn no fees (Section 7). — [Amazon.in Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)
  - The agreement does not explicitly mention link shorteners or cloaking. It defines "Redirecting Link" only to exclude search-engine redirects from fees.
- 180-day rule (Amazon US help): "we require at least three [qualified sales] within the first 180 days". The application can be withdrawn if there are not enough qualifying sales in the 180 days after submission. — [Amazon US Associates help: Application Review Process](https://affiliate-program.amazon.com/gp/associates/help/t21); [Amazon.ca Account Dormancy](https://associates.amazon.ca/help/node/topic/G7MJTPEP9NC3YKMG)
  - Third-party India guides say the same 3 sales / 180 days applies to amazon.in, with automatic closure and the option to reapply — [fluxnote India guide](https://fluxnote.io/guides/amazon-associates-india-how-to-join-2026); [techtactician](https://techtactician.com/amazon-affiliate-3-sales-in-180-days)
  - The India Operating Agreement text I fetched does not contain this rule.
- Commission rates vary by category; the third-party figures below are unofficial:
  - Electronics 1–3%, Fashion 5–9% — [fluxnote 2026 rates guide](https://fluxnote.io/guides/amazon-india-affiliate-commission-rates-2026)
  - Cookie window reportedly 24 hours — [fluxnote earnings guide](https://fluxnote.io/guides/amazon-associates-earnings-india-guide)
  - I did not fetch the official fee schedule.
- Signup costs nothing: no official fee is mentioned in any page I read. Signup steps in the guides (Associates Central sign-in, add website/YouTube channel URL, choose a store ID, which becomes the tracking ID such as `name-21`) are from third-party guides only — [fluxnote India join guide](https://fluxnote.io/guides/amazon-associates-india-how-to-join-2026)

**Disclosure**
- Section 10 requires you to "clearly and prominently state" exactly: **"As an Amazon Associate I earn from qualifying purchases."** (or a substantially similar statement previously allowed) — [Amazon.in Operating Agreement](https://affiliate-program.amazon.in/help/operating/agreement)
- The Influencer Program Policy additionally asks for link-level disclosures such as "(paid link)", "#ad", "#PaidPartnership" or "#Sponsored", placed "near any affiliate link or product review in a location that customers will notice easily" — [Amazon.in Operating Agreement / policies](https://affiliate-program.amazon.in/help/operating/agreement)

### Inferences
- A new channel will almost certainly not have API access at launch. The workflow should use plain tagged URLs, built by hand as `https://www.amazon.in/dp/<ASIN>?tag=<AMZ_TAG>` or from SiteStripe/amzn.to, until it reaches 10 sales in 30 days. Even then the API is only for product data (titles, prices, images). It is not needed to earn commission.
- Code should treat the Creators API as optional. It must degrade gracefully on 403/429 and when access is lost after 30 sales-free days.
- The first 180 days are the real risk. At 2–3 links per video, a comedy channel needs 3 separate qualifying orders, and personal orders do not count.

### Gaps
- No official amazon.in help page fetched states the 180-day/3-sale rule. It may still apply (US/CA docs confirm it), but the India confirmation is unverified.
- The exact "Version" value and token endpoint for the India/EU region on the Creators API are unverified: the locale page did not list them.
- Whether Bitly-shortened Amazon links are allowed under the India agreement is unverified. The agreement says nothing explicit. Amazon's own amzn.to (SiteStripe) shortener is the safe choice.
- The official commission rate table for India was not fetched (unverified).
- The exact PA-API retirement date is not on the current official deprecation page (May 15, 2026 is from a search snippet).

## EarnKaro: signup, API, payout, fees

### Takeaway
EarnKaro is free and app-based. You sign up with email, mobile and password, then make "Profit Links" one at a time with "Make Link". There is no documented public API or developer key. An EARNKARO_KEY may not exist for a small channel, so plan on manual link creation. The minimum payout is ₹10 by free NEFT, and earnings take 30–90 days to confirm.

### Cited Findings
- Sign up: click "Get Started" on the home page and enter email, mobile number and password. Links are made one at a time in the app with "Make Link". — [EarnKaro FAQ](https://earnkaro.com/faq)
- The FAQ mentions no API, bulk converter or developer access — [EarnKaro FAQ](https://earnkaro.com/faq)
- An "Affiliaters" tool automates deal-sharing for large Telegram, WhatsApp and Facebook groups (ek.affiliaters.in). EarnKaro's Magic Tool page says accounts with good traffic can get a Telegram bot set up via an account manager. — [EarnKaro: how to get your own Flipkart tag](https://earnkaro.com/profitshala/ek-affiliaters/how-to-get-your-own-flipkart-tag); [EarnKaro Magic Tool](https://earnkaro.com/profitshala/magic-tool/what-is-magic-tool)
- Payout: you can withdraw once confirmed profit is ₹10 or more ("lowest in the industry") — [EarnKaro homepage](https://earnkaro.com/) (via search snippet)
- Payments go by NEFT to an Indian bank account and are free; you request them under Profile > My Payments — [EarnKaro FAQ](https://earnkaro.com/faq)
- Confirmation time: pending profit appears "within 5 minutes to 72 hours of a sale", and confirmation "can take anywhere between 30 to 90 days" (elsewhere in the FAQ: "48 hours to 90 days") — [EarnKaro FAQ](https://earnkaro.com/faq)
- Support contact: support@earnkaro.com — [EarnKaro contact](https://earnkaro.com/blog/contact-us/)

### Inferences
- EarnKaro is a sub-affiliate aggregator: it keeps part of the retailer commission. Its value is access to Flipkart, Myntra, Ajio and others without separate approval. For an automated pipeline, expect a manual step or a request to an account manager for API or bot access.

### Gaps
- Whether a public link-conversion API exists, and how to get an EARNKARO_KEY: **unverified**, with no official documentation found. The `ekaro-api.affiliaters.in` endpoint seen in community code has no official docs.
- EarnKaro's revenue share as a percentage of the retailer commission: unverified.
- YouTube-specific rules: none found.

## Cuelinks (and vCommission as an alternative): signup, API, payout

### Takeaway
Cuelinks is free to join and pays out from ₹500 to Indian banks. It keeps "a small portion" of the commission (no percentage given). It has a documented REST API with self-serve keys under Resource Center > API Key and `Authorization: Token <key>`. However, the link-convert endpoint needs the `write:links` scope, which seems to require the sales-assisted Publisher Plus tier; the free Starter tier gets only `read:campaigns`. vCommission pays monthly with a ₹1,000 threshold for Indian affiliates. Its API is thinly documented publicly.

### Cited Findings
**Cuelinks**
- "Cuelinks is free to join for all website owners, bloggers, content writers, and social media influencers." The page lists no approval criteria and does not mention YouTube. — [Cuelinks publishers](https://www.cuelinks.com/publishers)
- "The minimum payout on Cuelinks is Rs.500 for affiliates with Indian bank accounts"; Rs.20,000 for non-Indian accounts; payment by bank transfer — [Cuelinks publishers](https://www.cuelinks.com/publishers)
- Fee model: "we do take a small portion of the commission earned" (no % stated) — [Cuelinks publishers](https://www.cuelinks.com/publishers)
- API key: sign in, go to Resource Center > API Key (cuelinks.com/api-key), click "Create new key" and choose scopes. The header is `Authorization: Token <key>`. — [Cuelinks developer docs](https://developers.cuelinks.com/)
- Endpoints:
  - `POST /pub_api/v3/links/convert` turns any URL into a tracked affiliate link (needs `write:links`).
  - `POST /pub_api/v3/links/monetize` returns a link plus rewritten copy.
  - [Cuelinks developer docs](https://developers.cuelinks.com/)
- Tiers:
  - Free Starter: `read:campaigns` only.
  - Publisher Plus (Growth): full read/write.
  - Enterprise: custom scopes and rate limits.
  - Plus and Enterprise require contacting sales. Rate limits "scale with your plan", with no numbers given.
  - [Cuelinks developer docs](https://developers.cuelinks.com/)
- Cuelinks also offers an MCP server (mcp.cuelinks.com) — [Cuelinks publishers](https://www.cuelinks.com/publishers)

**vCommission**
- vCommission "works on a monthly payment terms across all advertisers". Indian affiliates have a default threshold of Rs. 1,000 in approved commissions, paid by bank transfer only. — [vCommission payments](https://vcommission.com/payments)
- Directory sites list a $100 minimum with monthly payout (probably the non-India threshold; conflicts with the ₹1,000 above) — [Post Affiliate Pro directory](https://www.postaffiliatepro.com/affiliate-program-directory/vcommission-affiliate-program); [QualityUnit directory](https://cdn.qualityunit.com/affiliate-program-directory/vcommission-affiliate-program)
- API key: a third-party integrator says to log into the vCommission publisher dashboard and go to Account > API (or Tools > APIs) to generate or request a key — [WeCanTrack vCommission integration](https://wecantrack.com/vcommission-integration/)

### Inferences
- With Cuelinks you could fall back to manual links or the browser extension and dashboard link tools on the free tier. Automating via the API means asking Cuelinks sales for the write scope.
- vCommission is mostly CPA and offer-based (apps, finance, D2C). It suits product-link videos less well than Cuelinks or EarnKaro, which deep-link retailer product pages, but this is an inference.

### Gaps
- Cuelinks: the exact share it keeps, payout timing, TDS handling, Publisher Plus price, and whether free-tier keys can call `/links/convert` are all unverified. The docs only imply that write needs Plus.
- vCommission: official API docs, approval criteria for YouTube-only publishers, and the deeplink generator are unverified (no official page found). Its signup steps were not researched from an official page.

## Bitly: API token, free limits, paid plans, self-hosted alternatives

### Takeaway
Create the BITLY_TOKEN at app.bitly.com/settings/api/ and send it as `Authorization: Bearer <token>`. The Free plan allows only 5 links/month and 1,000 API requests/month, with an ad interstitial. That is too small for 2–3 links × several videos a month. The cheapest paid plan is Core at $10/month, billed annually ($120/yr, 100 links/mo, 5,000 API requests/mo). The pricing page shows no INR prices. Shlink and YOURLS are free, MIT-licensed, self-hosted alternatives with REST APIs.

### Cited Findings
- Token: go to Developer settings at app.bitly.com/settings/api/ and generate a token. Auth header: "Authorization: Bearer {token}". Don't request tokens repeatedly via `/oauth/access_token`, or you will be rate-limited. — [Bitly dev docs: authentication](https://dev.bitly.com/docs/getting-started/authentication/)
- Plans (USD, no INR shown):

| Plan | Price | Links/mo | QR codes/mo | API requests/mo | Custom domain |
|---|---|---|---|---|---|
| Free | $0, with ads | 5 | 2 | 1,000 | No |
| Core | $10/mo, annual only ($120/yr) | 100 | 5 | 5,000 | No |
| Growth | $29/mo ($348/yr) | 500 | 10 | 25,000 | Yes (free custom domain) |
| Premium | $199/mo ($2,388/yr) | 3,000 | 200 | 50,000 | Yes |
| Enterprise | Custom | – | – | – | – |

  Free also includes 3 custom back-halves/mo and unlimited clicks. — [Bitly pricing](https://bitly.com/pages/pricing)
- Free-plan links reportedly show an interstitial ad before redirecting (third-party) — [linklyhq Bitly free plan](https://linklyhq.com/blog/bitly-free-plan)
  - Some competitor blogs claim 10 free links/month — [cutt.ly comparison](https://cutt.ly/resources/blog/cuttly-vs-bitly-2026)
  - This conflicts with Bitly's own page, which says 5.
- Shlink is an API-first, MIT-licensed, PHP self-hosted shortener with visit analytics, QR codes, custom slugs, multi-domain support, bot detection, a REST API and a CLI. YOURLS is an MIT-licensed PHP shortener with an API, click stats and plugins. — [selfhostyourself: Shlink](https://selfhostyourself.com/services/shlink); [selfhostyourself: YOURLS](https://selfhostyourself.com/services/yourls); [euro-stack Shlink](https://euro-stack.com/solutions/shlink)

### Inferences
- At 2–3 links/video and about 8–12 videos/month (assumed), you need about 16–36 links/month. That rules out Free and fits Core (100).
- For Amazon links, amzn.to from SiteStripe is free and Amazon-sanctioned, which avoids the shortener-policy question. A self-hosted Shlink on a cheap VPS or free tier costs nothing in licence fees, but you must run the server and domain yourself.

### Gaps
- INR pricing for Bitly: not shown on the pricing page. Indian GST or billing currency is unverified.
- Monthly-billing (non-annual) prices for Growth and Premium are not shown on the page.
- Bitly's per-hour or per-minute API rate limits were not fetched.

## India rules: ASCI influencer guidelines on affiliate disclosure in videos

### Takeaway
ASCI's influencer guidelines treat any "material connection", including monetary compensation, as requiring a disclosure label. Only #Advertisement, #Ad, #Sponsored, #Collaboration, #Partnership, #Employee and #Free gift are permitted; "#affiliate" is not on the list. For YouTube videos of 2 minutes or more, the label must stay on screen for the whole duration of the sections where the promoted product is mentioned. Live streams need it at the start and end. Captions/descriptions must carry it "in a manner that is hard to miss". ASCI pages do not address affiliate links specifically.

### Cited Findings
- Material connection includes "monetary or other compensation" and "discounts" — [ASCI social FAQs](https://www.ascionline.in/social/faqs/)
- Permitted labels: #Advertisement, #Ad, #Sponsored, #Collaboration, #Partnership, #Employee, #Free gift. "No other labels can be used." The list is reviewed periodically. — [ASCI social FAQs](https://www.ascionline.in/social/faqs/)
- Video timing:
  - Up to 15s: at least 3 seconds.
  - Over 15s and under 2 min: at least one-third of the length.
  - 2 min or longer: "the disclosure has to stay for the entire duration in sections where the promoted brand or its features are mentioned".
  - With a caption: in the caption "in a manner that is hard to miss".
  - Live streams: "at the beginning and end of the broadcast".
  - Audio/podcasts: at the start and end.
  - [ASCI social FAQs](https://www.ascionline.in/social/faqs/)
- For video-only posts without caption text, the label must be superimposed on the video. ASCI also suggests platform tools such as "paid partnership" tags. — [ASCI Influencer Guidelines PDF (Apr 2025)](https://www.ascionline.in/social/wp-content/uploads/2025/04/ASCI-Influencer-Guidelines.pdf) (via search snippet; the PDF text could not be extracted); [ASCI 2023 guidelines PDF](https://www.ascionline.in/wp-content/uploads/2023/08/GUIDELINES-FOR-INFLUENCER-ADVERTISING-IN-DIGITAL-MEDIA.pdf)
- ASCI notifies both the brand owner and the influencer of violations — [asci.social guidelines PDF](https://asci.social/assets/files/ASCI%20Guidelines%20-%20Influencer%20Advertising%20In%20Digital%20Media.pdf) (via search snippet)

### Inferences
- A practical compliant setup for each video:
  - Put "#Ad" plus the Amazon sentence at the top of the YouTube description, above the fold and next to the links.
  - Turn on YouTube's "includes paid promotion" flag.
  - Show an on-screen "#Ad" overlay whenever a linked product is shown or mentioned. For videos of 2 minutes or more, it must cover those whole segments.
- Combined description line: "#Ad — As an Amazon Associate I earn from qualifying purchases. Links below are affiliate links; I may earn a commission."

### Gaps
- ASCI does not explicitly say whether pure affiliate links, with no brand brief, need the same in-video overlay. I found no ASCI text specific to affiliate links. Treating them as a material connection is an inference from the "monetary compensation" definition.
- The April 2025 ASCI PDF text could not be extracted, so whether it adds affiliate-specific rules is unverified. Rules are taken from the live ASCI FAQ page.
