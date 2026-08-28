"""
Tests for Event-Driven Backtesting, Walk-Forward Validation, and Monte Carlo Simulation.
"""
import pytest
from app.trading.strategies import ALL_QUANT_STRATEGIES
from app.backtesting.engine import backtest_engine
from app.backtesting.walk_forward import walk_forward_engine
from app.backtesting.monte_carlo import monte_carlo_engine
from app.backtesting.sensitivity import sensitivity_analyzer
from app.backtesting.regime_analysis import regime_analyzer
from app.backtesting.stress_testing import stress_tester


def test_event_driven_backtest():
    strat = ALL_QUANT_STRATEGIES[0]
    res = backtest_engine.run_backtest(strat, "EURUSD", bars_count=300)
    assert "metrics" in res
    assert "equity_curve" in res
    assert len(res["equity_curve"]) >= 1


def test_walk_forward_optimization():
    strat = ALL_QUANT_STRATEGIES[0]
    wf = walk_forward_engine.run_walk_forward(strat, "EURUSD", windows_count=3, bars_per_window=100)
    assert "windows_count" in wf
    assert len(wf["window_results"]) == 3
    assert "average_oos_return_pct" in wf


def test_monte_carlo_resampling():
    strat = ALL_QUANT_STRATEGIES[0]
    mc = monte_carlo_engine.run_monte_carlo(strat, "EURUSD", iterations=100)
    assert "confidence_metrics" in mc
    assert "p95_worst_case_max_drawdown_pct" in mc["confidence_metrics"]


def test_parameter_sensitivity_studio():
    sens = sensitivity_analyzer.analyze_atr_sl_tp_sensitivity(
        strategy_id=ALL_QUANT_STRATEGIES[0].strategy_id,
        symbol="EURUSD",
        sl_multipliers=[1.2, 1.5],
        tp_multipliers=[2.5, 3.0],
    )
    assert "grid_results" in sens
    assert len(sens["grid_results"]) == 2


def test_regime_performance_analysis():
    reg = regime_analyzer.evaluate_regime_breakdown(
        strategy_id=ALL_QUANT_STRATEGIES[0].strategy_id,
        symbol="EURUSD",
    )
    assert "regime_breakdown" in reg


def test_stress_testing_suite():
    stress = stress_tester.run_stress_suite(
        strategy_id=ALL_QUANT_STRATEGIES[0].strategy_id,
        symbol="EURUSD",
    )
    assert "scenarios" in stress
    assert len(stress["scenarios"]) == 6
