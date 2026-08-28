"""
Tests for Broker Adapters, Broker Manager, Hot-Swapping, and Live Trading Gates.
"""
import pytest
from app.execution.manager import broker_manager
from app.execution.registry import broker_registry
from app.risk.engine import risk_engine
from app.execution.models import OrderRequest
from app.execution.enums import OrderSide, OrderType


@pytest.mark.asyncio
async def test_broker_switching():
    assert broker_manager.get_active_broker_id() == "MOCK_BROKER"
    success = broker_manager.set_active_broker("BINANCE")
    assert success is True
    assert broker_manager.get_active_broker_id() == "BINANCE"
    broker_manager.set_active_broker("MOCK_BROKER")


@pytest.mark.asyncio
async def test_live_trading_gate_rejection_on_real_broker():
    broker_manager.set_active_broker("BINANCE")
    risk_engine.set_live_trading_gate(False)

    order_req = OrderRequest(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=65000.0,
        stop_loss=64000.0,
        take_profit=67500.0,
        strategy_id="TEST",
    )

    result = await broker_manager.submit_order(order_req)
    assert result.success is False
    assert "Master Live Trading Gate is locked" in result.error_message

    # Reset
    broker_manager.set_active_broker("MOCK_BROKER")
