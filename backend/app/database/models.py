"""
SQLAlchemy ORM models for quantitative platform entities.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, Index
from app.database.session import Base
from app.core.logging import format_ist_timestamp


class CandleModel(Base):
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("idx_symbol_tf_ts", "symbol", "timeframe", "timestamp", unique=True),
    )


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(64), unique=True, index=True, nullable=False)
    client_order_id = Column(String(64), index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False, default="MARKET")
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    state = Column(String(30), index=True, nullable=False, default="ORDER_CREATED")
    broker = Column(String(30), nullable=False, default="MOCK_BROKER")
    strategy_id = Column(String(50), nullable=True)
    strategy_version = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    idempotency_key = Column(String(64), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PositionModel(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    side = Column(String(10), nullable=False)
    lots = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    initial_sl = Column(Float, nullable=True)
    break_even_active = Column(Boolean, default=False)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    broker = Column(String(30), nullable=False, default="MOCK_BROKER")
    status = Column(String(20), index=True, default="OPEN")  # OPEN, CLOSED
    strategy_id = Column(String(50), nullable=True)
    strategy_version = Column(String(20), nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)


class TradeModel(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(64), unique=True, index=True, nullable=False)
    position_id = Column(String(64), index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    side = Column(String(10), nullable=False)
    lots = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    pnl_pips = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    strategy_id = Column(String(50), nullable=True)
    strategy_version = Column(String(20), nullable=True)
    exit_reason = Column(String(50), nullable=False)  # TP_HIT, SL_HIT, BE_HIT, MANUAL_CLOSE, EMERGENCY_STOP
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, default=datetime.utcnow)


class SignalModel(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp_ist = Column(String(40), nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), nullable=False)
    strategy_id = Column(String(50), index=True, nullable=False)
    strategy_version = Column(String(20), nullable=False)
    decision = Column(String(20), index=True, nullable=False)  # APPROVED, NO_TRADE
    market_regime = Column(String(40), nullable=False)
    side = Column(String(10), nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=True)
    indicators_json = Column(Text, nullable=True)
    rules_json = Column(Text, nullable=True)
    veto_reasons_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp_ist = Column(String(40), nullable=False)
    event_type = Column(String(50), index=True, nullable=False)
    payload_json = Column(Text, nullable=False)
    previous_hash = Column(String(64), nullable=False)
    hash = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class StrategyModel(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(64), index=True, nullable=False)
    version = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    strategy_class = Column(String(50), nullable=False)  # TREND_FOLLOWING, MEAN_REVERSION, BREAKOUT, LIQUIDITY_REVERSAL, CUSTOM
    status = Column(String(30), default="RESEARCH")     # RESEARCH, BACKTESTED, WALK_FORWARD_VERIFIED, PAPER_TRADING, APPROVED, LIVE, DEPRECATED
    params_json = Column(Text, nullable=False)
    rules_json = Column(Text, nullable=False)
    backtest_metrics_json = Column(Text, nullable=True)
    promotion_stage = Column(String(30), default="RESEARCH")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_strategy_ver", "strategy_id", "version", unique=True),
    )


class BrokerCredentialModel(Base):
    __tablename__ = "broker_credentials"

    id = Column(Integer, primary_key=True, index=True)
    broker_id = Column(String(50), unique=True, index=True, nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)
    account_id_encrypted = Column(Text, nullable=True)
    environment = Column(String(30), nullable=True, default="paper")
    extra_params_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

