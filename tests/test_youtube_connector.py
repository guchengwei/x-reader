import json

from xfetch.connectors.youtube import YouTubeConnector


class FakeResponse:
    def __init__(self, body: str, url: str, content_type: str = "text/html; charset=utf-8"):
        self._body = body.encode("utf-8")
        self._url = url
        self.headers = {"Content-Type": content_type}
    def read(self): return self._body
    def geturl(self): return self._url
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False


def _video_html(player_response: dict | None = None) -> str:
    player_script = ""
    if player_response is not None:
        player_script = f"<script>var ytInitialPlayerResponse = {json.dumps(player_response)};</script>"
    return f"""
    <html><head>
      <meta property="og:title" content="YouTube Test Video" />
      <meta name="author" content="Video Creator" />
      <meta property="og:description" content="This is the video description." />
      <meta property="og:image" content="https://i.ytimg.com/vi/abc123/maxresdefault.jpg" />
    </head><body>{player_script}</body></html>
    """


def test_youtube_connector_extracts_metadata_from_html(monkeypatch):
    html = _video_html()
    monkeypatch.setattr("xfetch.connectors.youtube.urlopen", lambda request, timeout=15: FakeResponse(html, "https://www.youtube.com/watch?v=abc123"))
    doc = YouTubeConnector().fetch("https://www.youtube.com/watch?v=abc123")
    assert doc.source_type == "youtube"
    assert doc.external_id == "abc123"
    assert doc.title == "YouTube Test Video"
    assert doc.author == "Video Creator"
    assert doc.author_handle == "video-creator"
    assert "This is the video description." in doc.text
    assert doc.assets == [{"url": "https://i.ytimg.com/vi/abc123/maxresdefault.jpg", "type": "image"}]
    assert doc.metadata["has_transcript"] is False
    assert doc.metadata["transcript_available"] is False
    assert doc.capture_status == "metadata_only"
    assert doc.content_kinds == ["metadata", "thumbnail"]


def test_youtube_connector_captures_preferred_manual_transcript(monkeypatch):
    player_response = {
        "captions": {
            "playerCaptionsTracklistRenderer": {
                "captionTracks": [
                    {
                        "baseUrl": "https://www.youtube.com/api/timedtext?v=abc123&lang=ja&kind=asr",
                        "languageCode": "ja",
                        "kind": "asr",
                    },
                    {
                        "baseUrl": "https://www.youtube.com/api/timedtext?v=abc123&lang=en",
                        "languageCode": "en",
                        "name": {"simpleText": "English"},
                    },
                ]
            }
        }
    }
    html = _video_html(player_response)
    transcript_payload = {
        "events": [
            {"segs": [{"utf8": "Hello "}, {"utf8": "world"}]},
            {"segs": [{"utf8": "Second line"}]},
            {"tStartMs": 2000},
        ]
    }
    calls = []

    def fake_urlopen(request, timeout=15):
        calls.append(request.full_url)
        if "api/timedtext" in request.full_url:
            return FakeResponse(json.dumps(transcript_payload), request.full_url, "application/json")
        return FakeResponse(html, "https://www.youtube.com/watch?v=abc123")

    monkeypatch.setattr("xfetch.connectors.youtube.urlopen", fake_urlopen)
    doc = YouTubeConnector().fetch("https://www.youtube.com/watch?v=abc123")

    assert doc.capture_status == "partial"
    assert doc.content_kinds == ["text", "transcript", "metadata", "thumbnail"]
    assert doc.metadata["has_transcript"] is True
    assert doc.metadata["transcript_available"] is True
    assert doc.metadata["transcript_language"] == "en"
    assert doc.metadata["transcript_kind"] == "manual"
    assert doc.metadata["unpreserved_media"] == ["video"]
    assert doc.language == "en"
    assert "Hello world\nSecond line" in doc.text
    assert "## Transcript" in doc.markdown
    assert any("lang=en" in call and "fmt=json3" in call for call in calls)
    assert not any("lang=ja" in call and "api/timedtext" in call for call in calls)


def test_youtube_connector_falls_back_when_caption_fetch_fails(monkeypatch):
    player_response = {
        "captions": {
            "playerCaptionsTracklistRenderer": {
                "captionTracks": [
                    {
                        "baseUrl": "https://www.youtube.com/api/timedtext?v=abc123&lang=en&exp=xpe",
                        "languageCode": "en",
                        "kind": "asr",
                    }
                ]
            }
        }
    }
    html = _video_html(player_response)

    def fake_urlopen(request, timeout=15):
        if "api/timedtext" in request.full_url:
            return FakeResponse("", request.full_url, "application/json")
        return FakeResponse(html, "https://www.youtube.com/watch?v=abc123")

    monkeypatch.setattr("xfetch.connectors.youtube.urlopen", fake_urlopen)
    doc = YouTubeConnector().fetch("https://www.youtube.com/watch?v=abc123")

    assert doc.capture_status == "metadata_only"
    assert doc.metadata["has_transcript"] is False
    assert doc.metadata["transcript_available"] is True
    assert doc.metadata["transcript_language"] == "en"
    assert doc.metadata["transcript_kind"] == "auto"
    assert doc.metadata["transcript_capture_error"] == "empty caption response"
    assert doc.text == "This is the video description."
    assert "## Transcript" not in doc.markdown


def test_youtube_connector_matches_youtube_urls_only():
    connector = YouTubeConnector()
    assert connector.can_handle("https://www.youtube.com/watch?v=abc123") is True
    assert connector.can_handle("https://youtu.be/abc123") is True
    assert connector.can_handle("https://example.com/watch?v=abc123") is False
