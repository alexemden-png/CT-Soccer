# CT Soccer Hub daily videos

How the daily task makes new 20-second vertical videos for ctsoccerhub.com and schedules them in Buffer. Every video uses the same template, so they all look alike: a 3D blocky stadium opening with a question, a white "spotlight" card whose fact rows appear as the narrator says them, an optional big number, and the CT Soccer Hub end card.

## Setup (once per session)

```bash
bash pipeline/setup.sh   # voice model (~350 MB from GitHub), kokoro-onnx, three.js; checks Playwright, ffmpeg, Inter font
```

## Make one video

1. `mkdir -p jobs/<slug>` and write `jobs/<slug>/spec.json` (format below). `jobs/` is git-ignored.
2. `bash pipeline/make_video.sh jobs/<slug>` (about 4 minutes).
3. Look at `jobs/<slug>/<slug>_sheet.jpg`, six frames from the video. All text must sit inside its card or plate, nothing cut off or overlapping. If something doesn't fit, shorten that text and run it again.

## spec.json

```json
{
  "slug": "club-west-hartford-sc",
  "hook": "Playing soccer in [West Hartford]?",
  "head": "Club [spotlight]",
  "hookShot": "save",
  "ctaShot": "goal",
  "card": {
    "kicker": "Youth club · CJSA",
    "title": "West Hartford SC",
    "subtitle": "West Hartford · Hartford County",
    "color": "#1d4fd8",
    "rows": [
      {"icon": "calendar", "label": "Founded", "value": "1969", "at": [2, "founded"]},
      {"icon": "people", "label": "Age groups", "value": "U6 to U18", "at": [2, "under six"]},
      {"icon": "ball", "label": "Teams", "value": "Rec leagues + travel teams", "at": [2, "rec leagues"]},
      {"icon": "pin", "label": "Home field", "value": "Norfeldt / Charter Oak Park", "at": [2, "norfeldt"]}
    ]
  },
  "stat": {"n": "13", "label": "age groups,\n[no gaps]", "at": [3, "thirteen"]},
  "note": "Age groups are updated by hand, so check with the club",
  "cta": "See the full profile",
  "narration": [
    "Playing soccer in West Hartford?",
    "West Hartford Soccer Club was founded in 1969, with teams from under six to under eighteen, rec leagues and travel teams, at Norfeldt and Charter Oak Park.",
    "That's thirteen age groups, with no gaps.",
    "See the full profile at C T Soccer Hub dot com."
  ]
}
```

| Field | Rule |
|---|---|
| `slug` | lowercase-with-dashes, starting with the series: `club-`, `coach-`, `guide-`, `tournament-`, `course-`, `town-`. It becomes the file name, and a topic counts as done once `videos/**/<slug>.mp4` exists. |
| `hook` | A question of 7 words or fewer. `[brackets]` turn yellow. |
| `head` | 2-3 words above the card: `Club [spotlight]`, `Coach [spotlight]`, `Tournament [guide]`, `Coaching [course]`, `Soccer in [Glastonbury]`, `Parent [guide]`. |
| `card.kicker` | Short line above the title, e.g. `Youth club · CJSA`. |
| `card.title` | The name, 28 characters or fewer. |
| `card.subtitle` | e.g. town · county, 40 characters or fewer. Optional. |
| `card.color` | One of `#1d4fd8` blue, `#2fa84f` green, `#e5484d` red, `#c48a00` gold, `#7c3aed` purple, `#0f9fb5` teal. Make videos posted next to each other differ. |
| `card.rows` | 2-4 rows. `icon`: calendar, people, ball, pin, trophy, clipboard, star, clock, link, whistle, shield, chart, dollar. `label` 18 characters or fewer, `value` 30 or fewer. `at`: `[line, "words exactly as in that narration line"]`, so the row appears as it is said. |
| `stat` | Optional big number: `n` is a short number or text (`"13"`, `"U6-U18"`); whole numbers count up. `label` 3 short lines or fewer. `at` as above, usually line 3. |
| `note` | Optional caveat pill, 60 characters or fewer. |
| `cta` | 4 words or fewer: `See the full profile`, `Find your course`, `Plan your season`, `Read the full story`. |
| `hookShot` / `ctaShot` | `save` or `trophy` / `goal` or `trophy`. Vary them. |
| `narration` | Exactly 4 lines in the af_heart voice: (1) the hook, 8 words or fewer; (2) the facts in row order, 24 words or fewer; (3) one extra point, 12 words or fewer; (4) `<cta> at C T Soccer Hub dot com.` Write for the ear: `C T`, not `CT`; `under nine`, not `U9`; `dot com`. `make_voice.py` prints the speech total: keep it 13-17 seconds so the video lands at 18-22 seconds. |

## Facts

- Use only facts printed on ctsoccerhub.com pages fetched in this run. Never guess or fill a gap from memory.
- Neutral wording: no "best", no rankings, no claims about quality, safety, coaching or results that the page doesn't make.
- If a page says something isn't on file, leave it out.
- People: only what the site's own published spotlight says about them.
- Dates: only upcoming or ongoing ones; never present a past event as upcoming.

## Topics

A topic is done when `videos/**/<slug>.mp4` exists in this repo. Mix series within a day.

1. **Club spotlights** (`club-<page slug>`): the 37 `/clubs/<slug>.html` pages listed in https://ctsoccerhub.com/sitemap.xml.
2. **News** (`/news/<slug>.html` in the sitemap): coach spotlights (`coach-<name>`), guides (`guide-<slug>`), season reviews. Skip a news spotlight of a club that already has a `club-` video.
3. **Tournaments** (`tournament-<name>`): one per video, from https://ctsoccerhub.com/tournaments.html.
4. **Coaching courses** (`course-<name>`): upcoming ones from https://ctsoccerhub.com/coaching-clinics.html.
5. **Towns** (`town-<town>`): clubs in one town, from https://ctsoccerhub.com/clubs-by-town.html, if the page shows them.

Already covered, so not repeated: the site overview promo and the 10 feature videos in `videos/ctsh_*.mp4` (find a club, clubs by town, club profiles, compare clubs, standings, standings predictor, tournaments & events, coaching courses, Soccer Assistant, news & season review).

## Posting

- **Hosting**: commit each video as `videos/<posting date YYYY-MM-DD>/<slug>.mp4`, push to `main`, and use `https://raw.githubusercontent.com/alexemden-png/CT-Soccer/main/videos/<date>/<slug>.mp4`. Check that it returns HTTP 200 with the right size before posting.
- **Buffer**: organization "My organization". Instagram `ctsoccerhub` = `6aea45e6e29c69a171509efa` (type reel, shouldShareToFeed true). YouTube `CT Soccer` = `6ae7e06fe29c69a17130c4f7` (title ending ` | CT Soccer Hub`, 100 characters or fewer; categoryId `17`; madeForKids false; privacy public). Mode `customScheduled`, schedulingType `automatic`.
- **Slots**: 9:00 AM, 1:00 PM and 7:00 PM America/New_York, at least 3 posts a day on each channel. Build `dueAt` with Python `zoneinfo` so the UTC offset is right on both sides of daylight saving time.
- **Buffer free plan**: at most 10 scheduled posts per channel, so schedule no more than two days ahead.
- **Instagram caption**:

  ```
  <question or hook with one emoji>

  <two short sentences of facts from the page>

  <CTA> at ctsoccerhub.com (link in bio)

  #CTsoccer #ConnecticutSoccer #youthsoccer #<topic tag> #ctsoccerhub
  ```

  The YouTube description is the same text, with `at https://ctsoccerhub.com` instead of `at ctsoccerhub.com (link in bio)`. Five hashtags at most; the topic tag is something like `#WestHartford` or `#soccercoach`.
