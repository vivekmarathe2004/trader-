"""
Event definitions for asynchronous event bus.
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.logging import format_ist_timestamp


class EventType(str, Enum):
    MARKET_EVENT = "MARKET_EVENT"
    SIGNAL_EVENT = "SIGNAL_EVENT"
    NO_TRADE_EVENT = "NO_TRADE_EVENT"
    RISK_EVENT = "RISK_EVENT"
    ORDER_EVENT = "ORDER_EVENT"
    EXECUTION_EVENT = "EXECUTION_EVENT"
    POSITION_EVENT = "POSITION_EVENT"
    PORTFOLIO_EVENT = "PORTFOLIO_EVENT"
    SYSTEM_EVENT = "SYSTEM_EVENT"


class BaseEvent(BaseModel):
    event_type: EventType
    timestamp_ist: str = Field(default_factory=format_ist_timestamp)
    source: str = "SYSTEM"


class MarketEvent(BaseEvent):
    event_type: EventType = EventType.MARKET_EVENT
    symbol: str
    bid: float
    ask: float
    spread_pips: float
    high_24h: float
    low_24h: float
    volume_24h: float
    regime: str


class SignalEvent(BaseEvent):
    event_type: EventType = EventType.SIGNAL_EVENT
    signal_id: str
    symbol: str
    strategy_id: str
    strategy_version: str
    decision: str  # APPROVED, NO_TRADE
    side: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward: Optional[float] = None
    market_regime: str
    rules_passed: List[str] = Field(default_factory=list)


class NoTradeEvent(BaseEvent):
    event_type: EventType = EventType.NO_TRADE_EVENT
    symbol: str
    strategy_id: str
    strategy_version: str
    market_regime: str
    veto_reasons: List[str] = Field(default_factory=list)


class RiskEvent(BaseEvent):
    event_type: EventType = EventType.RISK_EVENT
    symbol: str
    status: str  # PASSED, REJECTED
    risk_score: float
    daily_loss_pct: float
    drawdown_pct: float
    open_positions_count: int
    rejection_reason: Optional[str] = None


class OrderEvent(BaseEvent):
    event_type: EventType = EventType.ORDER_EVENT
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    state: str  # ORDER_CREATED, ORDER_SUBMITTED, FILLED, REJECTED, etc.
    broker: str
    error_message: Optional[str] = None


class ExecutionEvent(BaseEvent):
    event_type: EventType = EventType.EXECUTION_EVENT
    order_id: str
    symbol: str
    side: str
    fill_price: float
    fill_quantity: float
    slippage: float
    commission: float
    broker: str


class PositionEvent(BaseEvent):
    event_type: EventType = EventType.POSITION_EVENT
    position_id: str
    symbol: str
    side: str
    lots: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    break_even_active: bool = False
    unrealized_pnl: float = 0.0
    status: str  # OPEN, CLOSED


class PortfolioEvent(BaseEvent):
    event_type: EventType = EventType.PORTFOLIO_EVENT
    total_equity: float
    free_balance: float
    daily_pnl: float
    daily_pnl_pct: float
    open_positions: int
    win_rate: float
    drawdown_pct: float
    var_95: float
    cvar_95: float


class SystemEvent(BaseEvent):
    event_type: EventType = EventType.SYSTEM_EVENT
    subsystem: str
    status: str  # HEALTHY, DEGRADED, ERROR
    message: str
    latency_ms: float = 0.0
