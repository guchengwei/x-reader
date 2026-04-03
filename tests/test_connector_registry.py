from xfetch.connectors.registry import connector_registry, pick_connector
from xfetch.connectors.rss import RSSConnector
from xfetch.connectors.web import WebConnector
from xfetch.connectors.x import XConnector


def test_connector_registry_starts_with_x_then_rss_then_web():
    registry = connector_registry()
    assert [type(connector) for connector in registry[:3]] == [XConnector, RSSConnector, WebConnector]


def test_pick_connector_returns_x_connector_for_x_urls():
    connector = pick_connector("https://x.com/alice/status/123")
    assert isinstance(connector, XConnector)


def test_pick_connector_returns_rss_connector_for_feed_urls():
    connector = pick_connector("https://example.com/feed.xml")
    assert isinstance(connector, RSSConnector)


def test_pick_connector_returns_web_connector_for_generic_http_urls():
    connector = pick_connector("https://example.com/posts/123")
    assert isinstance(connector, WebConnector)


def test_pick_connector_returns_none_for_unsupported_schemes():
    assert pick_connector("mailto:alice@example.com") is None
