"""
Generic Custom REST Broker Adapter.
"""
from typing import List, Dict, Optional, Any
from app.execution.broker_interface import BaseBroker
from app.execution.models import OrderRequest, OrderResult, NormalizedPosition, BrokerConfig
from app.execution.enums import OrderSide, OrderType, OrderState, ExecutionMode


class CustomBroker(BaseBroker):
    broker_id = "CUSTOM_REST"
    name = "Custom Webhook / REST Bridge"

    def __init__(self):
        self._positions: Dict[str, NormalizedPosition] = {}

    async def connect(self) -> bool:
        return True

    async def disconnect(self):
        pass

    def get_balance(self) -> Dict[str, float]:
        return {"equity": 20000.0, "free_balance": 20000.0, "currency": "USD"}

    def get_positions(self) -> List[NormalizedPosition]:
        return list(self._positions.values())

    async def place_order(self, request: OrderRequest, approved_lots: float) -> OrderResult:
        order_id = f"CUS-{id(request)}"
        return OrderResult(
            success=True,
            order_id=order_id,
            client_order_id=request.client_order_id or order_id,
            symbol=request.symbol,
            side=request.side.value,
            order_state=OrderState.FILLED,
            fill_price=request.price or 1.0,
            fill_quantity=approved_lots,
        )

    async def close_position(self, position_id: str, reason: str = "MANUAL_CLOSE") -> bool:
        if position_id in self._positions:
            del self._positions[position_id]
            return True
        return False

    def modify_position(self, position_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        pos = self._positions.get(position_id)
        if pos:
            if stop_loss: pos.stop_loss = stop_loss
            if take_profit: pos.take_profit = take_profit
            return True
        return False

    def configure_credentials(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: Optional[str] = None,
        extra_params: Optional[dict] = None,
    ):
        pass

    def get_config(self) -> BrokerConfig:
        return BrokerConfig(
            broker_id=self.broker_id,
            name=self.name,
            mode=ExecutionMode.PAPER,
            is_active=False,
            is_connected=True,
            api_key_masked="WEBHOOK_ACTIVE",
            environment="custom",
            latency_ms=15.0,
        )


custom_broker = CustomBroker()

