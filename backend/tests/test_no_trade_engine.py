"""
Tests for Deterministic No-Trade Engine and Veto filters.
"""
import pytest
import pandas as pd
from app.trading.no_trade import no_trade_engine
from app.services.mock_provider import mock_provider
from app.features.pipeline import compute_indicator_pipeline


def test_no_trade_rsi_climax_guard():
    raw_df = mock_provider.generate_ohlcv("EURUSD", "15m", 50)
    df = compute_indicator_pipeline(raw_df)

    # Force RSI = 85.0 on latest candle
    df.loc[df.index[-1], "rsi_14"] = 85.0

    is_vetoed, reasons = no_trade_engine.evaluate_vetoes(
        symbol="EURUSD",
        side="BUY",
        strategy_id="TEST",
        df_m15=df,
    )
    assert is_vetoed is True
    assert any("RSI Climax Guard" in r for r in reasons)


def test_no_trade_spread_breach():
    raw_df = mock_provider.generate_ohlcv("EURUSD", "15m", 50)
    df = compute_indicator_pipeline(raw_df)

    quote = {"quality_valid": True, "spread_pips": 4.5}
    is_vetoed, reasons = no_trade_engine.evaluate_vetoes(
        symbol="EURUSD",
        side="BUY",
        strategy_id="TEST",
        df_m15=df,
        quote=quote,
    )
    assert is_vetoed is True
    assert any("exceeds" in r for r in reasons)
