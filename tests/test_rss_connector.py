from xfetch.connectors.rss import RSSConnector


class FakeResponse:
    def __init__(self, body: str, url: str, content_type: str = "application/rss+xml"):
        self._body = body.encode("utf-8")
        self._url = url
        self.headers = {"Content-Type": content_type}

    def read(self):
        return self._body

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_rss_connector_normalizes_latest_entry(monkeypatch):
    rss_xml = """
    <rss version=\"2.0\">
      <channel>
        <title>Example Feed</title>
        <item>
          <title>First post</title>
          <link>https://example.com/posts/1</link>
          <guid>post-1</guid>
          <author>alice@example.com (Alice Example)</author>
          <pubDate>Tue, 01 Apr 2026 12:00:00 GMT</pubDate>
          <description>Hello from RSS.</description>
        </item>
      </channel>
    </rss>
    """

    monkeypatch.setattr(
        "xfetch.connectors.rss.urlopen",
        lambda request, timeout=10: FakeResponse(rss_xml, "https://example.com/feed.xml"),
    )

    connector = RSSConnector()
    doc = connector.fetch("https://example.com/feed.xml")

    assert doc.source_type == "rss"
    assert doc.source_url == "https://example.com/feed.xml"
    assert doc.canonical_url == "https://example.com/posts/1"
    assert doc.title == "First post"
    assert doc.author == "Alice Example"
    assert doc.author_handle == "example.com"
    assert doc.created_at == "2026-04-01T12:00:00Z"
    assert "Hello from RSS." in doc.text
    assert doc.metadata["feed_title"] == "Example Feed"
    assert doc.lineage["connector"] == "rss"


def test_rss_connector_matches_feed_urls_only():
    connector = RSSConnector()
    assert connector.can_handle("https://example.com/feed.xml") is True
    assert connector.can_handle("https://example.com/feed") is True
    assert connector.can_handle("https://example.com/posts/1") is False
