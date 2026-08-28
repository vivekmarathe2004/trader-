"""
Portfolio Risk Engine: Value at Risk (VaR 95% & 99%) and Expected Shortfall (CVaR).
"""
import numpy as np
from typing import Dict, List, Any


class PortfolioRiskEngine:
    def __init__(self):
        pass

    def compute_portfolio_risk_metrics(self, equity: float, returns_history: List[float]) -> Dict[str, float]:
        """
        Computes 1-day 95% and 99% Parametric and Historical VaR, and Expected Shortfall.
        """
        if not returns_history or len(returns_history) < 20:
            # Default conservative estimates (1.5% 1-day VaR)
            var_95_pct = 0.015
            var_99_pct = 0.025
            cvar_95_pct = 0.022
        else:
            returns = np.array(returns_history)
            mean_ret = np.mean(returns)
            std_ret = np.std(returns)
            
            # Parametric VaR (Normal distribution assumption: z=1.645 for 95%, z=2.326 for 99%)
            var_95_pct = float(max(0.005, -(mean_ret - 1.645 * std_ret)))
            var_99_pct = float(max(0.010, -(mean_ret - 2.326 * std_ret)))
            
            # Historical Expected Shortfall (CVaR 95%)
            losses = -returns
            cutoff_95 = np.percentile(losses, 95)
            tail_losses = losses[losses >= cutoff_95]
            cvar_95_pct = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var_95_pct * 1.3

        var_95_usd = round(equity * var_95_pct, 2)
        var_99_usd = round(equity * var_99_usd if 'var_99_usd' in locals() else equity * var_99_pct, 2)
        cvar_95_usd = round(equity * cvar_95_pct, 2)

        return {
            "var_95_pct": round(var_95_pct * 100, 2),
            "var_95_usd": var_95_usd,
            "var_99_pct": round(var_99_pct * 100, 2),
            "var_99_usd": var_99_usd,
            "cvar_95_pct": round(cvar_95_pct * 100, 2),
            "cvar_95_usd": cvar_95_usd,
        }


portfolio_risk_engine = PortfolioRiskEngine()
