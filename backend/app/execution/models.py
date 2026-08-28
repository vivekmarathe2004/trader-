"""
Pydantic data models for execution, positions, and broker configurations.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.execution.enums import OrderSide, OrderType, OrderState, ExecutionMode
from app.core.logging import format_ist_timestamp


class OrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    quantity: float = 0.0  # If 0.0, auto-sized by RiskEngine
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_id: str = "MANUAL"
    strategy_version: str = "v1.0.0"
    client_order_id: Optional[str] = None


class OrderResult(BaseModel):
    success: bool
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    order_state: OrderState
    fill_price: Optional[float] = None
    fill_quantity: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0
    error_message: Optional[str] = None
    timestamp_ist: str = Field(default_factory=format_ist_timestamp)


class NormalizedPosition(BaseModel):
    position_id: str
    symbol: str
    side: str
    lots: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    initial_sl: Optional[float] = None
    break_even_active: bool = False
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    broker: str = "MOCK_BROKER"
    status: str = "OPEN"  # OPEN, CLOSED
    strategy_id: str = "SUPERTREND_TREND_FOLLOWING"
    strategy_version: str = "v1.0.0"
    opened_at_ist: str = Field(default_factory=format_ist_timestamp)


class BrokerConfig(BaseModel):
    broker_id: str
    name: str
    mode: ExecutionMode
    is_active: bool = False
    is_connected: bool = False
    api_key_masked: str = "Not Configured"
    environment: str = "paper"  # paper, testnet, live
    latency_ms: float = 0.0
    last_heartbeat_ist: str = Field(default_factory=format_ist_timestamp)
