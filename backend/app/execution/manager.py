"""
Hot-swappable zero-downtime Broker Manager with un-bypassable RiskEngine routing.
"""
import time
from typing import List, Dict, Optional, Any
from app.execution.broker_interface import BaseBroker
from app.execution.registry import broker_registry
from app.execution.models import OrderRequest, OrderResult, NormalizedPosition, BrokerConfig
from app.execution.enums import OrderState
from app.risk.engine import risk_engine
from app.events.bus import event_bus
from app.events.types import OrderEvent, ExecutionEvent, PositionEvent
from app.core.logging import logger


class BrokerManager:
    def __init__(self, default_broker_id: str = "MOCK_BROKER"):
        self._active_broker_id: str = default_broker_id

    def get_active_broker(self) -> BaseBroker:
        return broker_registry.get_broker(self._active_broker_id)

    def set_active_broker(self, broker_id: str) -> bool:
        broker_id = broker_id.upper()
        broker = broker_registry.get_broker(broker_id)
        if broker:
            self._active_broker_id = broker_id
            logger.warning(f"Active broker switched to: {broker_id}")
            return True
        return False

    def get_active_broker_id(self) -> str:
        return self._active_broker_id

    def get_broker_by_id(self, broker_id: str) -> Optional[BaseBroker]:
        """Return a specific broker instance by ID without changing the active broker."""
        return broker_registry.get_broker(broker_id.upper())

    def list_all_broker_configs(self) -> List[BrokerConfig]:
        configs = []
        for broker in broker_registry.list_brokers():
            cfg = broker.get_config()
            cfg.is_active = (broker.broker_id == self._active_broker_id)
            configs.append(cfg)
        return configs

    def update_broker_credentials(
        self,
        broker_id: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: Optional[str] = None,
        extra_params: Optional[dict] = None,
    ) -> BrokerConfig:
        broker_id = broker_id.upper()
        broker = broker_registry.get_broker(broker_id)
        if broker and hasattr(broker, "configure_credentials"):
            broker.configure_credentials(
                api_key=api_key,
                api_secret=api_secret,
                account_id=account_id,
                environment=environment,
                extra_params=extra_params,
            )
        cfg = broker.get_config() if broker else None
        return cfg

    async def test_broker_connection(self, broker_id: str) -> Dict[str, Any]:
        broker_id = broker_id.upper()
        broker = broker_registry.get_broker(broker_id)
        if not broker:
            return {"broker_id": broker_id, "is_connected": False, "error": f"Unknown broker {broker_id}"}
        
        start_t = time.time()
        try:
            connected = await broker.connect()
            latency = (time.time() - start_t) * 1000
            balance = broker.get_balance()
            return {
                "broker_id": broker_id,
                "name": broker.name,
                "is_connected": connected,
                "latency_ms": round(latency, 2),
                "balance": balance,
            }
        except Exception as e:
            return {
                "broker_id": broker_id,
                "name": broker.name,
                "is_connected": False,
                "latency_ms": 0.0,
                "error": str(e),
            }

    def load_persisted_credentials(self, credentials_list: List[Dict[str, Any]]):
        for c in credentials_list:
            self.update_broker_credentials(
                broker_id=c["broker_id"],
                api_key=c.get("api_key"),
                api_secret=c.get("api_secret"),
                account_id=c.get("account_id"),
                environment=c.get("environment"),
                extra_params=c.get("extra_params"),
            )

    async def submit_order(self, request: OrderRequest) -> OrderResult:
        active_broker = self.get_active_broker()
        open_positions = active_broker.get_positions()
        
        # Un-bypassable Risk Validation
        from app.services.unified_provider import unified_provider
        quote = unified_provider.get_latest_quote(request.symbol)
        spread_pips = quote.get("spread_pips", 1.2)
        
        is_approved, rejection_reason, approved_lots = risk_engine.validate_order(
            symbol=request.symbol,
            side=request.side.value,
            quantity=request.quantity,
            price=request.price or quote["price"],
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            broker_type=active_broker.broker_id,
            open_positions=open_positions,
            strategy_id=request.strategy_id,
            current_spread_pips=spread_pips,
        )

        if not is_approved:
            logger.warning(f"Order for {request.symbol} rejected by RiskEngine: {rejection_reason}")
            return OrderResult(
                success=False,
                order_id=f"REJ-{id(request)}",
                client_order_id=request.client_order_id or "REJECTED",
                symbol=request.symbol,
                side=request.side.value,
                order_state=OrderState.REJECTED,
                error_message=rejection_reason,
            )

        # Place order on active broker
        result = await active_broker.place_order(request, approved_lots)

        # Publish execution events
        if result.success:
            await event_bus.publish(OrderEvent(
                order_id=result.order_id,
                client_order_id=result.client_order_id,
                symbol=result.symbol,
                side=result.side,
                order_type=request.order_type.value,
                quantity=result.fill_quantity,
                price=result.fill_price,
                state=result.order_state.value,
                broker=active_broker.broker_id,
            ))

            await event_bus.publish(ExecutionEvent(
                order_id=result.order_id,
                symbol=result.symbol,
                side=result.side,
                fill_price=result.fill_price or 1.0,
                fill_quantity=result.fill_quantity,
                slippage=result.slippage,
                commission=result.commission,
                broker=active_broker.broker_id,
            ))

        return result

    async def flatten_all_positions(self, reason: str = "EMERGENCY_FLATTEN") -> int:
        active_broker = self.get_active_broker()
        positions = active_broker.get_positions()
        closed_count = 0
        for pos in positions:
            success = await active_broker.close_position(pos.position_id, reason=reason)
            if success:
                closed_count += 1
        logger.critical(f"Flattened {closed_count} open positions on {active_broker.broker_id} ({reason}).")
        return closed_count


broker_manager = BrokerManager()
