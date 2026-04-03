from xfetch.connectors.youtube import YouTubeConnector


class FakeResponse:
    def __init__(self, body: str, url: str, content_type: str = "text/html; charset=utf-8"):
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


def test_youtube_connector_extracts_metadata_from_html(monkeypatch):
    html = """
    <html>
      <head>
        <meta property=\"og:title\" content=\"YouTube Test Video\" />
        <meta name=\"author\" content=\"Video Creator\" />
        <meta property=\"og:description\" content=\"This is the video description.\" />
        <meta property=\"og:image\" content=\"https://i.ytimg.com/vi/abc123/maxresdefault.jpg\" />
      </head>
      <body></body>
    </html>
    """

    monkeypatch.setattr(
        "xfetch.connectors.youtube.urlopen",
        lambda request, timeout=15: FakeResponse(html, "https://www.youtube.com/watch?v=abc123"),
    )

    connector = YouTubeConnector()
    doc = connector.fetch("https://www.youtube.com/watch?v=abc123")

    assert doc.source_type == "youtube"
    assert doc.external_id == "abc123"
    assert doc.title == "YouTube Test Video"
    assert doc.author == "Video Creator"
    assert doc.author_handle == "video-creator"
    assert "This is the video description." in doc.text
    assert doc.assets == [{"url": "https://i.ytimg.com/vi/abc123/maxresdefault.jpg", "type": "image"}]
    assert doc.metadata["has_transcript"] is False


def test_youtube_connector_matches_youtube_urls_only():
    connector = YouTubeConnector()
    assert connector.can_handle("https://www.youtube.com/watch?v=abc123") is True
    assert connector.can_handle("https://youtu.be/abc123") is True
    assert connector.can_handle("https://example.com/watch?v=abc123") is False
