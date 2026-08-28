"""
Tests for Market Data Providers, Brownian Motion generator, and Data Quality Guard.
"""
import pytest
from app.services.mock_provider import mock_provider
from app.services.unified_provider import unified_provider
from app.services.quality_guard import quality_guard


def test_mock_provider_tick_generation():
    quote = mock_provider.get_latest_price("EURUSD")
    assert quote["symbol"] == "EURUSD"
    assert quote["bid"] > 0
    assert quote["ask"] > quote["bid"]
    assert quote["spread_pips"] > 0


def test_mock_provider_ohlcv_generation():
    df = mock_provider.generate_ohlcv("EURUSD", "15m", 100)
    assert len(df) == 100
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "close" in df.columns
    assert (df["high"] >= df["low"]).all()


def test_quality_guard_valid_and_invalid_ticks():
    # Valid tick
    valid, err = quality_guard.validate_tick("EURUSD", 1.0850, 1.0852)
    assert valid is True
    assert err is None

    # Inverted spread (Crossed market)
    invalid, err = quality_guard.validate_tick("EURUSD", 1.0860, 1.0850)
    assert invalid is False
    assert "Crossed market" in err

    # Abnormal spread
    invalid_spread, err_spread = quality_guard.validate_tick("EURUSD", 1.0800, 1.0850)
    assert invalid_spread is False
    assert "exceeds" in err_spread
