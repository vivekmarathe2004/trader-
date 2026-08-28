"""
Hardened Risk Engine tests verifying all unbypassable safety constraints.
"""
import pytest
from app.risk.engine import risk_engine
from app.execution.models import NormalizedPosition


@pytest.fixture(autouse=True)
def clean_risk_state():
    risk_engine.reset_daily_stats()
    risk_engine.reset_emergency_kill_switch()


def test_risk_engine_max_open_positions():
    dummy_positions = [
        NormalizedPosition(position_id=f"P{i}", symbol="EURUSD", side="BUY", lots=0.1, entry_price=1.085, current_price=1.085)
        for i in range(3)
    ]

    approved, reason, _ = risk_engine.validate_order(
        symbol="GBPUSD",
        side="BUY",
        quantity=0.1,
        price=1.2650,
        stop_loss=1.2600,
        take_profit=1.2800,
        broker_type="MOCK_BROKER",
        open_positions=dummy_positions,
    )
    assert approved is False
    assert "Max Open Positions reached" in reason


def test_risk_engine_min_risk_reward():
    # Attempt R:R = 1.0 (Entry 1.0850, SL 1.0800, TP 1.0900)
    approved, reason, _ = risk_engine.validate_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.1,
        price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0900,
        broker_type="MOCK_BROKER",
        open_positions=[],
    )
    assert approved is False
    assert "below mandatory minimum" in reason


def test_risk_engine_spread_filter():
    approved, reason, _ = risk_engine.validate_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.1,
        price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        broker_type="MOCK_BROKER",
        open_positions=[],
        current_spread_pips=4.5,
    )
    assert approved is False
    assert "Spread 4.50 pips exceeds max threshold" in reason
