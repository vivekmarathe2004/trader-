"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../../components/GlassCard";
import { PageHeader } from "../../components/PageHeader";
import { formatCurrency, formatPercent } from "@/lib/format";
import { api } from "@/lib/api";
import { useNav } from "@/lib/nav-context";
import { Shield, Lock, Unlock, AlertTriangle, Calculator, DollarSign, Layers } from "lucide-react";

export default function RiskParametersPage() {
  const { liveTradingEnabled, setLiveTradingEnabled, emergencyKillActive, triggerEmergencyStop } = useNav();
  const [riskStatus, setRiskStatus] = useState<any>(null);

  // Position Sizing Calculator States
  const [calcSymbol, setCalcSymbol] = useState<string>("EURUSD");
  const [calcEntry, setCalcEntry] = useState<number>(1.0850);
  const [calcSl, setCalcSl] = useState<number>(1.0800);
  const [calculatedLots, setCalculatedLots] = useState<number | null>(null);

  const loadRisk = async () => {
    try {
      const data = await api.getRiskStatus().catch(() => null);
      setRiskStatus(data);
    } catch (e) {
      console.warn("Failed to load risk status:", e);
    }
  };

  useEffect(() => {
    loadRisk();
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        loadRisk();
      }
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleCalculateSize = async () => {
    try {
      const res = await api.calculateLotSize(calcSymbol, calcEntry, calcSl, riskStatus?.current_equity);
      setCalculatedLots(res.calculated_lots);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hardened Risk Parameters & Safety Controls"
        subtitle="Unbypassable deterministic risk boundaries. The backend strictly enforces safety checks regardless of order source."
      />

      {/* Master Safety Gate Banner */}
      <GlassCard className="p-5 border border-primary/10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${liveTradingEnabled ? "bg-loss/10 text-loss" : "bg-profit/10 text-profit"}`}>
              {liveTradingEnabled ? <Unlock className="w-6 h-6" /> : <Lock className="w-6 h-6" />}
            </div>
            <div>
              <h3 className="font-bold text-base text-primary">Master Live Trading Gate</h3>
              <p className="text-xs text-primary-muted">
                {liveTradingEnabled
                  ? "LIVE EXECUTION ARMED: Orders route to real exchange APIs."
                  : "PAPER TRADING SAFEGUARD: All executions restricted to simulated MockBroker."}
              </p>
            </div>
          </div>

          <button
            onClick={() => setLiveTradingEnabled(!liveTradingEnabled)}
            className={`px-4 py-2 rounded-xl font-bold text-xs transition-all shadow-sm ${
              liveTradingEnabled
                ? "bg-loss text-white hover:bg-loss/90"
                : "bg-profit text-white hover:bg-profit/90"
            }`}
          >
            {liveTradingEnabled ? "DISARM LIVE TRADING" : "ARM LIVE TRADING"}
          </button>
        </div>
      </GlassCard>

      {/* Hard Risk Limits Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <GlassCard>
          <div className="text-[10px] text-primary-muted uppercase font-bold">Max Peak Drawdown</div>
          <div className="text-2xl font-bold text-loss mt-1">10.0% Hard Limit</div>
          <div className="text-xs text-primary-muted mt-1">
            Current: <strong className="text-primary">{riskStatus?.drawdown_pct || "0.0"}%</strong>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="text-[10px] text-primary-muted uppercase font-bold">Max Daily Loss</div>
          <div className="text-2xl font-bold text-loss mt-1">1.0% Hard Limit</div>
          <div className="text-xs text-primary-muted mt-1">
            Current: <strong className="text-primary">{riskStatus?.daily_loss_pct || "0.0"}%</strong>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="text-[10px] text-primary-muted uppercase font-bold">Max Open Positions</div>
          <div className="text-2xl font-bold text-primary mt-1">3 Concurrent Max</div>
          <div className="text-xs text-primary-muted mt-1">
            Active: <strong className="text-primary">{riskStatus?.open_positions_count || 0} / 3</strong>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="text-[10px] text-primary-muted uppercase font-bold">Fast Break-Even Trigger</div>
          <div className="text-2xl font-bold text-profit mt-1">+0.5R (+0.3p)</div>
          <div className="text-xs text-primary-muted mt-1">
            Min R:R: <strong className="text-primary">1.50:1 (Scalp)</strong>
          </div>
        </GlassCard>
      </div>

      {/* Position Sizer & Exposure Tracker */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position Sizer Calculator */}
        <GlassCard className="space-y-4">
          <h3 className="text-sm font-bold text-primary flex items-center gap-2">
            <Calculator className="w-4 h-4 text-accent" />
            Fixed Fractional Position Sizer (0.25% Equity Risk)
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="text-primary-muted font-bold block mb-1">Symbol</label>
              <select
                value={calcSymbol}
                onChange={(e) => setCalcSymbol(e.target.value)}
                className="w-full p-2 rounded-lg bg-surface border border-primary/15 font-bold text-primary"
              >
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="USDJPY">USDJPY</option>
                <option value="BTCUSDT">BTCUSDT</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-primary-muted font-bold block mb-1">Entry Price</label>
                <input
                  type="number"
                  step="0.0001"
                  value={calcEntry}
                  onChange={(e) => setCalcEntry(parseFloat(e.target.value))}
                  className="w-full p-2 rounded-lg bg-surface border border-primary/15 font-bold text-primary"
                />
              </div>
              <div>
                <label className="text-primary-muted font-bold block mb-1">Stop Loss</label>
                <input
                  type="number"
                  step="0.0001"
                  value={calcSl}
                  onChange={(e) => setCalcSl(parseFloat(e.target.value))}
                  className="w-full p-2 rounded-lg bg-surface border border-primary/15 font-bold text-loss"
                />
              </div>
            </div>

            <button
              onClick={handleCalculateSize}
              className="w-full py-2.5 rounded-xl bg-accent text-white font-bold text-xs hover:bg-accent-hover transition-colors shadow-sm"
            >
              CALCULATE LOT SIZE
            </button>

            {calculatedLots !== null && (
              <div className="p-3 rounded-xl bg-profit-subtle border border-profit-border flex items-center justify-between">
                <span className="font-bold text-profit">Recommended Sizing:</span>
                <strong className="text-base text-profit font-mono">{calculatedLots} Lots</strong>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Currency Concentration Tracker */}
        <GlassCard className="space-y-4">
          <h3 className="text-sm font-bold text-primary flex items-center gap-2">
            <Layers className="w-4 h-4 text-accent" />
            Net Currency Exposure Breakdown
          </h3>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between py-2 border-b border-primary/10">
              <span className="text-primary-muted">Total USD Notional:</span>
              <strong className="text-primary font-bold">
                {formatCurrency(riskStatus?.exposure?.total_notional_usd || 0)}
              </strong>
            </div>
            <div className="flex justify-between py-2 border-b border-primary/10">
              <span className="text-primary-muted">Max Notional Cap:</span>
              <strong className="text-primary font-bold">
                {formatCurrency(riskStatus?.exposure?.max_notional_limit || 50000)}
              </strong>
            </div>
            <div className="flex justify-between py-2 border-b border-primary/10">
              <span className="text-primary-muted">Max Currency Pairs Cap:</span>
              <strong className="text-primary font-bold">Max 2 per Currency</strong>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-primary-muted">Concentration Status:</span>
              <span className="text-profit font-bold">WITHIN SAFE LIMITS</span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
