"""
Abstract Base Broker Interface defining standard execution contracts.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from app.execution.models import OrderRequest, OrderResult, NormalizedPosition, BrokerConfig


class BaseBroker(ABC):
    broker_id: str
    name: str

    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        """Returns {'equity': float, 'free_balance': float, 'currency': str}"""
        pass

    @abstractmethod
    def get_positions(self) -> List[NormalizedPosition]:
        pass

    @abstractmethod
    async def place_order(self, request: OrderRequest, approved_lots: float) -> OrderResult:
        pass

    @abstractmethod
    async def close_position(self, position_id: str, reason: str = "MANUAL_CLOSE") -> bool:
        pass

    @abstractmethod
    def modify_position(self, position_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        pass

    @abstractmethod
    def get_config(self) -> BrokerConfig:
        pass
