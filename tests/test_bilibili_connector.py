from xfetch.connectors.bilibili import BilibiliConnector


class FakeResponse:
    def __init__(self, body: str, url: str, content_type: str = "application/json"):
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


def test_bilibili_connector_extracts_metadata_from_api(monkeypatch):
    payload = """
    {
      "code": 0,
      "data": {
        "title": "Bilibili Test Video",
        "desc": "This is a bilibili description.",
        "owner": {"name": "UP Author"},
        "pic": "https://i0.hdslb.com/test-cover.jpg",
        "duration": 321,
        "stat": {"view": 12345}
      }
    }
    """

    monkeypatch.setattr(
        "xfetch.connectors.bilibili.urlopen",
        lambda request, timeout=10: FakeResponse(payload, "https://api.bilibili.com/x/web-interface/view?bvid=BV1xx411c7mD"),
    )

    connector = BilibiliConnector()
    doc = connector.fetch("https://www.bilibili.com/video/BV1xx411c7mD")

    assert doc.source_type == "bilibili"
    assert doc.external_id == "BV1xx411c7mD"
    assert doc.title == "Bilibili Test Video"
    assert doc.author == "UP Author"
    assert doc.author_handle == "up-author"
    assert "This is a bilibili description." in doc.text
    assert doc.assets == [{"url": "https://i0.hdslb.com/test-cover.jpg", "type": "image"}]
    assert doc.metadata["view_count"] == 12345
    assert doc.metadata["duration"] == 321


def test_bilibili_connector_matches_bilibili_urls_only():
    connector = BilibiliConnector()
    assert connector.can_handle("https://www.bilibili.com/video/BV1xx411c7mD") is True
    assert connector.can_handle("https://b23.tv/BV1xx411c7mD") is True
    assert connector.can_handle("https://example.com/video/BV1xx411c7mD") is False
