"""
Tests for Rule Provenance Snapshot generator and cryptographic hash integrity.
"""
import pytest
from app.trading.provenance import build_provenance_snapshot


def test_provenance_snapshot_generation_and_hash():
    snapshot = build_provenance_snapshot(
        symbol="EURUSD",
        timeframe="15m",
        strategy_id="SUPERTREND_TREND_FOLLOWING",
        strategy_version="v1.0.0",
        market_regime="STRONG_BULLISH_TREND",
        indicator_snapshot={"ema_20": 1.0850, "rsi_14": 62.0},
        rule_evaluation_matrix=[{"rule": "Price > EMA20", "passed": True}],
        decision="APPROVED",
        veto_reasons=[],
    )

    assert "provenance_id" in snapshot
    assert snapshot["symbol"] == "EURUSD"
    assert "record_hash" in snapshot
    assert len(snapshot["record_hash"]) == 64  # SHA-256 length
