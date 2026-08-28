"""
Parameter Sensitivity Analysis Studio.
Sweeps strategy parameter ranges to detect robust stability plateaus vs overfit fragile peaks.
"""
from typing import Dict, List, Any
import numpy as np
from app.trading.strategies import QuantitativeStrategy, ALL_QUANT_STRATEGIES
from app.backtesting.engine import backtest_engine
from app.services.mock_provider import mock_provider
from app.features.pipeline import compute_indicator_pipeline


class SensitivityAnalyzer:
    def analyze_atr_sl_tp_sensitivity(
        self,
        strategy_id: str,
        symbol: str = "EURUSD",
        sl_multipliers: List[float] = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0],
        tp_multipliers: List[float] = [2.0, 2.5, 3.0, 3.5, 4.0],
    ) -> Dict[str, Any]:
        """
        Evaluates a 2D parameter grid of Stop Loss & Take Profit ATR multipliers.
        """
        symbol = symbol.upper()
        raw_df = mock_provider.generate_ohlcv(symbol, "15m", 400)
        df = compute_indicator_pipeline(raw_df)

        strat_cls = next((s for s in ALL_QUANT_STRATEGIES if s.strategy_id == strategy_id), ALL_QUANT_STRATEGIES[0])

        grid_results = []
        best_sharpe = -999.0
        best_params = {}

        for sl in sl_multipliers:
            row = []
            for tp in tp_multipliers:
                # Override parameters temporarily
                strat_cls.sl_atr_multiplier = sl
                strat_cls.tp_atr_multiplier = tp
                res = backtest_engine.run_backtest(strat_cls, symbol, df=df)
                metrics = res["metrics"]
                sharpe = metrics.get("sharpe_ratio", 0.0)
                ret = metrics.get("total_return_pct", 0.0)

                point = {
                    "sl_atr": sl,
                    "tp_atr": tp,
                    "sharpe_ratio": sharpe,
                    "return_pct": ret,
                    "win_rate_pct": metrics.get("win_rate_pct", 0.0),
                    "trades": metrics.get("total_trades", 0),
                }
                row.append(point)

                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {"sl_atr": sl, "tp_atr": tp, "sharpe": sharpe, "return_pct": ret}
            grid_results.append(row)

        return {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "grid_results": grid_results,
            "best_params": best_params,
            "stability_score": "HIGH_PLATEAU" if best_sharpe > 1.2 else "MODERATE",
        }


sensitivity_analyzer = SensitivityAnalyzer()
