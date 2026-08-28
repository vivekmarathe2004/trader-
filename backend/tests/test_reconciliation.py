"""
Tests for Remote vs Local Position Reconciliation Engine.
"""
import pytest
from app.execution.reconciliation import reconciliation_engine


def test_reconciliation_audit():
    result = reconciliation_engine.reconcile_active_broker()
    assert "is_synced" in result
    assert "broker_id" in result
    assert "discrepancies_count" in result
    assert isinstance(result["discrepancies"], list)
