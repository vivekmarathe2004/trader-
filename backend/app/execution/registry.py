"""
Broker registration registry holding active broker adapters.
"""
from typing import Dict, List
from app.execution.broker_interface import BaseBroker
from app.execution.mock_broker import mock_broker
from app.execution.binance_broker import binance_broker
from app.execution.oanda_broker import oanda_broker
from app.execution.deriv_broker import deriv_broker
from app.execution.mt5_broker import mt5_broker
from app.execution.custom_broker import custom_broker


class BrokerRegistry:
    def __init__(self):
        self._brokers: Dict[str, BaseBroker] = {
            mock_broker.broker_id: mock_broker,
            binance_broker.broker_id: binance_broker,
            oanda_broker.broker_id: oanda_broker,
            deriv_broker.broker_id: deriv_broker,
            mt5_broker.broker_id: mt5_broker,
            custom_broker.broker_id: custom_broker,
        }

    def get_broker(self, broker_id: str) -> BaseBroker:
        return self._brokers.get(broker_id.upper(), mock_broker)

    def list_brokers(self) -> List[BaseBroker]:
        return list(self._brokers.values())


broker_registry = BrokerRegistry()
