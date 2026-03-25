# HuggingFace Daily Papers Digest

Track the most impactful AI papers every day — filtered by community upvotes and GitHub stars.

## What This Skill Does

When invoked (`/hf` or asking about today's papers), this skill:
1. Fetches today's HuggingFace daily papers via their JSON API
2. Filters to papers with **upvotes >= 20** OR **GitHub stars >= 100** (configurable)
3. Generates a concise structured summary for each qualifying paper
4. Delivers via your configured method (stdout, Telegram, or email)

---

## Onboarding (First Run)

Check for `~/.hf-papers/config.json` with `onboardingComplete: true`. If absent, guide the user through these steps sequentially:

### Step 1 — Introduction
Explain: "This skill monitors HuggingFace's daily paper submissions and surfaces the ones getting real traction — based on community upvotes and GitHub stars. You'll get a daily digest of only the papers worth reading."

### Step 2 — Upvote Threshold
Ask: "How many upvotes should a paper have to be included? Default is 20. Papers with fewer upvotes but popular GitHub repos will also be included."
Save to `config.upvoteThreshold`.

### Step 3 — GitHub Stars Threshold
Ask: "What's the minimum GitHub stars for a paper's code repo to qualify? Default is 100."
Save to `config.githubStarsThreshold`.

### Step 4 — Language
Ask: "Would you like the digest in English, Chinese (中文), or bilingual (both, interleaved paragraph by paragraph)?"
Options: `en`, `zh`, `bilingual`. Save to `config.language`.

### Step 5 — Delivery Method
Ask: "How should I deliver the digest?"
- **Here in the terminal** (stdout) — works right now, no setup needed
- **Telegram** — sends to a Telegram chat/channel automatically
- **Email** — sends via Resend API

Save to `config.deliveryMethod`.

If Telegram: explain how to create a bot via @BotFather, get the token, and find chat ID. Ask for `chatId`, save to `config.telegram.chatId`. Tell them to add `TELEGRAM_BOT_TOKEN=xxx` to `~/.hf-papers/.env`.

If Email: ask for email address, save to `config.email.address`. Tell them to add `RESEND_API_KEY=xxx` to `~/.hf-papers/.env`.

### Step 6 — Schedule (optional)
Ask: "Would you like a daily or weekly digest? At what time and timezone?"
Save to `config.schedule` and `config.timezone`.

For automated delivery (Telegram/Email), suggest setting up a cron job:
```
# Add to crontab (crontab -e):
# Daily at 9:00 AM Beijing time (UTC+8 = 1:00 AM UTC):
0 1 * * * cd /path/to/auto-hf-papers && node scripts/fetch-papers.js | claude -p "$(cat prompts/summarize-paper.md)" | node scripts/deliver.js
```

### Step 7 — Mark Complete & Run First Digest
Set `config.onboardingComplete = true`. Write the complete config to `~/.hf-papers/config.json` (create directory if needed).

Immediately run the first digest (see Content Delivery Workflow below) and ask for feedback.

---

## Content Delivery Workflow

When the user invokes `/hf`, asks for "today's papers", or the scheduled task fires:

### Step 1 — Load config
Read `~/.hf-papers/config.json`. Use defaults if missing (upvotes=20, stars=100, language=en, delivery=stdout).

### Step 2 — Fetch and filter papers
Run: `node scripts/fetch-papers.js`

Optional overrides:
- `node scripts/fetch-papers.js --date=2026-03-20` for a specific date
- `node scripts/fetch-papers.js --upvotes=10 --stars=50` to override thresholds

The script outputs a JSON blob to stdout containing:
- `date` — the date fetched
- `stats` — total papers, filtered count, thresholds used
- `papers` — array of filtered papers with title, upvotes, githubStars, abstract, authors, links
- `prompts` — summarizePaper, digestIntro, translate prompt texts
- `errors` — non-fatal errors (empty array if all went well)

### Step 3 — Check for content
If `papers` array is empty:
- Tell the user: "No papers today exceeded the thresholds (upvotes >= X, stars >= Y). Total papers submitted: N."
- Suggest: "You can lower thresholds with `node scripts/fetch-papers.js --upvotes=5`"
- Stop here.

### Step 4 — Generate the digest
Using the JSON output:

**Header:** Apply the `digestIntro` prompt — fill in date, stats (filtered, total, upvoteThreshold, starsThreshold).

**Per paper:** For each paper in the `papers` array (sorted by upvotes desc), apply the `summarizePaper` prompt:
- Include title, upvotes, githubStars, TL;DR from abstract, what they did, why it matters
- Always include hfUrl and arxivUrl links
- Only include githubRepo link if the field is non-null
- Use aiSummary and abstract fields — do NOT fabricate content or visit external URLs
- Keep each paper under 150 words

**CRITICAL RULES:**
- NEVER invent or fabricate content. Only use what's in the JSON.
- Every paper must have its hfUrl and arxivUrl included.
- Job titles / affiliations come from the authors field only.

### Step 5 — Apply language setting
- `en` → keep English only
- `zh` → translate full digest to Chinese following translate prompt
- `bilingual` → interleave English and Chinese paragraph by paragraph following translate prompt

### Step 6 — Deliver
Pipe the digest text through `node scripts/deliver.js` or display inline based on `config.deliveryMethod`.

---

## Configuration Management

All preferences can be changed via conversation at any time:
- "Change language to Chinese" → update `config.language = "zh"`
- "Lower the upvote threshold to 10" → update `config.upvoteThreshold = 10`
- "Switch delivery to Telegram" → update `config.deliveryMethod = "telegram"`, collect chatId and token

Config file location: `~/.hf-papers/config.json`
API keys location: `~/.hf-papers/.env`

## Prompt Customization

Users can override any prompt by copying files to `~/.hf-papers/prompts/`:
- `~/.hf-papers/prompts/summarize-paper.md` — customize paper summary format
- `~/.hf-papers/prompts/digest-intro.md` — customize digest header
- `~/.hf-papers/prompts/translate.md` — customize translation style

These take priority over the project defaults. Changes take effect on the next run.

---

## Data Source

Papers are fetched from the official HuggingFace API:
`https://huggingface.co/api/daily_papers?date=YYYY-MM-DD`

The API returns upvote counts and GitHub star counts directly — no GitHub API calls needed.
Papers are submitted by the community to https://huggingface.co/papers each day.
