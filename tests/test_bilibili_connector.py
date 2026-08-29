import json

from xfetch.connectors.bilibili import BilibiliConnector


class FakeResponse:
    def __init__(self, body: str, url: str, content_type: str = "application/json"):
        self._body = body.encode("utf-8")
        self._url = url
        self.headers = {"Content-Type": content_type}
    def read(self): return self._body
    def geturl(self): return self._url
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False


def test_bilibili_connector_extracts_metadata_from_api(monkeypatch):
    payload = """
    {"code":0,"data":{"title":"Bilibili Test Video","desc":"This is a bilibili description.","owner":{"name":"UP Author"},"pic":"https://i0.hdslb.com/test-cover.jpg","duration":321,"stat":{"view":12345}}}
    """
    monkeypatch.setattr("xfetch.connectors.bilibili.urlopen", lambda request, timeout=10: FakeResponse(payload, request.full_url))
    doc = BilibiliConnector().fetch("https://www.bilibili.com/video/BV1xx411c7mD")
    assert doc.source_type == "bilibili"
    assert doc.external_id == "BV1xx411c7mD"
    assert doc.title == "Bilibili Test Video"
    assert doc.author == "UP Author"
    assert doc.author_handle == "up-author"
    assert "This is a bilibili description." in doc.text
    assert doc.assets == [{"url": "https://i0.hdslb.com/test-cover.jpg", "type": "image"}]
    assert doc.metadata["view_count"] == 12345
    assert doc.metadata["duration"] == 321
    assert doc.metadata["has_transcript"] is False
    assert doc.metadata["transcript_available"] is False
    assert doc.capture_status == "metadata_only"


def test_bilibili_connector_captures_public_subtitle(monkeypatch):
    view_payload = {
        "code": 0,
        "data": {
            "title": "Bilibili Test Video",
            "desc": "Video description.",
            "owner": {"name": "UP Author"},
            "pic": "https://i0.hdslb.com/test-cover.jpg",
            "cid": 987654,
            "duration": 321,
            "stat": {"view": 12345},
        },
    }
    player_payload = {
        "code": 0,
        "data": {
            "subtitle": {
                "subtitles": [
                    {
                        "lan": "zh-CN",
                        "lan_doc": "中文（简体）",
                        "subtitle_url": "//i0.hdslb.com/bfs/subtitle/test.json",
                    }
                ]
            }
        },
    }
    subtitle_payload = {
        "body": [
            {"from": 0.0, "to": 1.0, "content": "第一句"},
            {"from": 1.0, "to": 2.0, "content": "第二句"},
        ]
    }
    calls = []

    def fake_urlopen(request, timeout=10):
        calls.append(request.full_url)
        if "/x/web-interface/view" in request.full_url:
            return FakeResponse(json.dumps(view_payload), request.full_url)
        if "/x/player/v2" in request.full_url:
            return FakeResponse(json.dumps(player_payload), request.full_url)
        if "/bfs/subtitle/" in request.full_url:
            return FakeResponse(json.dumps(subtitle_payload), request.full_url)
        raise AssertionError(request.full_url)

    monkeypatch.setattr("xfetch.connectors.bilibili.urlopen", fake_urlopen)
    doc = BilibiliConnector().fetch("https://www.bilibili.com/video/BV1xx411c7mD")

    assert doc.capture_status == "partial"
    assert doc.content_kinds == ["text", "transcript", "metadata", "thumbnail"]
    assert doc.metadata["has_transcript"] is True
    assert doc.metadata["transcript_available"] is True
    assert doc.metadata["transcript_language"] == "zh-CN"
    assert doc.metadata["transcript_language_name"] == "中文（简体）"
    assert doc.metadata["cid"] == 987654
    assert doc.metadata["unpreserved_media"] == ["video"]
    assert doc.language == "zh-CN"
    assert "第一句\n第二句" in doc.text
    assert "## Transcript" in doc.markdown
    assert any("/x/player/v2" in call and "cid=987654" in call for call in calls)
    assert any(call.startswith("https://i0.hdslb.com/bfs/subtitle/") for call in calls)


def test_bilibili_connector_records_login_required_subtitles(monkeypatch):
    view_payload = {
        "code": 0,
        "data": {
            "title": "Bilibili Test Video",
            "desc": "Video description.",
            "owner": {"name": "UP Author"},
            "cid": 987654,
        },
    }
    player_payload = {
        "code": 0,
        "data": {
            "subtitle": {
                "need_login_subtitle": True,
                "subtitles": [],
            }
        },
    }

    def fake_urlopen(request, timeout=10):
        if "/x/web-interface/view" in request.full_url:
            return FakeResponse(json.dumps(view_payload), request.full_url)
        if "/x/player/v2" in request.full_url:
            return FakeResponse(json.dumps(player_payload), request.full_url)
        raise AssertionError(request.full_url)

    monkeypatch.setattr("xfetch.connectors.bilibili.urlopen", fake_urlopen)
    doc = BilibiliConnector().fetch("https://www.bilibili.com/video/BV1xx411c7mD")

    assert doc.capture_status == "metadata_only"
    assert doc.metadata["has_transcript"] is False
    assert doc.metadata["transcript_available"] is False
    assert doc.metadata["transcript_requires_login"] is True
    assert "transcript_capture_error" not in doc.metadata


def test_bilibili_connector_matches_bilibili_urls_only():
    connector = BilibiliConnector()
    assert connector.can_handle("https://www.bilibili.com/video/BV1xx411c7mD") is True
    assert connector.can_handle("https://b23.tv/BV1xx411c7mD") is True
    assert connector.can_handle("https://example.com/video/BV1xx411c7mD") is False
