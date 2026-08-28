"""
Tests for Health, Control Center, Emergency Kill Switch, and Failsafe Monitor.
"""
import pytest
from app.risk.engine import risk_engine
from app.monitoring.control_center import control_center


def test_emergency_kill_switch_lifecycle():
    assert risk_engine.emergency_kill_switch_active is False
    
    # Trigger
    risk_engine.trigger_emergency_kill_switch("Test trigger")
    assert risk_engine.emergency_kill_switch_active is True

    # Validate rejection when armed
    approved, reason, _ = risk_engine.validate_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.1,
        price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        broker_type="MOCK_BROKER",
        open_positions=[],
    )
    assert approved is False
    assert "Kill Switch" in reason

    # Reset
    risk_engine.reset_emergency_kill_switch()
    assert risk_engine.emergency_kill_switch_active is False


def test_control_center_health_matrix():
    matrix = control_center.get_system_health_matrix()
    assert "subsystems" in matrix
    assert len(matrix["subsystems"]) >= 8
    assert matrix["overall_status"] in ["HEALTHY", "WARNING_RECONCILIATION", "EMERGENCY_STOP"]
