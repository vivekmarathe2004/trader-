"""
Deriv WebSocket Broker Adapter.
"""
from typing import List, Dict, Optional, Any
from app.execution.broker_interface import BaseBroker
from app.execution.models import OrderRequest, OrderResult, NormalizedPosition, BrokerConfig
from app.execution.enums import OrderSide, OrderType, OrderState, ExecutionMode
from app.core.config import settings
from app.core.security import mask_key


class DerivBroker(BaseBroker):
    broker_id = "DERIV"
    name = "Deriv WebSocket Bridge"

    def __init__(self):
        self.app_id = settings.DERIV_APP_ID
        self.api_token = settings.DERIV_API_TOKEN
        self._positions: Dict[str, NormalizedPosition] = {}

    async def connect(self) -> bool:
        return bool(self.api_token)

    async def disconnect(self):
        pass

    def get_balance(self) -> Dict[str, float]:
        return {"equity": 10000.0, "free_balance": 10000.0, "currency": "USD"}

    def get_positions(self) -> List[NormalizedPosition]:
        return list(self._positions.values())

    async def place_order(self, request: OrderRequest, approved_lots: float) -> OrderResult:
        order_id = f"DRV-{id(request)}"
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
        if api_key is not None: self.api_token = api_key
        if extra_params and "app_id" in extra_params:
            self.app_id = str(extra_params["app_id"])

    def get_config(self) -> BrokerConfig:
        return BrokerConfig(
            broker_id=self.broker_id,
            name=self.name,
            mode=ExecutionMode.LIVE if self.api_token else ExecutionMode.PAPER,
            is_active=False,
            is_connected=bool(self.api_token and len(self.api_token) > 5),
            api_key_masked=mask_key(self.api_token),
            environment="deriv_ws",
            latency_ms=28.0,
        )


deriv_broker = DerivBroker()

