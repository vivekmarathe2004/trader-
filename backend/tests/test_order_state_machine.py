"""
Tests for formal Order State Machine transitions and rejection handling.
"""
import pytest
from app.execution.state_machine import order_state_machine
from app.execution.enums import OrderState


def test_order_state_machine_valid_flow():
    order_id = "TEST-ORDER-1"
    
    # SIGNAL -> RISK_CHECK
    valid, _ = order_state_machine.transition(order_id, OrderState.RISK_CHECK)
    assert valid is True
    assert order_state_machine.get_state(order_id) == OrderState.RISK_CHECK

    # RISK_CHECK -> ORDER_CREATED
    valid, _ = order_state_machine.transition(order_id, OrderState.ORDER_CREATED)
    assert valid is True

    # ORDER_CREATED -> ORDER_SUBMITTED
    valid, _ = order_state_machine.transition(order_id, OrderState.ORDER_SUBMITTED)
    assert valid is True

    # ORDER_SUBMITTED -> FILLED
    valid, _ = order_state_machine.transition(order_id, OrderState.FILLED)
    assert valid is True

    # FILLED -> POSITION_OPEN
    valid, _ = order_state_machine.transition(order_id, OrderState.POSITION_OPEN)
    assert valid is True


def test_order_state_machine_invalid_transition():
    order_id = "TEST-ORDER-INVALID"
    # Attempt direct transition from SIGNAL to FILLED
    valid, err = order_state_machine.transition(order_id, OrderState.FILLED)
    assert valid is False
    assert "Invalid state machine transition" in err
