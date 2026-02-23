#!/usr/bin/env python3
"""BlackRoad Podcast Platform - RSS feed management and episode tracking."""

import argparse
import json
import sqlite3
import uuid
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DB_PATH = Path.home() / ".blackroad" / "podcast_platform.db"

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Podcast:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    author: str = ""
    description: str = ""
    feed_url: str = ""
    image_url: str = ""
    category: str = "Technology"
    language: str = "en"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class Episode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    podcast_id: str = ""
    title: str = ""
    description: str = ""
    audio_url: str = ""
    duration_secs: int = 0
    published_at: Optional[str] = None
    season: Optional[int] = None
    episode_num: Optional[int] = None
    explicit: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def _conn(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    _init_db(con)
    return con


def _init_db(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS podcasts (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            author      TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            feed_url    TEXT NOT NULL DEFAULT '',
            image_url   TEXT NOT NULL DEFAULT '',
            category    TEXT NOT NULL DEFAULT 'Technology',
            language    TEXT NOT NULL DEFAULT 'en',
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id           TEXT PRIMARY KEY,
            podcast_id   TEXT NOT NULL REFERENCES podcasts(id),
            title        TEXT NOT NULL,
            description  TEXT NOT NULL DEFAULT '',
            audio_url    TEXT NOT NULL DEFAULT '',
            duration_secs INTEGER DEFAULT 0,
            published_at TEXT,
            season       INTEGER,
            episode_num  INTEGER,
            explicit     INTEGER DEFAULT 0,
            created_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stats (
            id          TEXT PRIMARY KEY,
            episode_id  TEXT NOT NULL REFERENCES episodes(id),
            listens     INTEGER DEFAULT 0,
            downloads   INTEGER DEFAULT 0,
            recorded_at TEXT NOT NULL
        );
    """)
    con.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _secs_to_hhmmss(secs: int) -> str:
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _rfc2822(iso: Optional[str]) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except ValueError:
        return iso


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def create_podcast(podcast: Podcast, db: Path = DB_PATH) -> Podcast:
    with _conn(db) as con:
        con.execute(
            "INSERT OR REPLACE INTO podcasts VALUES (?,?,?,?,?,?,?,?,?)",
            (
                podcast.id, podcast.title, podcast.author,
                podcast.description, podcast.feed_url, podcast.image_url,
                podcast.category, podcast.language, podcast.created_at,
            ),
        )
    return podcast


def add_episode(episode: Episode, db: Path = DB_PATH) -> Episode:
    with _conn(db) as con:
        con.execute(
            "INSERT OR REPLACE INTO episodes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                episode.id, episode.podcast_id, episode.title,
                episode.description, episode.audio_url,
                episode.duration_secs, episode.published_at,
                episode.season, episode.episode_num,
                int(episode.explicit), episode.created_at,
            ),
        )
    return episode


def generate_rss_feed(podcast_id: str, db: Path = DB_PATH) -> str:
    """Build a valid Apple Podcasts-compatible RSS 2.0 feed."""
    with _conn(db) as con:
        pod = con.execute("SELECT * FROM podcasts WHERE id=?", (podcast_id,)).fetchone()
        if not pod:
            return f"<!-- podcast {podcast_id} not found -->"
        episodes = con.execute(
            """SELECT e.*, COALESCE(SUM(s.listens),0) listens
               FROM episodes e
               LEFT JOIN stats s ON s.episode_id = e.id
               WHERE e.podcast_id=? AND e.published_at IS NOT NULL
               GROUP BY e.id
               ORDER BY e.published_at DESC""",
            (podcast_id,),
        ).fetchall()

    root = ET.Element("rss", version="2.0")
    root.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")

    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = pod["title"]
    ET.SubElement(channel, "link").text = pod["feed_url"]
    ET.SubElement(channel, "description").text = pod["description"]
    ET.SubElement(channel, "language").text = pod["language"]
    ET.SubElement(channel, "itunes:author").text = pod["author"]
    ET.SubElement(channel, "itunes:category", text=pod["category"])
    if pod["image_url"]:
        img = ET.SubElement(channel, "itunes:image")
        img.set("href", pod["image_url"])

    for ep in episodes:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = ep["title"]
        ET.SubElement(item, "description").text = ep["description"]
        ET.SubElement(item, "pubDate").text = _rfc2822(ep["published_at"])
        ET.SubElement(item, "guid").text = ep["id"]
        ET.SubElement(item, "itunes:duration").text = _secs_to_hhmmss(ep["duration_secs"] or 0)
        if ep["episode_num"] is not None:
            ET.SubElement(item, "itunes:episode").text = str(ep["episode_num"])
        if ep["season"] is not None:
            ET.SubElement(item, "itunes:season").text = str(ep["season"])
        enc = ET.SubElement(item, "enclosure")
        enc.set("url", ep["audio_url"])
        enc.set("type", "audio/mpeg")
        enc.set("length", "0")

    return ET.tostring(root, encoding="unicode", xml_declaration=False)


def update_episode_stats(
    episode_id: str,
    listens: int,
    downloads: int,
    db: Path = DB_PATH,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with _conn(db) as con:
        con.execute(
            "INSERT INTO stats VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), episode_id, listens, downloads, now),
        )
    return {"ok": True, "episode_id": episode_id, "recorded_at": now}


def get_top_episodes(
    podcast_id: str,
    limit: int = 10,
    db: Path = DB_PATH,
) -> List[dict]:
    with _conn(db) as con:
        rows = con.execute(
            """SELECT e.id, e.title, e.episode_num, e.season,
                      COALESCE(SUM(s.listens),0)   total_listens,
                      COALESCE(SUM(s.downloads),0) total_downloads
               FROM episodes e
               LEFT JOIN stats s ON s.episode_id = e.id
               WHERE e.podcast_id=?
               GROUP BY e.id
               ORDER BY total_listens DESC
               LIMIT ?""",
            (podcast_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def export_opml(db: Path = DB_PATH) -> str:
    """Export all podcasts as an OPML file (for podcast app import)."""
    with _conn(db) as con:
        rows = con.execute("SELECT * FROM podcasts ORDER BY title").fetchall()

    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "title").text = "BlackRoad Podcast Subscriptions"
    body = ET.SubElement(root, "body")

    for row in rows:
        outline = ET.SubElement(body, "outline")
        outline.set("type", "rss")
        outline.set("text", row["title"])
        outline.set("title", row["title"])
        outline.set("xmlUrl", row["feed_url"])
        outline.set("description", row["description"])

    return ET.tostring(root, encoding="unicode", xml_declaration=False)


def get_podcast_stats(podcast_id: str, db: Path = DB_PATH) -> dict:
    with _conn(db) as con:
        ep_count = con.execute(
            "SELECT COUNT(*) n FROM episodes WHERE podcast_id=?", (podcast_id,)
        ).fetchone()["n"]
        totals = con.execute(
            """SELECT COALESCE(SUM(s.listens),0)   total_listens,
                      COALESCE(SUM(s.downloads),0) total_downloads
               FROM episodes e
               LEFT JOIN stats s ON s.episode_id = e.id
               WHERE e.podcast_id=?""",
            (podcast_id,),
        ).fetchone()
    return {
        "podcast_id": podcast_id,
        "episode_count": ep_count,
        "total_listens": totals["total_listens"],
        "total_downloads": totals["total_downloads"],
    }


def list_podcasts(db: Path = DB_PATH) -> List[dict]:
    with _conn(db) as con:
        rows = con.execute("SELECT * FROM podcasts ORDER BY title").fetchall()
    return [dict(r) for r in rows]


def list_episodes(podcast_id: str, db: Path = DB_PATH) -> List[dict]:
    with _conn(db) as con:
        rows = con.execute(
            "SELECT * FROM episodes WHERE podcast_id=? ORDER BY published_at DESC",
            (podcast_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="BlackRoad Podcast Platform")
    sub = p.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("create-podcast", help="Create a podcast")
    cp.add_argument("--title", required=True)
    cp.add_argument("--author", default="")
    cp.add_argument("--description", default="")
    cp.add_argument("--feed-url", default="")
    cp.add_argument("--image-url", default="")
    cp.add_argument("--category", default="Technology")

    ae = sub.add_parser("add-episode", help="Add an episode")
    ae.add_argument("podcast_id")
    ae.add_argument("--title", required=True)
    ae.add_argument("--description", default="")
    ae.add_argument("--audio-url", default="")
    ae.add_argument("--duration", type=int, default=0)
    ae.add_argument("--published-at", default=None)
    ae.add_argument("--season", type=int, default=None)
    ae.add_argument("--episode-num", type=int, default=None)

    rss = sub.add_parser("rss", help="Generate RSS feed")
    rss.add_argument("podcast_id")

    opml = sub.add_parser("opml", help="Export OPML")

    top = sub.add_parser("top-episodes", help="Get top episodes")
    top.add_argument("podcast_id")
    top.add_argument("--limit", type=int, default=10)

    us = sub.add_parser("update-stats", help="Update episode stats")
    us.add_argument("episode_id")
    us.add_argument("--listens", type=int, default=0)
    us.add_argument("--downloads", type=int, default=0)

    lp = sub.add_parser("list-podcasts", help="List all podcasts")
    le = sub.add_parser("list-episodes", help="List episodes")
    le.add_argument("podcast_id")

    stats = sub.add_parser("stats", help="Get podcast stats")
    stats.add_argument("podcast_id")

    return p


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "create-podcast":
        pod = Podcast(
            title=args.title,
            author=args.author,
            description=args.description,
            feed_url=args.feed_url,
            image_url=args.image_url,
            category=args.category,
        )
        print(json.dumps(asdict(create_podcast(pod)), indent=2))

    elif args.cmd == "add-episode":
        ep = Episode(
            podcast_id=args.podcast_id,
            title=args.title,
            description=args.description,
            audio_url=args.audio_url,
            duration_secs=args.duration,
            published_at=args.published_at,
            season=args.season,
            episode_num=args.episode_num,
        )
        print(json.dumps(asdict(add_episode(ep)), indent=2))

    elif args.cmd == "rss":
        print(generate_rss_feed(args.podcast_id))

    elif args.cmd == "opml":
        print(export_opml())

    elif args.cmd == "top-episodes":
        print(json.dumps(get_top_episodes(args.podcast_id, args.limit), indent=2))

    elif args.cmd == "update-stats":
        print(json.dumps(update_episode_stats(args.episode_id, args.listens, args.downloads), indent=2))

    elif args.cmd == "list-podcasts":
        print(json.dumps(list_podcasts(), indent=2))

    elif args.cmd == "list-episodes":
        print(json.dumps(list_episodes(args.podcast_id), indent=2))

    elif args.cmd == "stats":
        print(json.dumps(get_podcast_stats(args.podcast_id), indent=2))


if __name__ == "__main__":
    main()
