from xfetch.connectors.web import WebConnector


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


def test_web_connector_extracts_basic_document_fields(monkeypatch):
    html = """
    <html>
      <head>
        <title>Example Article</title>
        <meta name=\"author\" content=\"Alice Example\">
      </head>
      <body>
        <main>
          <h1>Example Article</h1>
          <p>Hello world.</p>
          <p>This is a test article.</p>
        </main>
      </body>
    </html>
    """

    monkeypatch.setattr(
        "xfetch.connectors.web.urlopen",
        lambda request, timeout=10: FakeResponse(html, "https://example.com/posts/123"),
    )

    connector = WebConnector()
    doc = connector.fetch("https://example.com/posts/123")

    assert doc.source_type == "web"
    assert doc.canonical_url == "https://example.com/posts/123"
    assert doc.title == "Example Article"
    assert doc.author == "Alice Example"
    assert doc.author_handle == "example.com"
    assert "Hello world." in doc.text
    assert doc.metadata["content_type"] == "text/html; charset=utf-8"
    assert doc.lineage["connector"] == "web"


def test_web_connector_matches_generic_http_urls_but_not_x_or_rss():
    connector = WebConnector()
    assert connector.can_handle("https://example.com/posts/123") is True
    assert connector.can_handle("https://x.com/alice/status/123") is False
    assert connector.can_handle("https://example.com/feed.xml") is False
