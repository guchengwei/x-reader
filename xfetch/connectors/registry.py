from __future__ import annotations

from xfetch.connectors.rss import RSSConnector
from xfetch.connectors.wechat import WeChatConnector
from xfetch.connectors.web import WebConnector
from xfetch.connectors.x import XConnector
from xfetch.connectors.xiaohongshu import XiaohongshuConnector


def connector_registry():
    return [XConnector(), RSSConnector(), WeChatConnector(), XiaohongshuConnector(), WebConnector()]


def pick_connector(url: str):
    for connector in connector_registry():
        if connector.can_handle(url):
            return connector
    return None
