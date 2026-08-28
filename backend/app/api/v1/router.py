"""
FastAPI REST API v1 Router providing 40+ endpoints.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.repository import Repository
from app.core.config import settings
from app.core.security import mask_key
from app.core.logging import logger, log_buffer, format_ist_timestamp
from app.services.unified_provider import unified_provider
from app.trading.strategies import ALL_QUANT_STRATEGIES
from app.trading.research_lab import CustomStrategyDefinition, CustomDynamicStrategy
from app.trading.confluence import confluence_engine
from app.trading.provenance import build_provenance_snapshot
from app.trading.pattern_engine import detect_candlestick_patterns
from app.trading.regime import classify_market_regime
from app.trading.auto_trader import auto_trader
from app.risk.engine import risk_engine
from app.risk.position_sizer import position_sizer
from app.execution.manager import broker_manager
from app.execution.reconciliation import reconciliation_engine
from app.execution.models import OrderRequest, OrderResult
from app.execution.enums import OrderSide, OrderType
from app.backtesting.engine import backtest_engine
from app.backtesting.sensitivity import sensitivity_analyzer
from app.backtesting.regime_analysis import regime_analyzer
from app.backtesting.stress_testing import stress_tester
from app.backtesting.walk_forward import walk_forward_engine
from app.backtesting.monte_carlo import monte_carlo_engine
from app.backtesting.promotion import promotion_manager
from app.monitoring.control_center import control_center
from app.monitoring.attribution import attribution_engine

router = APIRouter(prefix="/v1")


# --- Health, Config & Control Center ---
@router.get("/health")
def health_check():
    return {
        "status": "ONLINE",
        "app_env": settings.APP_ENV,
        "timestamp_ist": format_ist_timestamp(),
        "live_trading_enabled": risk_engine.live_trading_enabled,
        "kill_switch_active": risk_engine.emergency_kill_switch_active,
        "active_broker": broker_manager.get_active_broker_id(),
    }


@router.get("/config")
def get_system_config():
    return {
        "forex_symbols": settings.FOREX_SYMBOLS,
        "crypto_symbols": settings.CRYPTO_SYMBOLS,
        "pip_sizes": settings.PIP_SIZES,
        "risk_limits": {
            "default_risk_per_trade": settings.DEFAULT_RISK_PER_TRADE,
            "max_daily_loss": settings.MAX_DAILY_LOSS,
            "max_drawdown": settings.MAX_DRAWDOWN,
            "max_open_positions": settings.MAX_OPEN_POSITIONS,
            "min_risk_reward": settings.MIN_RISK_REWARD,
            "max_spread_pips": settings.MAX_SPREAD_PIPS,
            "live_trading_enabled": risk_engine.live_trading_enabled,
        },
    }


@router.get("/logs")
def get_audit_logs(limit: int = 100, level: Optional[str] = None, search: Optional[str] = None):
    return log_buffer.get_logs(limit=limit, level=level, search=search)


@router.get("/control-center/health-matrix")
def get_health_matrix():
    return control_center.get_system_health_matrix()


@router.get("/control-center/attribution")
def get_attribution(db: Session = Depends(get_db)):
    repo = Repository(db)
    trades = repo.get_trades(limit=100)
    trade_dicts = [{"strategy_id": t.strategy_id or "TREND_FOLLOWING", "pnl_usd": t.pnl, "symbol": t.symbol, "commission": t.commission} for t in trades]
    return attribution_engine.compute_attribution(trade_dicts)


# --- Emergency Controls ---
@router.post("/emergency-stop")
async def trigger_emergency_stop():
    risk_engine.trigger_emergency_kill_switch("Manual user emergency stop triggered")
    auto_trader.stop()
    closed = await broker_manager.flatten_all_positions(reason="EMERGENCY_STOP")
    return {"success": True, "message": f"Emergency stop armed. Flattened {closed} open positions.", "timestamp": format_ist_timestamp()}


@router.post("/emergency-reset")
def reset_emergency_stop():
    risk_engine.reset_emergency_kill_switch()
    return {"success": True, "message": "Emergency Kill Switch has been disarmed.", "timestamp": format_ist_timestamp()}


@router.post("/live-trading-toggle")
def toggle_live_trading(enabled: bool = Query(...)):
    risk_engine.set_live_trading_gate(enabled)
    return {"success": True, "live_trading_enabled": risk_engine.live_trading_enabled}


# --- Market Data & Indicators ---
@router.get("/market/quotes")
def get_all_market_quotes():
    return unified_provider.get_all_quotes()


@router.get("/market/quote/{symbol}")
def get_single_quote(symbol: str):
    return unified_provider.get_latest_quote(symbol)


@router.get("/market/ohlcv/{symbol}")
def get_ohlcv_data(symbol: str, timeframe: str = "15m", count: int = 200):
    df = unified_provider.get_ohlcv(symbol, timeframe, count)
    return df.to_dict(orient="records")


@router.get("/market/indicators/{symbol}")
def get_enriched_indicators(symbol: str, timeframe: str = "15m", count: int = 200):
    df = unified_provider.get_enriched_pipeline(symbol, timeframe, count)
    return df.to_dict(orient="records")


@router.get("/market/regime/{symbol}")
def get_market_regime(symbol: str):
    df = unified_provider.get_enriched_pipeline(symbol, "15m", 100)
    return classify_market_regime(df)


# --- Signals & Confluence ---
@router.get("/signals")
def get_active_signals(timeframe: Optional[str] = None):
    tf = timeframe or auto_trader.timeframe
    scans = auto_trader.get_latest_scans()
    if not scans or (timeframe and scans and scans[0].get("timeframe") != tf):
        # Generate on-demand for requested timeframe
        scans = []
        for s in settings.ALL_SYMBOLS:
            scans.append(confluence_engine.evaluate_symbol_confluence(s, timeframe=tf))
    return scans


@router.get("/confluence/{symbol}")
def get_symbol_confluence(symbol: str, timeframe: Optional[str] = None):
    tf = timeframe or auto_trader.timeframe
    return confluence_engine.evaluate_symbol_confluence(symbol, timeframe=tf)


@router.get("/signals/no-trade-feed")
def get_no_trade_feed():
    scans = auto_trader.get_latest_scans()
    no_trades = [s for s in scans if s.get("decision") == "NO_TRADE"]
    return no_trades


# --- Quant Lab: Strategies, Builder & Patterns ---
@router.get("/strategies")
def list_strategies():
    return [s.get_metadata() for s in ALL_QUANT_STRATEGIES]


@router.get("/patterns/detect/{symbol}")
def detect_patterns_for_symbol(symbol: str):
    df = unified_provider.get_enriched_pipeline(symbol, "15m", 50)
    return detect_candlestick_patterns(df)


@router.post("/strategy-builder/test")
def test_custom_strategy(definition: CustomStrategyDefinition, symbol: str = "EURUSD"):
    strat = CustomDynamicStrategy(definition)
    df = unified_provider.get_enriched_pipeline(symbol, "15m", 300)
    sig = strat.evaluate(df, symbol)
    bt = backtest_engine.run_backtest(strat, symbol, df=df)
    return {
        "evaluation": sig.model_dump(),
        "backtest": bt,
    }


# --- Quant Lab: Backtesting, Sensitivity, Stress, Walk-Forward, Monte Carlo ---
class BacktestRunRequest(BaseModel):
    strategy_id: str
    symbol: str = "EURUSD"
    timeframe: str = "15m"
    bars_count: int = 500
    custom_definition: Optional[CustomStrategyDefinition] = None


@router.post("/backtest/run")
def run_backtest_endpoint(req: BacktestRunRequest):
    if req.custom_definition:
        strat = CustomDynamicStrategy(req.custom_definition)
    else:
        strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == req.strategy_id), ALL_QUANT_STRATEGIES[0])
    return backtest_engine.run_backtest(strat, req.symbol, timeframe=req.timeframe, bars_count=req.bars_count)


@router.get("/backtest/sensitivity")
def run_sensitivity(strategy_id: str = "SUPERTREND_TREND_FOLLOWING", symbol: str = "EURUSD"):
    return sensitivity_analyzer.analyze_atr_sl_tp_sensitivity(strategy_id, symbol)


@router.get("/backtest/regime-analysis")
def run_regime_analysis(strategy_id: str = "SUPERTREND_TREND_FOLLOWING", symbol: str = "EURUSD"):
    return regime_analyzer.evaluate_regime_breakdown(strategy_id, symbol)


@router.get("/backtest/stress-test")
def run_stress_test(strategy_id: str = "SUPERTREND_TREND_FOLLOWING", symbol: str = "EURUSD"):
    return stress_tester.run_stress_suite(strategy_id, symbol)


@router.get("/backtest/walk-forward")
def run_walk_forward(strategy_id: str = "SUPERTREND_TREND_FOLLOWING", symbol: str = "EURUSD"):
    strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == strategy_id), ALL_QUANT_STRATEGIES[0])
    return walk_forward_engine.run_walk_forward(strat, symbol)


@router.get("/backtest/monte-carlo")
def run_monte_carlo(strategy_id: str = "SUPERTREND_TREND_FOLLOWING", symbol: str = "EURUSD", iterations: int = 1000):
    strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == strategy_id), ALL_QUANT_STRATEGIES[0])
    return monte_carlo_engine.run_monte_carlo(strat, symbol, iterations=iterations)


@router.get("/promotions")
def list_promotions():
    return promotion_manager.list_all_promotions()


@router.post("/promotions/evaluate")
def evaluate_strategy_promotion(strategy_id: str, version: str = "v1.0.0", symbol: str = "EURUSD"):
    strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == strategy_id), ALL_QUANT_STRATEGIES[0])
    bt = backtest_engine.run_backtest(strat, symbol)
    wf = walk_forward_engine.run_walk_forward(strat, symbol)
    mc = monte_carlo_engine.run_monte_carlo(strat, symbol)
    return promotion_manager.evaluate_promotion(
        strategy_id=strategy_id,
        version=version,
        backtest_metrics=bt["metrics"],
        walk_forward_metrics={"oos_consistency_pct": wf["oos_consistency_pct"]},
        monte_carlo_metrics=mc["confidence_metrics"],
        paper_trades_count=35,
    )


# --- AutoTrader ---
@router.get("/auto-trade/status")
def get_autotrader_status():
    return auto_trader.get_status()


@router.get("/auto-trade/mode")
def get_autotrader_mode():
    return {
        "trading_mode": auto_trader.trading_mode,
        "timeframe": auto_trader.timeframe,
        "available_modes": [
            {"mode": "TURBO_1M", "timeframe": "1m", "label": "⚡ Turbo Sub-Minute (<1m)", "description": "Under 1-minute execution with 5m trend filter (15-50s hold)"},
            {"mode": "SCALP_3M", "timeframe": "3m", "label": "3M Momentum Scalp", "description": "3-minute VWAP pullback execution (3-8 min hold)"},
            {"mode": "SCALP_5M", "timeframe": "5m", "label": "5M Momentum Scalp", "description": "5-minute FVG & liquidity execution (5-15 min hold)"},
            {"mode": "INTRADAY_15M", "timeframe": "15m", "label": "15M Intraday", "description": "15-minute standard execution with 1h trend filter (15-60 min hold)"},
        ],
    }


@router.post("/auto-trade/mode")
def set_autotrader_mode(mode: str = Query(..., description="SCALP_1M, SCALP_3M, SCALP_5M, or INTRADAY_15M")):
    auto_trader.set_trading_mode(mode)
    return {
        "success": True,
        "trading_mode": auto_trader.trading_mode,
        "timeframe": auto_trader.timeframe,
        "status": auto_trader.get_status(),
    }


@router.post("/auto-trade/start")
async def start_autotrader():
    auto_trader.start()
    return {"success": True, "is_running": True}


@router.post("/auto-trade/stop")
async def stop_autotrader():
    auto_trader.stop()
    return {"success": True, "is_running": False}


@router.get("/auto-trade/scans")
def get_autotrader_scans():
    return auto_trader.get_latest_scans()


@router.post("/auto-trade/scan-now")
async def scan_and_trade_now_endpoint():
    await auto_trader._execute_scan_cycle(force_execute=True)
    return {
        "success": True,
        "scans_count": len(auto_trader.get_latest_scans()),
        "status": auto_trader.get_status(),
        "performance": auto_trader.get_performance_metrics(),
    }


@router.get("/auto-trade/executions")
def get_autotrader_executions(limit: int = 50):
    return auto_trader.get_executions(limit=limit)


@router.get("/auto-trade/performance")
def get_autotrader_performance():
    return auto_trader.get_performance_metrics()


@router.get("/auto-trade/history")
def get_autotrader_history(limit: int = 100):
    return auto_trader.get_closed_trades(limit=limit)


@router.post("/auto-trade/reset")
def reset_autotrader_endpoint():
    perf = auto_trader.reset_paper_trades()
    return {"success": True, "message": "Paper trades data reset to 0.", "performance": perf}


@router.post("/paper-trading/reset")
def reset_paper_trading_endpoint():
    perf = auto_trader.reset_paper_trades()
    return {"success": True, "message": "Paper trades data reset to 0.", "performance": perf}


# --- Positions, Orders & Trading Operations ---
@router.get("/positions")
async def get_open_positions():
    active_broker = broker_manager.get_active_broker()
    if hasattr(active_broker, "fetch_live_balance"):
        balance = await active_broker.fetch_live_balance()
    else:
        balance = active_broker.get_balance()
    positions = active_broker.get_positions()
    return {
        "broker": active_broker.broker_id,
        "balance": balance,
        "positions": [p.model_dump() for p in positions],
    }


@router.post("/positions/{position_id}/close")
async def close_position_endpoint(position_id: str):
    success = await broker_manager.get_active_broker().close_position(position_id, reason="MANUAL_UI_CLOSE")
    return {"success": success, "position_id": position_id}


@router.post("/positions/{position_id}/modify")
def modify_position_endpoint(position_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
    success = broker_manager.get_active_broker().modify_position(position_id, stop_loss=stop_loss, take_profit=take_profit)
    return {"success": success, "position_id": position_id}


@router.post("/orders/submit")
async def submit_manual_order(req: OrderRequest):
    result = await broker_manager.submit_order(req)
    return result.model_dump()


# --- Brokers & Reconciliation ---
class BrokerCredentialRequest(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    environment: Optional[str] = "paper"
    extra_params: Optional[Dict[str, Any]] = None


def _update_env_file(key_val_map: Dict[str, str]):
    from pathlib import Path
    env_path = str(Path(__file__).resolve().parents[4] / ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        existing_keys = {}
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                k = line_str.split("=", 1)[0].strip()
                existing_keys[k] = idx
        
        for k, v in key_val_map.items():
            if v is not None:
                new_line = f"{k}={v}\n"
                if k in existing_keys:
                    lines[existing_keys[k]] = new_line
                else:
                    lines.append(new_line)
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        logger.error(f"Failed to update .env file: {e}")


@router.get("/brokers")
def list_brokers():
    return broker_manager.list_all_broker_configs()


@router.get("/brokers/{broker_id}/credentials")
def get_broker_credentials_endpoint(broker_id: str, db: Session = Depends(get_db)):
    repo = Repository(db)
    cred = repo.get_broker_credentials(broker_id)
    if not cred:
        return {
            "broker_id": broker_id.upper(),
            "has_credentials": False,
            "api_key_masked": None,
            "has_api_secret": False,
            "account_id_masked": None,
            "environment": "paper",
            "extra_params": {},
        }
    return {
        "broker_id": cred["broker_id"],
        "has_credentials": bool(cred["api_key"] or cred["account_id"]),
        "api_key_masked": mask_key(cred["api_key"]) if cred["api_key"] else None,
        "has_api_secret": bool(cred["api_secret"]),
        "account_id_masked": mask_key(cred["account_id"]) if cred["account_id"] else None,
        "environment": cred["environment"],
        "extra_params": cred["extra_params"],
        "updated_at": cred["updated_at"].isoformat() if cred.get("updated_at") else None,
    }


@router.post("/brokers/{broker_id}/credentials")
def save_broker_credentials_endpoint(broker_id: str, req: BrokerCredentialRequest, db: Session = Depends(get_db)):
    broker_id = broker_id.upper()
    repo = Repository(db)
    
    # 1. Save and encrypt in database
    repo.save_or_update_broker_credentials(
        broker_id=broker_id,
        api_key=req.api_key,
        api_secret=req.api_secret,
        account_id=req.account_id,
        environment=req.environment,
        extra_params=req.extra_params,
    )

    # 2. Update in-memory broker instance
    cfg = broker_manager.update_broker_credentials(
        broker_id=broker_id,
        api_key=req.api_key,
        api_secret=req.api_secret,
        account_id=req.account_id,
        environment=req.environment,
        extra_params=req.extra_params,
    )

    # 3. Synchronize with .env file for cold restarts
    env_updates = {}
    if broker_id == "BINANCE":
        if req.api_key: env_updates["BINANCE_API_KEY"] = req.api_key
        if req.api_secret: env_updates["BINANCE_API_SECRET"] = req.api_secret
        if req.environment: env_updates["BINANCE_TESTNET"] = "True" if req.environment.lower() == "testnet" else "False"
    elif broker_id == "OANDA":
        if req.api_key: env_updates["OANDA_API_KEY"] = req.api_key
        if req.account_id: env_updates["OANDA_ACCOUNT_ID"] = req.account_id
        if req.environment: env_updates["OANDA_ENVIRONMENT"] = req.environment.lower()
    elif broker_id == "DERIV":
        if req.api_key: env_updates["DERIV_API_TOKEN"] = req.api_key
        if req.extra_params and "app_id" in req.extra_params: env_updates["DERIV_APP_ID"] = str(req.extra_params["app_id"])
    elif broker_id == "MT5":
        if req.extra_params:
            if "host" in req.extra_params: env_updates["MT5_HOST"] = str(req.extra_params["host"])
            if "port" in req.extra_params: env_updates["MT5_PORT"] = str(req.extra_params["port"])
    
    if env_updates:
        _update_env_file(env_updates)

    logger.info(f"Updated and persisted credentials for {broker_id} (AES-256 + .env).")
    return {
        "success": True,
        "broker_id": broker_id,
        "config": cfg.model_dump() if cfg else None,
        "message": "Credentials encrypted and persisted successfully.",
    }


@router.post("/brokers/{broker_id}/test")
async def test_broker_connection_endpoint(broker_id: str):
    return await broker_manager.test_broker_connection(broker_id)


@router.post("/brokers/{broker_id}/set-active")
def set_active_broker_endpoint(broker_id: str):
    success = broker_manager.set_active_broker(broker_id)
    return {"success": success, "active_broker": broker_manager.get_active_broker_id()}


@router.get("/brokers/{broker_id}/reconcile")
def reconcile_broker_endpoint(broker_id: str):
    return reconciliation_engine.reconcile_for_broker(broker_id)


@router.post("/brokers/flatten-all")
async def flatten_all_endpoint():
    count = await broker_manager.flatten_all_positions(reason="MANUAL_USER_FLATTEN")
    return {"success": True, "flattened_count": count}


# --- Risk ---
@router.get("/risk/status")
def get_risk_status():
    open_pos = broker_manager.get_active_broker().get_positions()
    return risk_engine.get_risk_status(open_pos)


@router.get("/risk/calculate-size")
def calculate_lot_size(symbol: str, entry_price: float, stop_loss: float, equity: Optional[float] = None):
    eq = equity or risk_engine._current_equity
    lots = position_sizer.calculate_lots(symbol, eq, entry_price, stop_loss)
    return {"symbol": symbol, "equity": eq, "calculated_lots": lots}


@router.get("/performance")
def get_performance_endpoint(db: Session = Depends(get_db)):
    repo = Repository(db)
    return repo.get_performance_statistics()
