"""
Event-driven backtesting engine with realistic transaction costs, slippage, and performance metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from app.trading.strategies import QuantitativeStrategy, ALL_QUANT_STRATEGIES
from app.trading.research_lab import CustomDynamicStrategy
from app.features.pipeline import compute_indicator_pipeline
from app.services.mock_provider import mock_provider
from app.core.config import settings


class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0, commission_per_lot: float = 3.50, slippage_pips: float = 0.2):
        self.initial_capital = initial_capital
        self.commission_per_lot = commission_per_lot
        self.slippage_pips = slippage_pips

    def run_backtest(
        self,
        strategy: QuantitativeStrategy,
        symbol: str,
        df: Optional[pd.DataFrame] = None,
        timeframe: str = "15m",
        bars_count: int = 500,
    ) -> Dict[str, Any]:
        symbol = symbol.upper()
        if df is None or df.empty:
            raw_df = mock_provider.generate_ohlcv(symbol, timeframe, bars_count)
            df = compute_indicator_pipeline(raw_df)

        equity = self.initial_capital
        equity_curve = [equity]
        trades = []
        open_trade: Optional[Dict[str, Any]] = None

        pip_size = settings.get_pip_size(symbol)
        lot_units = settings.get_lot_units(symbol)
        fixed_lots = 0.5

        for i in range(50, len(df)):
            sub_df = df.iloc[: i + 1]
            current_bar = df.iloc[i]
            current_price = float(current_bar["close"])
            high_price = float(current_bar["high"])
            low_price = float(current_bar["low"])

            # Check open trade exit
            if open_trade is not None:
                side = open_trade["side"]
                entry_price = open_trade["entry_price"]
                sl = open_trade["stop_loss"]
                tp = open_trade["take_profit"]

                exit_reason = None
                exit_price = current_price

                if side == "BUY":
                    if low_price <= sl:
                        exit_reason = "STOP_LOSS"
                        exit_price = sl - (self.slippage_pips * pip_size)
                    elif high_price >= tp:
                        exit_reason = "TAKE_PROFIT"
                        exit_price = tp
                else:  # SELL
                    if high_price >= sl:
                        exit_reason = "STOP_LOSS"
                        exit_price = sl + (self.slippage_pips * pip_size)
                    elif low_price <= tp:
                        exit_reason = "TAKE_PROFIT"
                        exit_price = tp

                if exit_reason:
                    units = fixed_lots * lot_units
                    if side == "BUY":
                        pnl_usd = (exit_price - entry_price) * units
                        pnl_pips = (exit_price - entry_price) / pip_size
                    else:
                        pnl_usd = (entry_price - exit_price) * units
                        pnl_pips = (entry_price - exit_price) / pip_size

                    comm = self.commission_per_lot * fixed_lots
                    net_pnl = pnl_usd - comm
                    equity += net_pnl
                    equity_curve.append(round(equity, 2))

                    trades.append({
                        "trade_index": len(trades) + 1,
                        "side": side,
                        "entry_price": round(entry_price, 5),
                        "exit_price": round(exit_price, 5),
                        "pnl_usd": round(net_pnl, 2),
                        "pnl_pips": round(pnl_pips, 1),
                        "exit_reason": exit_reason,
                        "regime": open_trade.get("regime", "UNKNOWN"),
                    })
                    open_trade = None

            # Evaluate strategy if no open position
            if open_trade is None:
                sig = strategy.evaluate(sub_df, symbol)
                if sig.decision == "APPROVED" and sig.side and sig.stop_loss and sig.take_profit:
                    fill_price = current_price + (self.slippage_pips * pip_size) if sig.side == "BUY" else current_price - (self.slippage_pips * pip_size)
                    open_trade = {
                        "side": sig.side,
                        "entry_price": fill_price,
                        "stop_loss": sig.stop_loss,
                        "take_profit": sig.take_profit,
                        "regime": sig.market_regime,
                    }

        # Calculate performance statistics
        metrics = self._calculate_metrics(trades, equity_curve)

        return {
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.name,
            "strategy_version": strategy.version,
            "symbol": symbol,
            "timeframe": timeframe,
            "initial_capital": self.initial_capital,
            "final_equity": round(equity, 2),
            "metrics": metrics,
            "trades_count": len(trades),
            "trades": trades,
            "equity_curve": equity_curve,
        }

    def _calculate_metrics(self, trades: List[Dict[str, Any]], equity_curve: List[float]) -> Dict[str, float]:
        if not trades:
            return {
                "total_return_pct": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "win_rate_pct": 0.0,
                "profit_factor": 0.0,
                "expectancy_usd": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
            }

        pnls = [t["pnl_usd"] for t in trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p <= 0]

        total_return_pct = round(((equity_curve[-1] - self.initial_capital) / self.initial_capital) * 100.0, 2)
        win_rate = round((len(winning_trades) / len(trades)) * 100.0, 2)

        gross_profit = sum(winning_trades) if winning_trades else 0.0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0.0
        profit_factor = round(gross_profit / max(1.0, gross_loss), 2)

        # Drawdown calculation
        peaks = np.maximum.accumulate(equity_curve)
        drawdowns = (peaks - equity_curve) / np.maximum(peaks, 1.0)
        max_drawdown = round(float(np.max(drawdowns)) * 100.0, 2)

        # Sharpe & Sortino
        returns = np.diff(equity_curve) / np.maximum(equity_curve[:-1], 1.0)
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = round(float((np.mean(returns) / np.std(returns)) * np.sqrt(252 * 24)), 2)
            downside = returns[returns < 0]
            downside_std = np.std(downside) if len(downside) > 1 else np.std(returns)
            sortino = round(float((np.mean(returns) / max(1e-6, downside_std)) * np.sqrt(252 * 24)), 2)
        else:
            sharpe = 0.0
            sortino = 0.0

        expectancy = round(float(np.mean(pnls)), 2)

        return {
            "total_return_pct": total_return_pct,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown_pct": max_drawdown,
            "win_rate_pct": win_rate,
            "profit_factor": profit_factor,
            "expectancy_usd": expectancy,
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
        }


backtest_engine = BacktestEngine()
