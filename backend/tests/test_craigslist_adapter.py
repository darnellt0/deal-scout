import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.adapters.craigslist_rss import fetch_listings
from app.config import get_settings

SAMPLE_RSS = """
<rss xmlns:georss=\"http://www.georss.org/georss\">\n  <channel>\n    <item>\n      <title>Free Couch in Sunnyvale</title>\n      <link>https://example.invalid/couch</link>\n      <description> - needs pickup today</description>\n      <pubDate>Mon, 20 Oct 2025 10:00:00 +0000</pubDate>\n      <georss:point>37.3688 -122.0363</georss:point>\n    </item>\n  </channel>\n</rss>
"""


class DummyResponse:
    def __init__(self, url: str):
        self.url = url
        self.text = SAMPLE_RSS

    def raise_for_status(self):
        return None


class DummyClient:
    last_url = None

    def __init__(self, *_, **__):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url):
        DummyClient.last_url = url
        return DummyResponse(url)


def test_fetch_listings_builds_regional_urls(monkeypatch):
    settings = get_settings()
    settings.cl_region = "sfbay"
    settings.demo_mode = False
    monkeypatch.setattr("app.adapters.craigslist_rss.httpx.Client", DummyClient)
    results = fetch_listings(["couch"])
    assert results
    assert DummyClient.last_url.startswith("https://sfbay.craigslist.org")
    first = results[0]
    assert first["title"].startswith("Free Couch")
    assert first["coords"] == (37.3688, -122.0363)
