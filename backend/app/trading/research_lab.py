"""
Dynamic Strategy Builder & Hypothesis Evaluator.
Allows creating, testing, and promoting custom rule-based strategies.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from pydantic import BaseModel, Field
from app.trading.strategies import QuantitativeStrategy, StrategySignalResult
from app.trading.regime import classify_market_regime


class RuleCondition(BaseModel):
    indicator_a: str  # e.g., "ema_20", "close", "rsi_14", "adx_14"
    operator: str    # ">", "<", ">=", "<=", "BETWEEN", "=="
    indicator_b: Optional[str] = None  # e.g., "ema_50"
    constant_value: Optional[float] = None
    min_value: Optional[float] = None  # For BETWEEN
    max_value: Optional[float] = None  # For BETWEEN


class CustomStrategyDefinition(BaseModel):
    strategy_id: str
    version: str = "v1.0.0"
    name: str
    description: str = ""
    strategy_class: str = "CUSTOM"
    entry_side: str = "BUY"  # BUY or SELL
    entry_rules: List[RuleCondition] = Field(default_factory=list)
    sl_atr_multiplier: float = 1.5
    tp_atr_multiplier: float = 3.0
    allowed_regimes: List[str] = Field(default_factory=list)
    forbidden_regimes: List[str] = Field(default_factory=list)


class CustomDynamicStrategy(QuantitativeStrategy):
    def __init__(self, definition: CustomStrategyDefinition):
        self.definition = definition
        self.strategy_id = definition.strategy_id
        self.version = definition.version
        self.name = definition.name
        self.strategy_class = definition.strategy_class
        self.allowed_regimes = definition.allowed_regimes or [
            "STRONG_BULLISH_TREND", "WEAK_BULLISH_TREND", "SIDEWAYS_RANGE", "HIGH_VOLATILITY"
        ]
        self.forbidden_regimes = definition.forbidden_regimes or []
        self.sl_atr_multiplier = definition.sl_atr_multiplier
        self.tp_atr_multiplier = definition.tp_atr_multiplier

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 50:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        latest = df.iloc[-1]
        close = float(latest["close"])
        atr_14 = float(latest.get("atr_14", close * 0.01))

        checklist = []
        all_passed = True

        for rule in self.definition.entry_rules:
            passed = self._eval_rule(latest, rule)
            rule_str = f"{rule.indicator_a} {rule.operator} {rule.indicator_b or rule.constant_value or f'[{rule.min_value}, {rule.max_value}]'}"
            checklist.append({"rule": rule_str, "passed": passed})
            if not passed:
                all_passed = False

        if not all_passed or not self.definition.entry_rules:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        side = self.definition.entry_side.upper()
        if side == "BUY":
            sl = round(close - (self.sl_atr_multiplier * atr_14), 5)
            tp = round(close + (self.tp_atr_multiplier * atr_14), 5)
            rr = round((tp - close) / max(1e-5, (close - sl)), 2)
        else:
            sl = round(close + (self.sl_atr_multiplier * atr_14), 5)
            tp = round(close - (self.tp_atr_multiplier * atr_14), 5)
            rr = round((close - tp) / max(1e-5, (sl - close)), 2)

        veto_reasons = []
        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=checklist,
            veto_reasons=veto_reasons,
        )

    def _eval_rule(self, row: pd.Series, rule: RuleCondition) -> bool:
        val_a = float(row.get(rule.indicator_a, 0.0))
        if rule.operator == "BETWEEN" and rule.min_value is not None and rule.max_value is not None:
            return rule.min_value <= val_a <= rule.max_value

        val_b = float(row.get(rule.indicator_b, 0.0)) if rule.indicator_b else (rule.constant_value or 0.0)

        if rule.operator == ">":
            return val_a > val_b
        elif rule.operator == "<":
            return val_a < val_b
        elif rule.operator == ">=":
            return val_a >= val_b
        elif rule.operator == "<=":
            return val_a <= val_b
        elif rule.operator == "==":
            return abs(val_a - val_b) < 1e-5
        return False
