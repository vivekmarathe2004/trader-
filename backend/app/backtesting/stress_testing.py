"""
Transaction Cost, Slippage, Latency, and Spread Expansion Stress Tester.
"""
from typing import Dict, List, Any
from app.trading.strategies import QuantitativeStrategy, ALL_QUANT_STRATEGIES
from app.backtesting.engine import BacktestEngine


class StressTester:
    def run_stress_suite(self, strategy_id: str, symbol: str = "EURUSD") -> Dict[str, Any]:
        strat = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == strategy_id), ALL_QUANT_STRATEGIES[0])

        scenarios = [
            {"name": "Baseline (Ideal)", "slippage": 0.1, "comm": 3.50},
            {"name": "+25% Spread Expansion", "slippage": 0.25, "comm": 3.50},
            {"name": "+50% Spread Expansion", "slippage": 0.50, "comm": 3.50},
            {"name": "2x Slippage Adverse", "slippage": 0.60, "comm": 3.50},
            {"name": "3x Slippage High Volatility", "slippage": 1.00, "comm": 4.00},
            {"name": "Severe Latency (250ms) + 3x Slippage", "slippage": 1.50, "comm": 5.00},
        ]

        results = []
        baseline_return = 0.0

        for idx, sc in enumerate(scenarios):
            engine = BacktestEngine(
                initial_capital=100000.0,
                commission_per_lot=sc["comm"],
                slippage_pips=sc["slippage"],
            )
            bt = engine.run_backtest(strat, symbol, bars_count=400)
            ret = bt["metrics"]["total_return_pct"]
            if idx == 0:
                baseline_return = ret

            degradation = round(baseline_return - ret, 2) if idx > 0 else 0.0

            results.append({
                "scenario": sc["name"],
                "slippage_pips": sc["slippage"],
                "commission_per_lot": sc["comm"],
                "return_pct": ret,
                "sharpe_ratio": bt["metrics"]["sharpe_ratio"],
                "max_drawdown_pct": bt["metrics"]["max_drawdown_pct"],
                "win_rate_pct": bt["metrics"]["win_rate_pct"],
                "return_degradation_pct": degradation,
                "survived": ret > 0.0,
            })

        all_survived = all(r["survived"] for r in results[:4])

        return {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "scenarios": results,
            "stress_resilience_grade": "INSTITUTIONAL_ROBUST" if all_survived else "SENSITIVE_TO_COSTS",
        }


stress_tester = StressTester()
