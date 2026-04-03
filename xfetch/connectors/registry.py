from __future__ import annotations

from xfetch.connectors.rss import RSSConnector
from xfetch.connectors.web import WebConnector
from xfetch.connectors.x import XConnector


def connector_registry():
    return [XConnector(), RSSConnector(), WebConnector()]


def pick_connector(url: str):
    for connector in connector_registry():
        if connector.can_handle(url):
            return connector
    return None
