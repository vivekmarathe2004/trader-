"""
Strategy Promotion Lifecycle & Acceptance Criteria Registry.
Governs moving strategies through formal validation gates before Paper or Live trading.
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.core.logging import format_ist_timestamp, logger


class PromotionStage(str, Enum):
    RESEARCH = "RESEARCH"
    IN_SAMPLE_BACKTEST = "IN_SAMPLE_BACKTEST"
    WALK_FORWARD_VERIFIED = "WALK_FORWARD_VERIFIED"
    MONTE_CARLO_VERIFIED = "MONTE_CARLO_VERIFIED"
    PAPER_TRADING = "PAPER_TRADING"
    RISK_REVIEW_PASSED = "RISK_REVIEW_PASSED"
    APPROVED_FOR_LIVE = "APPROVED_FOR_LIVE"
    LIVE = "LIVE"
    DEPRECATED = "DEPRECATED"


class ClassAcceptanceCriteria(BaseModel):
    strategy_class: str
    min_backtest_sharpe: float
    min_profit_factor: float
    max_backtest_drawdown_pct: float
    min_oos_consistency_pct: float
    max_monte_carlo_95_dd_pct: float
    min_paper_trades: int


CLASS_CRITERIA: Dict[str, ClassAcceptanceCriteria] = {
    "TREND_FOLLOWING": ClassAcceptanceCriteria(
        strategy_class="TREND_FOLLOWING",
        min_backtest_sharpe=1.3,
        min_profit_factor=1.6,
        max_backtest_drawdown_pct=15.0,
        min_oos_consistency_pct=65.0,
        max_monte_carlo_95_dd_pct=16.0,
        min_paper_trades=30,
    ),
    "MEAN_REVERSION": ClassAcceptanceCriteria(
        strategy_class="MEAN_REVERSION",
        min_backtest_sharpe=1.4,
        min_profit_factor=1.7,
        max_backtest_drawdown_pct=12.0,
        min_oos_consistency_pct=70.0,
        max_monte_carlo_95_dd_pct=14.0,
        min_paper_trades=40,
    ),
    "BREAKOUT": ClassAcceptanceCriteria(
        strategy_class="BREAKOUT",
        min_backtest_sharpe=1.3,
        min_profit_factor=1.6,
        max_backtest_drawdown_pct=14.0,
        min_oos_consistency_pct=60.0,
        max_monte_carlo_95_dd_pct=15.0,
        min_paper_trades=30,
    ),
    "LIQUIDITY_REVERSAL": ClassAcceptanceCriteria(
        strategy_class="LIQUIDITY_REVERSAL",
        min_backtest_sharpe=1.4,
        min_profit_factor=1.7,
        max_backtest_drawdown_pct=12.0,
        min_oos_consistency_pct=70.0,
        max_monte_carlo_95_dd_pct=14.0,
        min_paper_trades=35,
    ),
    "CUSTOM": ClassAcceptanceCriteria(
        strategy_class="CUSTOM",
        min_backtest_sharpe=1.3,
        min_profit_factor=1.6,
        max_backtest_drawdown_pct=15.0,
        min_oos_consistency_pct=65.0,
        max_monte_carlo_95_dd_pct=15.0,
        min_paper_trades=30,
    ),
}


class StrategyPromotionManager:
    def __init__(self):
        self._strategy_registry: Dict[str, Dict[str, Any]] = {}

    def register_strategy(self, strategy_id: str, version: str, strategy_class: str, name: str):
        key = f"{strategy_id}:{version}"
        self._strategy_registry[key] = {
            "strategy_id": strategy_id,
            "version": version,
            "name": name,
            "strategy_class": strategy_class,
            "stage": PromotionStage.RESEARCH.value,
            "validation_history": [],
            "created_at_ist": format_ist_timestamp(),
        }

    def evaluate_promotion(
        self,
        strategy_id: str,
        version: str,
        backtest_metrics: Dict[str, float],
        walk_forward_metrics: Dict[str, float],
        monte_carlo_metrics: Dict[str, float],
        paper_trades_count: int = 0,
    ) -> Dict[str, Any]:
        key = f"{strategy_id}:{version}"
        record = self._strategy_registry.get(key)
        if not record:
            self.register_strategy(strategy_id, version, "CUSTOM", strategy_id)
            record = self._strategy_registry[key]

        strat_class = record["strategy_class"]
        criteria = CLASS_CRITERIA.get(strat_class, CLASS_CRITERIA["CUSTOM"])

        checklist = []
        # Gate 1: Backtest Sharpe
        sharpe = backtest_metrics.get("sharpe_ratio", 0.0)
        p_sharpe = sharpe >= criteria.min_backtest_sharpe
        checklist.append({"gate": "Backtest Sharpe", "threshold": criteria.min_backtest_sharpe, "actual": sharpe, "passed": p_sharpe})

        # Gate 2: Profit Factor
        pf = backtest_metrics.get("profit_factor", 0.0)
        p_pf = pf >= criteria.min_profit_factor
        checklist.append({"gate": "Profit Factor", "threshold": criteria.min_profit_factor, "actual": pf, "passed": p_pf})

        # Gate 3: Max Drawdown
        mdd = backtest_metrics.get("max_drawdown_pct", 100.0)
        p_mdd = mdd <= criteria.max_backtest_drawdown_pct
        checklist.append({"gate": "Max Drawdown (%)", "threshold": f"<={criteria.max_backtest_drawdown_pct}", "actual": mdd, "passed": p_mdd})

        # Gate 4: Walk-Forward Consistency
        oos_cons = walk_forward_metrics.get("oos_consistency_pct", 0.0)
        p_oos = oos_cons >= criteria.min_oos_consistency_pct
        checklist.append({"gate": "Walk-Forward OOS Consistency", "threshold": f">={criteria.min_oos_consistency_pct}%", "actual": oos_cons, "passed": p_oos})

        # Gate 5: Monte Carlo Worst-Case Drawdown
        mc_dd = monte_carlo_metrics.get("p95_worst_case_max_drawdown_pct", 100.0)
        p_mc = mc_dd <= criteria.max_monte_carlo_95_dd_pct
        checklist.append({"gate": "Monte Carlo 95% Worst DD", "threshold": f"<={criteria.max_monte_carlo_95_dd_pct}%", "actual": mc_dd, "passed": p_mc})

        # Gate 6: Paper Trades
        p_paper = paper_trades_count >= criteria.min_paper_trades
        checklist.append({"gate": "Paper Trading Sample", "threshold": f">={criteria.min_paper_trades} trades", "actual": paper_trades_count, "passed": p_paper})

        passed_all_quant_gates = p_sharpe and p_pf and p_mdd and p_oos and p_mc

        if passed_all_quant_gates and p_paper:
            next_stage = PromotionStage.APPROVED_FOR_LIVE.value
        elif passed_all_quant_gates:
            next_stage = PromotionStage.PAPER_TRADING.value
        elif p_sharpe and p_pf and p_mdd:
            next_stage = PromotionStage.IN_SAMPLE_BACKTEST.value
        else:
            next_stage = PromotionStage.RESEARCH.value

        record["stage"] = next_stage
        record["validation_checklist"] = checklist

        return {
            "strategy_id": strategy_id,
            "version": version,
            "current_stage": next_stage,
            "criteria": criteria.model_dump(),
            "checklist": checklist,
            "is_approved_for_paper": passed_all_quant_gates,
            "is_approved_for_live": passed_all_quant_gates and p_paper,
        }

    def list_all_promotions(self) -> List[Dict[str, Any]]:
        return list(self._strategy_registry.values())


promotion_manager = StrategyPromotionManager()
