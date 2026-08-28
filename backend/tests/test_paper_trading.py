"""
Tests for Simulated Paper Broker (MockBroker), fills, slippage, and position sizing.
"""
import pytest
from app.execution.mock_broker import mock_broker
from app.execution.models import OrderRequest
from app.execution.enums import OrderSide, OrderType


@pytest.mark.asyncio
async def test_mock_broker_order_fill():
    mock_broker._positions.clear()
    req = OrderRequest(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
    )

    result = await mock_broker.place_order(req, approved_lots=0.1)
    assert result.success is True
    assert result.fill_price > 0
    assert result.fill_quantity == 0.1
    assert result.commission > 0

    positions = mock_broker.get_positions()
    assert len(positions) == 1

    # Close the position
    pos_id = positions[0].position_id
    closed = await mock_broker.close_position(pos_id, reason="TEST_CLOSE")
    assert closed is True
    assert len(mock_broker.get_positions()) == 0
