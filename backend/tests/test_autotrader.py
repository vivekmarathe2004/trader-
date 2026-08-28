"""
Unit and integration tests for AutoTrader background engine and Quality Gate.
"""
import pytest
import asyncio
from app.trading.auto_trader import auto_trader
from app.core.config import settings


@pytest.mark.asyncio
async def test_autotrader_status():
    status = auto_trader.get_status()
    assert "is_running" in status
    assert "quality_mode" in status
    assert status["monitored_symbols_count"] == len(settings.ALL_SYMBOLS)


@pytest.mark.asyncio
async def test_autotrader_start_stop():
    auto_trader.start()
    assert auto_trader.is_running is True
    await asyncio.sleep(0.1)
    auto_trader.stop()
    assert auto_trader.is_running is False


@pytest.mark.asyncio
async def test_autotrader_cooldown_setting():
    auto_trader.trigger_cooldown("EURUSD", is_loss=False)
    status = auto_trader.get_status()
    assert "EURUSD" in status["active_cooldowns"]
    assert status["active_cooldowns"]["EURUSD"] > 0


@pytest.mark.asyncio
async def test_autotrader_performance_metrics():
    # Record a test trade to ensure calculation with data
    test_trade = {
        "trade_id": "TRD-PERF-001",
        "position_id": "POS-PERF-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "lots": 0.5,
        "entry_price": 1.0850,
        "exit_price": 1.0900,
        "pnl": 250.0,
        "pnl_pips": 50.0,
        "strategy_id": "SUPERTREND_TREND_FOLLOWING",
        "exit_reason": "TP_HIT",
    }
    auto_trader.record_closed_trade(test_trade)
    perf = auto_trader.get_performance_metrics()
    assert "win_rate_pct" in perf
    assert "net_pnl" in perf
    assert "net_pnl_inr" in perf
    assert "profit_factor" in perf
    assert "strategy_breakdown" in perf
    assert "symbol_breakdown" in perf
    assert "exit_reason_breakdown" in perf
    assert perf["total_trades"] > 0
    assert 0.0 <= perf["win_rate_pct"] <= 100.0


@pytest.mark.asyncio
async def test_autotrader_record_closed_trade():
    initial_count = len(auto_trader.get_closed_trades(limit=500))
    test_trade = {
        "trade_id": "TRD-TEST-999",
        "position_id": "POS-TEST-999",
        "symbol": "EURUSD",
        "side": "BUY",
        "lots": 0.5,
        "entry_price": 1.0850,
        "exit_price": 1.0900,
        "pnl": 250.0,
        "pnl_pips": 50.0,
        "strategy_id": "SUPERTREND_TREND_FOLLOWING",
        "exit_reason": "TP_HIT",
    }
    auto_trader.record_closed_trade(test_trade)
    closed = auto_trader.get_closed_trades(limit=500)
    assert len(closed) == initial_count + 1
    assert closed[0]["trade_id"] == "TRD-TEST-999"
    assert closed[0]["outcome"] == "WIN"


@pytest.mark.asyncio
async def test_autotrader_reset_paper_trades():
    perf = auto_trader.reset_paper_trades()
    assert perf["total_trades"] == 0
    assert perf["net_pnl"] == 0.0
    assert perf["win_rate_pct"] == 0.0
    assert len(auto_trader.get_closed_trades()) == 0
    assert len(auto_trader.get_executions()) == 0
