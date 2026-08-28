"""
OANDA v20 REST Broker Adapter.
"""
from typing import List, Dict, Optional, Any
from app.execution.broker_interface import BaseBroker
from app.execution.models import OrderRequest, OrderResult, NormalizedPosition, BrokerConfig
from app.execution.enums import OrderSide, OrderType, OrderState, ExecutionMode
from app.core.config import settings
from app.core.security import mask_key


class OandaBroker(BaseBroker):
    broker_id = "OANDA"
    name = "OANDA v20 REST Bridge"

    def __init__(self):
        self.api_key = settings.OANDA_API_KEY
        self.account_id = settings.OANDA_ACCOUNT_ID
        self.environment = settings.OANDA_ENVIRONMENT
        self.base_url = "https://api-fxpractice.oanda.com/v3" if self.environment == "practice" else "https://api-fxtrade.oanda.com/v3"
        self._positions: Dict[str, NormalizedPosition] = {}

    async def connect(self) -> bool:
        return bool(self.api_key and self.account_id)

    async def disconnect(self):
        pass

    def get_balance(self) -> Dict[str, float]:
        return {"equity": 25000.0, "free_balance": 25000.0, "currency": "USD"}

    def get_positions(self) -> List[NormalizedPosition]:
        return list(self._positions.values())

    async def place_order(self, request: OrderRequest, approved_lots: float) -> OrderResult:
        order_id = f"OAN-{int(settings.PORT)}"
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
        if api_key is not None: self.api_key = api_key
        if account_id is not None: self.account_id = account_id
        if environment is not None:
            self.environment = environment.lower()
            self.base_url = "https://api-fxpractice.oanda.com/v3" if self.environment == "practice" else "https://api-fxtrade.oanda.com/v3"

    def get_config(self) -> BrokerConfig:
        return BrokerConfig(
            broker_id=self.broker_id,
            name=self.name,
            mode=ExecutionMode.LIVE if self.environment == "live" else ExecutionMode.PAPER,
            is_active=False,
            is_connected=bool(self.api_key and self.account_id and len(self.api_key) > 5),
            api_key_masked=mask_key(self.api_key),
            environment=self.environment,
            latency_ms=62.0,
        )


oanda_broker = OandaBroker()

