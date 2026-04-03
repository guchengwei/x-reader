from xfetch.connectors.wechat import WeChatConnector


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


def test_wechat_connector_extracts_article_fields(monkeypatch):
    html = """
    <html>
      <head>
        <meta property=\"og:title\" content=\"WeChat Article Title\" />
        <meta name=\"author\" content=\"Alice Writer\" />
        <script>
          var nickname = \"AI Daily\";
          var ct = \"1711958400\";
        </script>
      </head>
      <body>
        <div class=\"rich_media_content \" id=\"js_content\">
          <p>First paragraph.</p>
          <p>Second paragraph.</p>
          <img data-src=\"https://mmbiz.qpic.cn/image-1.jpg\" />
        </div>
      </body>
    </html>
    """

    monkeypatch.setattr(
        "xfetch.connectors.wechat.urlopen",
        lambda request, timeout=15: FakeResponse(html, "https://mp.weixin.qq.com/s/example"),
    )

    connector = WeChatConnector()
    doc = connector.fetch("https://mp.weixin.qq.com/s/example")

    assert doc.source_type == "wechat"
    assert doc.title == "WeChat Article Title"
    assert doc.author == "Alice Writer"
    assert doc.author_handle == "AI Daily"
    assert doc.created_at == "2024-04-01T08:00:00Z"
    assert "First paragraph." in doc.text
    assert "Second paragraph." in doc.text
    assert doc.assets == [{"url": "https://mmbiz.qpic.cn/image-1.jpg", "type": "image"}]
    assert doc.metadata["account"] == "AI Daily"


def test_wechat_connector_matches_mp_weixin_urls_only():
    connector = WeChatConnector()
    assert connector.can_handle("https://mp.weixin.qq.com/s/example") is True
    assert connector.can_handle("https://example.com/s/example") is False
