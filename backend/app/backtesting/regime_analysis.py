"""
Regime-Segmented Performance Analysis.
Isolates strategy returns and win rates across the 5 canonical market regimes.
"""
from typing import Dict, List, Any
from app.trading.strategies import QuantitativeStrategy, ALL_QUANT_STRATEGIES
from app.backtesting.engine import backtest_engine
from app.trading.regime import MarketRegime


class RegimePerformanceAnalyzer:
    def evaluate_regime_breakdown(self, strategy_id: str, symbol: str = "EURUSD") -> Dict[str, Any]:
        strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == strategy_id), ALL_QUANT_STRATEGIES[0])
        res = backtest_engine.run_backtest(strat, symbol, bars_count=500)
        trades = res.get("trades", [])

        regimes = [
            MarketRegime.STRONG_BULLISH_TREND.value,
            MarketRegime.WEAK_BULLISH_TREND.value,
            MarketRegime.SIDEWAYS_RANGE.value,
            MarketRegime.HIGH_VOLATILITY.value,
            MarketRegime.STRONG_BEARISH_TREND.value,
        ]

        breakdown = {}
        for r in regimes:
            reg_trades = [t for t in trades if t.get("regime") == r]
            if reg_trades:
                pnl = sum(t["pnl_usd"] for t in reg_trades)
                wins = len([t for t in reg_trades if t["pnl_usd"] > 0])
                wr = round((wins / len(reg_trades)) * 100.0, 1)
            else:
                pnl = 0.0
                wr = 0.0
            breakdown[r] = {
                "trades_count": len(reg_trades),
                "pnl_usd": round(pnl, 2),
                "win_rate_pct": wr,
                "is_allowed_regime": r in strat.allowed_regimes,
            }

        return {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "overall_return_pct": res["metrics"]["total_return_pct"],
            "regime_breakdown": breakdown,
        }


regime_analyzer = RegimePerformanceAnalyzer()
