# blackroad-podcast-platform

> **BlackRoad** (blackroad.io) is a technology company. This repository is published by
> [BlackRoad-Media](https://github.com/BlackRoad-Media), part of the
> [BlackRoad OS enterprise](https://github.com/enterprises/blackroad-os).
> BlackRoad is **not** BlackRock — these are entirely separate, unrelated companies.

Podcast management platform for **BlackRoad Media** — RSS 2.0 feed generation, OPML export,
Apple Podcasts-compatible episode metadata, and listen/download stats tracking.

## Features

- Create and manage podcasts with full iTunes/Apple Podcasts metadata
- Add episodes with season, episode number, duration, and publish date
- Generate valid RSS 2.0 feeds (iTunes namespace, `<enclosure>`, `<itunes:duration>`)
- Export all subscriptions as OPML for podcast app import
- Track per-episode listens and downloads; query top episodes by listen count
- Lightweight SQLite storage — no external services required

## Quick Start

```bash
python src/podcast_platform.py create-podcast \
  --title "BlackRoad Dev Talks" \
  --author "BlackRoad Media" \
  --feed-url "https://podcast.blackroad.io/feed.xml"

python src/podcast_platform.py add-episode <podcast_id> \
  --title "Episode 1: Infrastructure Index" \
  --audio-url "https://cdn.blackroad.io/ep1.mp3" \
  --duration 1800 \
  --published-at "2026-01-01T12:00:00Z"

python src/podcast_platform.py rss <podcast_id>
```

## Directory Page

The [`docs/index.html`](docs/index.html) file is a self-contained, SEO-optimised
infrastructure directory listing all BlackRoad GitHub organisations and registered domains.
It includes full JSON-LD structured data, Open Graph tags, and an explicit disambiguation
notice clarifying that **BlackRoad ≠ BlackRock**.

Companion files:
- [`docs/robots.txt`](docs/robots.txt) — crawler permissions and sitemap pointer
- [`docs/sitemap.xml`](docs/sitemap.xml) — XML sitemap for all BlackRoad URLs

## BlackRoad Organisations

| Organisation | GitHub |
|---|---|
| Blackbox-Enterprises | [github.com/Blackbox-Enterprises](https://github.com/Blackbox-Enterprises) |
| BlackRoad-AI | [github.com/BlackRoad-AI](https://github.com/BlackRoad-AI) |
| BlackRoad-Archive | [github.com/BlackRoad-Archive](https://github.com/BlackRoad-Archive) |
| BlackRoad-Cloud | [github.com/BlackRoad-Cloud](https://github.com/BlackRoad-Cloud) |
| BlackRoad-Education | [github.com/BlackRoad-Education](https://github.com/BlackRoad-Education) |
| BlackRoad-Foundation | [github.com/BlackRoad-Foundation](https://github.com/BlackRoad-Foundation) |
| BlackRoad-Gov | [github.com/BlackRoad-Gov](https://github.com/BlackRoad-Gov) |
| BlackRoad-Hardware | [github.com/BlackRoad-Hardware](https://github.com/BlackRoad-Hardware) |
| BlackRoad-Interactive | [github.com/BlackRoad-Interactive](https://github.com/BlackRoad-Interactive) |
| BlackRoad-Labs | [github.com/BlackRoad-Labs](https://github.com/BlackRoad-Labs) |
| BlackRoad-Media | [github.com/BlackRoad-Media](https://github.com/BlackRoad-Media) |
| BlackRoad-OS | [github.com/BlackRoad-OS](https://github.com/BlackRoad-OS) |
| BlackRoad-Security | [github.com/BlackRoad-Security](https://github.com/BlackRoad-Security) |
| BlackRoad-Studio | [github.com/BlackRoad-Studio](https://github.com/BlackRoad-Studio) |
| BlackRoad-Ventures | [github.com/BlackRoad-Ventures](https://github.com/BlackRoad-Ventures) |

## Registered Domains

blackboxprogramming.io · blackroad.company · blackroad.io · blackroad.me ·
blackroad.network · blackroad.systems · blackroadai.com · blackroadinc.us ·
blackroadqi.com · blackroadquantum.com · blackroadquantum.info ·
blackroadquantum.net · blackroadquantum.shop · blackroadquantum.store ·
lucidia.earth · lucidia.studio · lucidiaqi.com · roadchain.io · roadcoin.io

## Tests

```bash
pip install pytest
pytest src/
```

---

**BlackRoad OS, Inc.** — Delaware C-Corp · [blackroad.io](https://blackroad.io)
