# Instagram poster

Posts scheduled Reels to Instagram without Buffer. A GitHub Actions job
(`.github/workflows/ig-poster.yml`) checks `poster/queue/` every 10 minutes and
publishes every post that is due through the Instagram API. YouTube still goes
through Buffer.

Accounts: `ctsoccerhub` and `clip.theory67`.

## Scheduling a Reel

Add one JSON file per post to `poster/queue/`, named `<YYYY-MM-DD>-<HHMM>-<account>-<slug>.json`,
then commit and push to `main`:

```json
{
  "account": "ctsoccerhub",
  "due_at": "2026-11-06T09:00:00-05:00",
  "video_url": "https://raw.githubusercontent.com/alexemden-png/CT-Soccer/main/videos/2026-11-06/example.mp4",
  "caption": "Caption text...\n\n#soccer #ctsoccerhub",
  "share_to_feed": true
}
```

- `due_at` must include the UTC offset (build it with Python `zoneinfo`, America/New_York).
- `video_url` must be a public, direct `https` link to an `.mp4` that already returns 200.
  Instagram Reels: vertical 9:16, 3 seconds to 15 minutes, H.264/AAC MP4.
- Caption: at most 2,200 characters and 30 hashtags.
- Expect posts to go out up to about 15 minutes after `due_at` (GitHub timers can lag).
  A post more than 6 hours late is not posted and is marked `expired`.
- Instagram allows up to 100 API posts per account in 24 hours.

After an attempt the file moves to `poster/done/` with a `result` block:
`posted` (with the Reel's permalink), `failed` (after 3 attempts, with the error),
or `expired`. To cancel a post, delete its file from `poster/queue/` before it is due.
To check what's scheduled, list `poster/queue/`.

Test without posting: Actions → Instagram poster → Run workflow → tick "Only list what would be posted".
Test the tokens: Actions → Instagram poster → Run workflow → tick "Only test the Instagram tokens".

## One-time setup

The Meta app is **CT Poster** (app ID 1899738484725586), owned by the **CT Soccer Hub** business portfolio.

1. **Instagram accounts**: each must be a Professional account (Business or Creator).
   In Instagram: Settings → Account type and tools → Switch to professional account.
2. **Testers**: in the app, App roles → Roles → Add People → Instagram Tester, and add each account.
   Then, signed in to each account, accept the invite at instagram.com → Settings →
   Apps and websites → Tester invites.
3. **Tokens**: in the app, Use cases → Instagram API → Customize → API setup with Unified login.
   Meta requires a business portfolio for this, and new apps no longer get the older
   "API setup with Instagram login". Step 1 needs a configuration ("Instagram API (Unified Login)",
   system-user token that never expires). In step 2, click **Generate token** next to each account
   and copy the token.
4. **GitHub secrets**: in this repo, Settings → Secrets and variables → Actions → New repository secret:
   - `IG_TOKEN_CTSOCCERHUB`: the ctsoccerhub token
   - `IG_TOKEN_CLIPTHEORY67`: the clip.theory67 token

These are Meta system-user tokens: they start with `EAA`, never expire, and are used with
graph.facebook.com and the account IDs in `post_due.py`, so there is nothing to renew.
The poster still accepts an older Instagram user token (starts with `IG`, used with
graph.instagram.com), but such a token lasts only 60 days and would need replacing by hand.

Tokens are never committed or printed. An account without a token is skipped.
