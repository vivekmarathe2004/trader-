"""Trading package."""
from app.trading.regime import MarketRegime, classify_market_regime
from app.trading.strategies import (
    QuantitativeStrategy, StrategySignalResult, ALL_QUANT_STRATEGIES,
    SupertrendTrendFollowingStrategy, SupportResistanceBreakoutStrategy,
    QuadEMATrendAlignmentStrategy, LiquiditySweepWickReversalStrategy,
    RSIBollingerMeanReversionStrategy, StatisticalArbitrageZScoreStrategy
)
from app.trading.pattern_engine import detect_candlestick_patterns
from app.trading.no_trade import no_trade_engine
from app.trading.confluence import confluence_engine
from app.trading.provenance import build_provenance_snapshot
from app.trading.research_lab import CustomStrategyDefinition, CustomDynamicStrategy, RuleCondition
from app.trading.auto_trader import auto_trader
