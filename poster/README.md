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

## One-time setup

1. **Instagram accounts**: each must be a Professional account (Business or Creator).
   In Instagram: Settings → Account type and tools → Switch to professional account.
2. **Meta app**: at developers.facebook.com → My Apps → Create app. Choose the use case
   for managing content on Instagram (Instagram API with Instagram Login). The app can stay in
   Development mode, since it only posts to your own accounts.
3. **Tokens**: in the app, open Instagram → API setup with Instagram login →
   Generate access tokens → Add account, and sign in with each Instagram account.
   If asked, accept the tester invite in Instagram (Settings → Website permissions/Apps and websites → Tester invites).
   It needs the permissions `instagram_business_basic` and `instagram_business_content_publish`.
   Copy each account's token.
4. **GitHub secrets**: in this repo, Settings → Secrets and variables → Actions → New repository secret:
   - `IG_TOKEN_CTSOCCERHUB`: the ctsoccerhub token
   - `IG_TOKEN_CLIPTHEORY67`: the clip.theory67 token
   - `GH_SECRETS_TOKEN`: a fine-grained GitHub token (github.com/settings/personal-access-tokens)
     with access to only this repo and the permission **Secrets: Read and write**. The weekly
     `ig-token-refresh` workflow uses it to renew the Instagram tokens, which last 60 days.

Tokens are never committed or printed. An account without a token is skipped.
