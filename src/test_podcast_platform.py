"""Tests for podcast_platform."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from podcast_platform import (
    Episode,
    Podcast,
    add_episode,
    create_podcast,
    export_opml,
    generate_rss_feed,
    get_podcast_stats,
    get_top_episodes,
    list_episodes,
    list_podcasts,
    update_episode_stats,
)


@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def sample_podcast(tmp_db):
    pod = Podcast(
        title="BlackRoad Dev Talks",
        author="Alexa",
        description="Tech conversations",
        feed_url="https://podcast.blackroad.ai/feed.xml",
    )
    return create_podcast(pod, db=tmp_db), tmp_db


def test_create_podcast(sample_podcast):
    pod, db = sample_podcast
    pods = list_podcasts(db=db)
    assert any(p["id"] == pod.id for p in pods)


def test_add_episode(sample_podcast):
    pod, db = sample_podcast
    ep = Episode(
        podcast_id=pod.id,
        title="Episode 1: Getting Started",
        duration_secs=1800,
        episode_num=1,
        season=1,
        published_at="2024-01-01T12:00:00Z",
        audio_url="https://cdn.blackroad.ai/ep1.mp3",
    )
    add_episode(ep, db=db)
    episodes = list_episodes(pod.id, db=db)
    assert any(e["id"] == ep.id for e in episodes)


def test_generate_rss_feed(sample_podcast):
    pod, db = sample_podcast
    ep = Episode(
        podcast_id=pod.id,
        title="RSS Test Episode",
        duration_secs=3600,
        published_at="2024-06-01T10:00:00Z",
        audio_url="https://cdn.blackroad.ai/ep.mp3",
    )
    add_episode(ep, db=db)
    rss = generate_rss_feed(pod.id, db=db)
    assert "<rss" in rss
    assert "BlackRoad Dev Talks" in rss
    assert "RSS Test Episode" in rss


def test_update_and_get_stats(sample_podcast):
    pod, db = sample_podcast
    ep = Episode(
        podcast_id=pod.id,
        title="Stats Episode",
        duration_secs=600,
        published_at="2024-01-15T10:00:00Z",
    )
    add_episode(ep, db=db)
    update_episode_stats(ep.id, listens=1000, downloads=500, db=db)
    top = get_top_episodes(pod.id, limit=5, db=db)
    assert any(t["id"] == ep.id for t in top)
    assert top[0]["total_listens"] >= 1000


def test_export_opml(sample_podcast):
    pod, db = sample_podcast
    opml = export_opml(db=db)
    assert "<opml" in opml
    assert "BlackRoad Dev Talks" in opml


def test_podcast_stats(sample_podcast):
    pod, db = sample_podcast
    for i in range(3):
        ep = Episode(podcast_id=pod.id, title=f"Ep {i}", published_at="2024-01-01T00:00:00Z")
        add_episode(ep, db=db)
        update_episode_stats(ep.id, listens=100 * (i + 1), downloads=50, db=db)
    stats = get_podcast_stats(pod.id, db=db)
    assert stats["episode_count"] == 3
    assert stats["total_listens"] == 600


def test_secs_to_hhmmss():
    from podcast_platform import _secs_to_hhmmss
    assert _secs_to_hhmmss(3661) == "01:01:01"
    assert _secs_to_hhmmss(0) == "00:00:00"
