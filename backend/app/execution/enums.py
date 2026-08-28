"""
Execution layer enums for orders, broker states, and order state machine.
"""
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class ExecutionMode(str, Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"


class OrderState(str, Enum):
    # Standard Flow
    SIGNAL = "SIGNAL"
    RISK_CHECK = "RISK_CHECK"
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    POSITION_OPEN = "POSITION_OPEN"
    POSITION_MODIFIED = "POSITION_MODIFIED"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    RECONCILED = "RECONCILED"

    # Explicit Failure & Disconnect States
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    BROKER_ERROR = "BROKER_ERROR"
    RECONCILIATION_FAILED = "RECONCILIATION_FAILED"
