"""
Tests for the 6 Quantitative Strategies, Indicators, and Candlestick Pattern Engine.
"""
import pytest
from app.services.mock_provider import mock_provider
from app.features.pipeline import compute_indicator_pipeline
from app.trading.strategies import ALL_QUANT_STRATEGIES
from app.trading.pattern_engine import detect_candlestick_patterns
from app.trading.regime import classify_market_regime


def test_strategy_definitions_and_metadata():
    assert len(ALL_QUANT_STRATEGIES) >= 6
    for strat in ALL_QUANT_STRATEGIES:
        meta = strat.get_metadata()
        assert "strategy_id" in meta
        assert "version" in meta
        assert "allowed_regimes" in meta
        assert meta["min_risk_reward"] >= 1.5


def test_indicator_pipeline_enrichment():
    raw_df = mock_provider.generate_ohlcv("EURUSD", "5m", 150)
    df = compute_indicator_pipeline(raw_df)
    
    assert "ema_3" in df.columns
    assert "ema_8" in df.columns
    assert "ema_21" in df.columns
    assert "ema_20" in df.columns
    assert "ema_50" in df.columns
    assert "rsi_14" in df.columns
    assert "atr_5" in df.columns
    assert "atr_14" in df.columns
    assert "stoch_k" in df.columns
    assert "stoch_d" in df.columns
    assert "vwap" in df.columns
    assert "macd_hist" in df.columns
    assert "bb_upper" in df.columns
    assert "adx_14" in df.columns
    assert "supertrend" in df.columns


def test_short_timeframe_scalp_strategies():
    raw_df = mock_provider.generate_ohlcv("EURUSD", "1m", 100)
    df = compute_indicator_pipeline(raw_df)
    
    scalp_ids = ["M1_MICRO_MOMENTUM_SCALP", "M5_ORDERFLOW_FVG_SCALP", "M3_VWAP_MICRO_PULLBACK"]
    for sid in scalp_ids:
        strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == sid), None)
        assert strat is not None
        sig = strat.evaluate(df, "EURUSD")
        assert sig.strategy_id == sid
        assert sig.decision in ("APPROVED", "NO_SIGNAL", "NO_TRADE")


def test_candlestick_pattern_detection():
    raw_df = mock_provider.generate_ohlcv("EURUSD", "15m", 50)
    df = compute_indicator_pipeline(raw_df)
    patterns = detect_candlestick_patterns(df)
    assert isinstance(patterns, list)


def test_market_regime_classification():
    raw_df = mock_provider.generate_ohlcv("EURUSD", "15m", 150)
    df = compute_indicator_pipeline(raw_df)
    regime = classify_market_regime(df)
    assert "regime" in regime
    assert "adx" in regime

