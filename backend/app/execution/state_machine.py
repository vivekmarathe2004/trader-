"""
Formal 11-State Order State Machine with deterministic transitions and failure handlers.
"""
from typing import Dict, Set, Optional, Tuple
from app.execution.enums import OrderState
from app.core.logging import logger


class OrderStateMachine:
    # Deterministic valid transitions graph
    VALID_TRANSITIONS: Dict[OrderState, Set[OrderState]] = {
        OrderState.SIGNAL: {OrderState.RISK_CHECK, OrderState.REJECTED},
        OrderState.RISK_CHECK: {OrderState.ORDER_CREATED, OrderState.REJECTED},
        OrderState.ORDER_CREATED: {OrderState.ORDER_SUBMITTED, OrderState.CANCELLED, OrderState.BROKER_ERROR},
        OrderState.ORDER_SUBMITTED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.REJECTED, OrderState.CANCELLED, OrderState.EXPIRED, OrderState.BROKER_ERROR},
        OrderState.PARTIALLY_FILLED: {OrderState.FILLED, OrderState.CANCELLED, OrderState.POSITION_OPEN, OrderState.BROKER_ERROR},
        OrderState.FILLED: {OrderState.POSITION_OPEN, OrderState.BROKER_ERROR},
        OrderState.POSITION_OPEN: {OrderState.POSITION_OPEN, OrderState.POSITION_MODIFIED, OrderState.CLOSING, OrderState.CLOSED, OrderState.RECONCILIATION_FAILED},
        OrderState.POSITION_MODIFIED: {OrderState.POSITION_MODIFIED, OrderState.CLOSING, OrderState.CLOSED, OrderState.RECONCILIATION_FAILED},
        OrderState.CLOSING: {OrderState.CLOSED, OrderState.BROKER_ERROR},
        OrderState.CLOSED: {OrderState.RECONCILED, OrderState.RECONCILIATION_FAILED},
        OrderState.RECONCILED: set(),  # Terminal success state

        # Terminal / Error states
        OrderState.REJECTED: set(),
        OrderState.CANCELLED: set(),
        OrderState.EXPIRED: set(),
        OrderState.BROKER_ERROR: {OrderState.CANCELLED, OrderState.RECONCILIATION_FAILED},
        OrderState.RECONCILIATION_FAILED: set(),
    }

    def __init__(self):
        self._order_states: Dict[str, OrderState] = {}

    def get_state(self, order_id: str) -> OrderState:
        if order_id not in self._order_states and order_id.startswith("POS-"):
            return OrderState.POSITION_OPEN
        return self._order_states.get(order_id, OrderState.SIGNAL)

    def transition(self, order_id: str, new_state: OrderState, reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        current_state = self.get_state(order_id)
        
        allowed_targets = self.VALID_TRANSITIONS.get(current_state, set())
        if new_state not in allowed_targets:
            err = f"Invalid state machine transition for Order {order_id}: {current_state} -> {new_state}"
            logger.error(err)
            return False, err

        self._order_states[order_id] = new_state
        logger.info(f"Order {order_id} transitioned: {current_state.value} -> {new_state.value} {f'({reason})' if reason else ''}")
        return True, None


order_state_machine = OrderStateMachine()
