from xfetch.connectors.base import BaseConnector
from xfetch.connectors.registry import connector_registry


def test_all_registered_connectors_implement_base_contract():
    for connector in connector_registry():
        assert isinstance(connector, BaseConnector)
        assert callable(connector.can_handle)
        assert callable(connector.fetch)
