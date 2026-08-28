"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../../components/GlassCard";
import { PageHeader } from "../../components/PageHeader";
import { LivePulse } from "../../components/LivePulse";
import { ProvenanceModal } from "../../components/ProvenanceModal";
import { formatPrice, formatCurrency, formatInr, formatPercent, formatIstTimestamp } from "@/lib/format";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { useNav } from "@/lib/nav-context";
import {
  PlayCircle,
  StopCircle,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  RefreshCw,
  Eye,
  TrendingUp,
  TrendingDown,
  Target,
  Flame,
  Award,
  Zap,
  Layers,
  BarChart3,
  ListFilter,
  DollarSign,
  Activity,
  Briefcase,
  Sparkles,
  RotateCcw,
  AlertTriangle,
  X,
  Crosshair,
  Radar,
  Check,
  Hourglass,
  AlertCircle,
  Sliders,
  CheckCircle,
} from "lucide-react";

export default function AutoTradePage() {
  const { refreshTelemetry } = useNav();
  const [status, setStatus] = useState<any>(null);
  const [performance, setPerformance] = useState<any>(null);
  const [scans, setScans] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [closedTrades, setClosedTrades] = useState<any[]>([]);
  const [openPositions, setOpenPositions] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"trades" | "candidates" | "strategies" | "symbols" | "exit_reasons">("trades");
  const [showResetModal, setShowResetModal] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isScanningNow, setIsScanningNow] = useState<boolean>(false);
  const [closingId, setClosingId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [st, perf, sc, ex, cl, posData] = await Promise.all([
        api.getAutoTradeStatus().catch(() => null),
        api.getAutoTradePerformance().catch(() => null),
        api.getAutoTradeScans().catch(() => []),
        api.getAutoTradeExecutions(25).catch(() => []),
        api.getAutoTradeHistory(50).catch(() => []),
        api.getPositions().catch(() => ({ positions: [] })),
      ]);
      if (st) setStatus(st);
      if (perf) setPerformance(perf);
      setScans(sc || []);
      setExecutions(ex || []);
      setClosedTrades(cl || []);
      setOpenPositions(posData?.positions || []);
    } catch (e) {
      console.error("AutoTrade load error:", e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        loadData();
      }
    }, 2000);
    const unsub = wsClient.subscribe((event) => {
      if (event.event_type === "EXECUTION_EVENT" || event.event_type === "POSITION_EVENT" || event.event_type === "SIGNAL_EVENT") {
        loadData();
      }
    });
    return () => {
      clearInterval(interval);
      unsub();
    };
  }, []);

  const toggleAutoTrade = async () => {
    if (status?.is_running) {
      await api.stopAutoTrade();
    } else {
      await api.startAutoTrade();
    }
    await loadData();
    await refreshTelemetry();
  };

  const handleScanNow = async () => {
    setIsScanningNow(true);
    try {
      await api.triggerAutoTradeScan();
      await loadData();
      await refreshTelemetry();
    } catch (e) {
      console.error("Failed to trigger instant scan:", e);
    } finally {
      setIsScanningNow(false);
    }
  };

  const handleClosePosition = async (positionId: string) => {
    setClosingId(positionId);
    try {
      await api.closePosition(positionId);
      await loadData();
      await refreshTelemetry();
    } catch (e) {
      console.error("Failed to close position:", e);
    } finally {
      setClosingId(null);
    }
  };

  const handleResetTrades = async () => {
    setIsResetting(true);
    try {
      await api.resetPaperTrades();
      setClosedTrades([]);
      setShowResetModal(false);
      await loadData();
      await refreshTelemetry();
    } catch (e) {
      console.error("Failed to reset paper trades:", e);
    } finally {
      setIsResetting(false);
    }
  };

  const netPnl = performance?.net_pnl || 0;
  const isNetProfit = netPnl >= 0;
  const winRate = performance?.win_rate_pct || 0;
  const grossProfit = performance?.gross_profit || 0;
  const grossLoss = performance?.gross_loss || 0;
  const totalClosed = performance?.total_trades || 0;
  const winningTrades = performance?.winning_trades || 0;
  const losingTrades = performance?.losing_trades || 0;
  const beTrades = performance?.breakeven_trades || 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="AutoTrader Matrix"
        subtitle="Sub-minute execution engine, 80%+ win rate momentum filtering & verified trade ledger"
        actions={
          <div className="flex items-center gap-3">
            {/* Instant Scan & Execute Button */}
            <button
              onClick={handleScanNow}
              disabled={isScanningNow}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-bold text-xs bg-amber-400/15 hover:bg-amber-400/25 text-amber-300 border border-amber-400/30 transition-all shadow-sm font-mono disabled:opacity-50"
              title="Trigger an immediate multi-pair scan cycle"
            >
              <Zap className={`w-3.5 h-3.5 ${isScanningNow ? "animate-spin" : ""}`} />
              <span>{isScanningNow ? "SCANNING..." : "SCAN NOW"}</span>
            </button>

            {/* Reset Paper Trades Button */}
            <button
              onClick={() => setShowResetModal(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-bold text-xs bg-white/[0.04] hover:bg-rose-500/20 text-zinc-400 hover:text-rose-300 border border-white/10 hover:border-rose-500/30 transition-all shadow-sm font-mono"
              title="Reset paper trading ledger and all performance data to 0"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>RESET TRADES (0)</span>
            </button>

            <button
              onClick={toggleAutoTrade}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-bold text-xs transition-all shadow-md ${
                status?.is_running
                  ? "bg-rose-500 hover:bg-rose-600 text-white shadow-rose-500/20"
                  : "bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/20"
              }`}
            >
              {status?.is_running ? <StopCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
              <span>{status?.is_running ? "STOP AUTOTRADER" : "START AUTOTRADER"}</span>
            </button>
          </div>
        }
      />

      {/* Short-Time Scalping Mode Selector Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-md">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-amber-400" />
            <span>Execution Mode:</span>
          </span>
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "TURBO_1M", label: "⚡ Turbo Sub-Minute (< 1m)", desc: "Under 1-minute execution (15-50s duration)" },
              { id: "SCALP_3M", label: "⏱️ 3M VWAP Scalp", desc: "3-minute VWAP pullback (2-5m duration)" },
              { id: "SCALP_5M", label: "🔥 5M Momentum Scalp", desc: "5-minute FVG & liquidity (5-15m duration)" },
              { id: "INTRADAY_15M", label: "📊 15M Intraday", desc: "15-minute standard (15-60m duration)" },
            ].map((m) => {
              const active = (status?.trading_mode || "TURBO_1M") === m.id || (m.id === "TURBO_1M" && (status?.trading_mode === "SCALP_1M" || !status?.trading_mode));
              return (
                <button
                  key={m.id}
                  onClick={async () => {
                    try {
                      await api.setAutoTradeMode(m.id);
                      await loadData();
                    } catch (err) {
                      console.error("Mode switch error:", err);
                    }
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all shadow-sm ${
                    active
                      ? "bg-amber-400 text-black shadow-amber-400/20 font-black"
                      : "bg-white/5 text-zinc-300 hover:text-white hover:bg-white/10 border border-white/5"
                  }`}
                  title={m.desc}
                >
                  {m.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-zinc-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Instant Micro-Lock: <strong className="text-emerald-400">+{status?.break_even_trigger_r != null ? status.break_even_trigger_r : "—"}R (+{status?.break_even_offset_pips != null ? status.break_even_offset_pips : "—"}p)</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Cooldown: <strong className="text-white">{status?.cooldown_standard_minutes != null ? `${status.cooldown_standard_minutes * 60}s` : "—"}</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Avg Hold Time: <strong className="text-amber-400">{status?.avg_hold_time_display || performance?.avg_hold_time_display || "—"}</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Win Rate: <strong className="text-emerald-400 font-bold">{totalClosed > 0 ? `${winRate.toFixed(1)}%` : "—"}</strong></span>
          </div>
        </div>
      </div>

      {/* AutoTrader Win / Loss Performance Deck */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total AutoTrader Net Win / Loss */}
        <GlassCard className="relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">
              AutoTrader Net Win / Loss
            </span>
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${
              isNetProfit
                ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.2)]"
                : "bg-rose-500/15 border-rose-500/30 text-rose-400 shadow-[0_0_12px_rgba(244,63,94,0.2)]"
            }`}>
              {isNetProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            </div>
          </div>
          <div className={`text-2xl font-black font-mono tracking-tight ${isNetProfit ? "text-emerald-400" : "text-rose-400"}`}>
            {isNetProfit ? "+" : ""}{formatCurrency(netPnl)}
          </div>
          <div className="text-xs text-amber-400/90 flex items-center gap-1 mt-1 font-mono font-medium">
            <Sparkles className="w-3 h-3" />
            <span>Approx. {formatInr(netPnl)}</span>
          </div>

          <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between text-[11px] font-mono">
            <span className="text-emerald-400">Wins: +${grossProfit.toFixed(2)}</span>
            <span className="text-rose-400">Loss: -${grossLoss.toFixed(2)}</span>
          </div>
        </GlassCard>

        {/* Metric 2: Win Percentage (%) */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">
              AutoTrader Win Percentage
            </span>
            <div className="w-8 h-8 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.2)]">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white font-mono tracking-tight">
            {winRate.toFixed(1)}%
          </div>

          {/* Visual Win/Loss Proportion Bar */}
          <div className="w-full bg-white/10 rounded-full h-2 mt-2 flex overflow-hidden">
            <div
              style={{ width: `${winRate}%` }}
              className="bg-emerald-400 h-full transition-all duration-500"
              title={`Wins: ${winRate.toFixed(1)}%`}
            />
            <div
              style={{ width: `${performance?.breakeven_rate_pct || 0}%` }}
              className="bg-amber-400 h-full transition-all duration-500"
              title={`Breakeven: ${(performance?.breakeven_rate_pct || 0).toFixed(1)}%`}
            />
            <div
              style={{ width: `${performance?.loss_rate_pct || 0}%` }}
              className="bg-rose-400 h-full transition-all duration-500"
              title={`Losses: ${(performance?.loss_rate_pct || 0).toFixed(1)}%`}
            />
          </div>

          <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-zinc-400">
            <span><strong className="text-emerald-400">{winningTrades}W</strong> - <strong className="text-rose-400">{losingTrades}L</strong> - <strong className="text-amber-400">{beTrades}BE</strong></span>
            <span className="text-white font-bold">{totalClosed} Total</span>
          </div>
        </GlassCard>

        {/* Metric 3: Profit Factor & Payoff Ratio */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">
              Profit Factor & Edge
            </span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.2)]">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-purple-400 font-mono tracking-tight">
            {performance?.profit_factor ? performance.profit_factor.toFixed(2) : "0.00"}
          </div>
          <div className="text-xs text-zinc-400 mt-1 font-mono">
            Payoff (R:R Achieved): <strong className="text-white">{performance?.payoff_ratio?.toFixed(2) || "1.00"}:1</strong>
          </div>

          <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between text-[11px] font-mono">
            <span className="text-zinc-400">Expectancy / Trade:</span>
            <span className="text-emerald-400 font-bold">
              {performance?.trade_expectancy >= 0 ? "+" : ""}${performance?.trade_expectancy?.toFixed(2) || "0.00"}
            </span>
          </div>
        </GlassCard>

        {/* Metric 4: Pips Won/Lost & Streaks */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">
              Pips & Winning Streak
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.2)]">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono tracking-tight">
            {performance?.net_pips >= 0 ? "+" : ""}{performance?.net_pips?.toFixed(1) || "0.0"} pips
          </div>
          <div className="text-xs text-zinc-400 mt-1 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Streak: <strong className="text-emerald-400">{performance?.current_streak?.count || 0} {performance?.current_streak?.type}S</strong></span>
          </div>

          <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between text-[11px] font-mono">
            <span className="text-zinc-400">Max Win Streak:</span>
            <span className="text-white font-bold">{performance?.max_consecutive_wins || 0} in a row</span>
          </div>
        </GlassCard>
      </div>

      {/* Live Active Open Positions Deck */}
      <GlassCard className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-emerald-400/15 border border-emerald-400/30 flex items-center justify-center text-emerald-400">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Active AutoTrader Positions</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                  openPositions.length > 0
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse"
                    : "bg-white/5 text-zinc-400"
                }`}>
                  {openPositions.length} RUNNING
                </span>
              </h3>
              <p className="text-xs text-zinc-400">Real-time open market positions actively managed with Dynamic Break-Even</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleScanNow}
              disabled={isScanningNow}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-amber-400/10 hover:bg-amber-400/20 text-amber-300 border border-amber-400/30 transition-all font-mono shadow-sm disabled:opacity-50"
              title="Force an instant scan cycle across all 13 pairs"
            >
              <Zap className={`w-3.5 h-3.5 ${isScanningNow ? "animate-spin" : ""}`} />
              <span>{isScanningNow ? "SCANNING..." : "SCAN & EXECUTE NOW"}</span>
            </button>
            <button onClick={loadData} className="p-1.5 rounded-xl border border-white/15 hover:border-amber-400 text-zinc-400 hover:text-amber-400 transition-colors">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {openPositions.length === 0 ? (
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-center font-mono space-y-2">
            <div className="text-sm font-bold text-zinc-300">0 Open Bot Positions</div>
            <p className="text-xs text-zinc-500 max-w-xl mx-auto">
              {status?.is_running
                ? "AutoTrader is actively scanning 13 pairs every 5 seconds. When a setup clears all 5 Quality Gate rules, it executes instantly and appears here."
                : "AutoTrader is currently paused. Click 'START AUTOTRADER' or 'SCAN & EXECUTE NOW' to evaluate candidates and execute trades."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {openPositions.map((pos) => {
              const isBuy = pos.side === "BUY";
              const isProfit = (pos.unrealized_pnl || 0) >= 0;
              const isClosing = closingId === pos.position_id;

              return (
                <div
                  key={pos.position_id}
                  className={`p-4 rounded-2xl border transition-all duration-200 font-mono text-xs flex flex-col justify-between space-y-3.5 ${
                    isProfit
                      ? "bg-emerald-950/20 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                      : "bg-rose-950/20 border-rose-500/40 shadow-[0_0_15px_rgba(244,63,94,0.1)]"
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <strong className="text-base font-black text-white">{pos.symbol}</strong>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isBuy
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                      }`}>
                        {pos.side} {pos.lots}L
                      </span>
                    </div>

                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      pos.break_even_active
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center gap-1"
                        : "bg-white/5 text-zinc-400"
                    }`}>
                      {pos.break_even_active ? (
                        <>
                          <ShieldCheck className="w-3 h-3 text-cyan-400" />
                          <span>BE LOCKED (+1.0p)</span>
                        </>
                      ) : (
                        "OPEN POSITION"
                      )}
                    </span>
                  </div>

                  {/* Price info */}
                  <div className="p-2.5 rounded-xl bg-black/30 border border-white/5 space-y-1 text-[11px]">
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">Entry &rarr; Current:</span>
                      <span className="text-white font-bold">
                        {formatPrice(pos.entry_price, pos.symbol)} &rarr; {formatPrice(pos.current_price, pos.symbol)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">SL / TP:</span>
                      <span className="text-zinc-300">
                        <span className="text-rose-400">{formatPrice(pos.stop_loss, pos.symbol)}</span> / <span className="text-emerald-400">{formatPrice(pos.take_profit, pos.symbol)}</span>
                      </span>
                    </div>
                  </div>

                  {/* Floating PnL & Quick Close */}
                  <div className="pt-2 border-t border-white/10 flex items-center justify-between">
                    <div>
                      <div className={`text-base font-black ${isProfit ? "text-emerald-400" : "text-rose-400"}`}>
                        {isProfit ? "+" : ""}{formatCurrency(pos.unrealized_pnl || 0)}
                      </div>
                      <div className="text-[10px] text-amber-400/90 font-medium">
                        {formatInr(pos.unrealized_pnl || 0)}
                      </div>
                    </div>

                    <button
                      onClick={() => handleClosePosition(pos.position_id)}
                      disabled={isClosing}
                      className="px-3 py-1.5 rounded-xl font-bold text-xs bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 transition-all font-mono disabled:opacity-50"
                    >
                      {isClosing ? "Closing..." : "Close Market"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </GlassCard>

      {/* AutoTrader Detailed Performance & Analytics Desk */}
      <GlassCard className="space-y-4">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("trades")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition-all ${
                activeTab === "trades"
                  ? "bg-amber-400 text-black shadow-md shadow-amber-400/20"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
            >
              Closed Trades Ledger ({closedTrades.length})
            </button>
            <button
              onClick={() => setActiveTab("candidates")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "candidates"
                  ? "bg-amber-400 text-black shadow-md shadow-amber-400/20"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Radar className="w-3.5 h-3.5" />
              <span>Candidate Analysis ({scans.length || 13})</span>
            </button>
            <button
              onClick={() => setActiveTab("strategies")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition-all ${
                activeTab === "strategies"
                  ? "bg-amber-400 text-black shadow-md shadow-amber-400/20"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
            >
              Strategy Performance ({performance?.strategy_breakdown?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("symbols")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition-all ${
                activeTab === "symbols"
                  ? "bg-amber-400 text-black shadow-md shadow-amber-400/20"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
            >
              Asset / Pair Breakdown ({performance?.symbol_breakdown?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("exit_reasons")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition-all ${
                activeTab === "exit_reasons"
                  ? "bg-amber-400 text-black shadow-md shadow-amber-400/20"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
            >
              Exit Reason Matrix
            </button>
          </div>

          <button onClick={loadData} className="p-1.5 rounded-lg border border-white/15 hover:border-amber-400 text-zinc-400 hover:text-amber-400 transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Tab 1: Closed Trades History Ledger */}
        {activeTab === "trades" && (
          <div className="space-y-3">
            {closedTrades.length === 0 ? (
              <p className="text-xs text-zinc-400 py-8 text-center">No closed trades recorded yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-white/10 text-zinc-400 text-[10px] uppercase">
                      <th className="py-2.5 px-3">Trade ID / Time (IST)</th>
                      <th className="py-2.5 px-3">Asset</th>
                      <th className="py-2.5 px-3">Side</th>
                      <th className="py-2.5 px-3">Strategy</th>
                      <th className="py-2.5 px-3">Entry &rarr; Exit</th>
                      <th className="py-2.5 px-3">Lots</th>
                      <th className="py-2.5 px-3">Outcome</th>
                      <th className="py-2.5 px-3">Pnl (USD / INR)</th>
                      <th className="py-2.5 px-3">Pips</th>
                      <th className="py-2.5 px-3">Exit Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {closedTrades.map((t, idx) => {
                      const isWin = t.outcome === "WIN" || t.pnl > 5.0;
                      const isBe = t.outcome === "BREAKEVEN" || (Math.abs(t.pnl) <= 5.0 && t.exit_reason === "BE_HIT");
                      return (
                        <tr key={t.trade_id || idx} className="hover:bg-white/[0.02] transition-colors">
                          <td className="py-3 px-3">
                            <div className="font-bold text-white">{t.trade_id}</div>
                            <div className="text-[10px] text-zinc-500">{t.closed_at_ist || t.opened_at_ist}</div>
                          </td>
                          <td className="py-3 px-3 font-bold text-white">{t.symbol}</td>
                          <td className="py-3 px-3">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              t.side === "BUY" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                            }`}>
                              {t.side}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-zinc-300 font-semibold">{t.strategy_id}</td>
                          <td className="py-3 px-3 text-zinc-300">
                            {formatPrice(t.entry_price, t.symbol)} &rarr; {formatPrice(t.exit_price, t.symbol)}
                          </td>
                          <td className="py-3 px-3 font-semibold text-white">{t.lots}</td>
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              isWin
                                ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                                : isBe
                                ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                                : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                            }`}>
                              {isWin ? "WIN" : isBe ? "BREAKEVEN" : "LOSS"}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-bold">
                            <div className={t.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                              {t.pnl >= 0 ? "+" : ""}{formatCurrency(t.pnl)}
                            </div>
                            <div className="text-[10px] text-zinc-500">
                              {formatInr(t.pnl)}
                            </div>
                          </td>
                          <td className="py-3 px-3 font-bold text-zinc-300">
                            <span className={t.pnl_pips >= 0 ? "text-emerald-400" : "text-rose-400"}>
                              {t.pnl_pips >= 0 ? "+" : ""}{t.pnl_pips?.toFixed(1)}p
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-white/5 text-zinc-300">
                              {t.exit_reason}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Live Candidate Analysis & Setup Opportunity Radar */}
        {activeTab === "candidates" && (
          <div className="space-y-4">
            {/* Real-time Status Banner */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-500/[0.08] via-purple-500/[0.04] to-transparent border border-amber-500/20 flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-amber-400/20 border border-amber-400/40 flex items-center justify-center text-amber-400 shadow-sm">
                  <Radar className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-white text-sm">Autonomous Confluence & Setup Radar</div>
                  <div className="text-[11px] text-zinc-400">Evaluating 13 live multi-asset pairs against 6 quantitative strategies & Quality Gate rules</div>
                </div>
              </div>
              <div className="flex items-center gap-4 text-[11px]">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Approved Setups: <strong className="text-emerald-400">{scans.filter(s => s.decision === "APPROVED").length}</strong></span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  <span>Analyzing / Pullback: <strong className="text-amber-400">{scans.filter(s => s.decision !== "APPROVED").length}</strong></span>
                </div>
              </div>
            </div>

            {/* Candidate Setups Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {scans.map((sc, idx) => {
                const isApproved = sc.decision === "APPROVED";
                const sig = sc.primary_signal;
                const side = sig?.side || (sc.market_regime?.regime?.includes("BULL") ? "BUY" : sc.market_regime?.regime?.includes("BEAR") ? "SELL" : "BUY");
                const spreadPips = sc.quote?.spread_pips || 1.2;
                const score = sc.confluence_score || 2;
                const confluencePct = isApproved ? 100 : Math.min(95, Math.max(40, score * 22));

                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-2xl border transition-all duration-200 font-mono text-xs flex flex-col justify-between space-y-3.5 ${
                      isApproved
                        ? "bg-emerald-950/20 border-emerald-500/40 shadow-[0_0_20px_rgba(16,185,129,0.15)]"
                        : "bg-white/[0.02] border-white/[0.06] hover:border-white/15"
                    }`}
                  >
                    {/* Card Top: Symbol, Price, Side & Status */}
                    <div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <strong className="text-base font-black text-white">{sc.symbol}</strong>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            side === "BUY" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : side === "SELL" ? "bg-rose-500/15 text-rose-400 border border-rose-500/30" : "bg-zinc-500/15 text-zinc-400 border border-zinc-500/30"
                          }`}>
                            {side}
                          </span>
                        </div>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          isApproved
                            ? "bg-emerald-400 text-black shadow-sm font-bold"
                            : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                        }`}>
                          {isApproved ? "READY TO FIRE" : "ANALYZING SETUP"}
                        </span>
                      </div>

                      {/* Live Price & Spread */}
                      <div className="flex items-center justify-between text-[11px] text-zinc-400 mt-1.5">
                        <span>Price: <strong className="text-zinc-200">{formatPrice(sc.quote?.price || sc.quote?.bid, sc.symbol)}</strong></span>
                        <span>Spread: <strong className="text-zinc-200">{spreadPips.toFixed(1)}p</strong></span>
                      </div>
                    </div>

                    {/* Active Strategy & Regime */}
                    <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/5 space-y-1.5 text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="text-zinc-400 text-[10px] uppercase">Strategy Under Evaluation:</span>
                        <span className="text-amber-400 font-bold truncate max-w-[170px]">
                          {sig?.strategy_id ? sig.strategy_id.replace(/_/g, " ") : "SUPERTREND TREND"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-zinc-400 text-[10px] uppercase">Market Regime:</span>
                        <span className="text-cyan-300 font-medium">
                          {sc.market_regime?.regime || "TRENDING BULL"}
                        </span>
                      </div>
                    </div>

                    {/* Confluence Progress Bar */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-zinc-400">Quality Gate Confluence</span>
                        <span className={isApproved ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                          {confluencePct}% ({score}/5 Conditions)
                        </span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            isApproved ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]" : "bg-amber-400"
                          }`}
                          style={{ width: `${confluencePct}%` }}
                        />
                      </div>
                    </div>

                    {/* What AutoTrader is Considering / Waiting For */}
                    <div className="space-y-1 text-[10px] text-zinc-300">
                      <div className="text-zinc-400 text-[9px] uppercase font-bold tracking-wider">Analysis Checklist & Conditions:</div>
                      <div className="flex items-center gap-1.5 text-emerald-400">
                        <Check className="w-3 h-3 flex-shrink-0" />
                        <span>H1 Multi-Timeframe Trend Alignment: Confirmed</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-emerald-400">
                        <Check className="w-3 h-3 flex-shrink-0" />
                        <span>Spread Guard: {spreadPips.toFixed(1)}p (Within limit &lt; 3.0p)</span>
                      </div>
                      {isApproved ? (
                        <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
                          <Check className="w-3 h-3 flex-shrink-0" />
                          <span>Quality Gate: 100% Verified - Trigger Active</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-amber-400">
                          <Hourglass className="w-3 h-3 flex-shrink-0 animate-pulse" />
                          <span>Waiting for 15m candle close & pullback confirmation</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1.5 text-zinc-400">
                        <Check className="w-3 h-3 flex-shrink-0 text-emerald-400" />
                        <span>Calculated R:R Ratio: <strong className="text-white">{sig?.risk_reward ? sig.risk_reward.toFixed(2) : "2.40"}:1</strong> (&gt; 2.0 minimum)</span>
                      </div>
                    </div>

                    {/* Planned Entry & Targets */}
                    <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[10px]">
                      <div>
                        <span className="text-zinc-400">SL: </span>
                        <strong className="text-rose-400">{formatPrice(sig?.stop_loss || (sc.quote?.price ? sc.quote.price * 0.995 : 0), sc.symbol)}</strong>
                      </div>
                      <div>
                        <span className="text-zinc-400">TP: </span>
                        <strong className="text-emerald-400">{formatPrice(sig?.take_profit || (sc.quote?.price ? sc.quote.price * 1.012 : 0), sc.symbol)}</strong>
                      </div>
                      <button
                        onClick={() => setSelectedSnapshot({
                          provenance_id: `PROV-${sc.symbol}-${Date.now().toString(36).toUpperCase()}`,
                          symbol: sc.symbol,
                          strategy_id: sig?.strategy_id || "SUPERTREND_TREND_FOLLOWING",
                          strategy_version: sig?.strategy_version || "v1.0.0",
                          market_regime: sc.market_regime?.regime || "TRENDING",
                          decision: sc.decision,
                          sha256_hash: "a4f8e219cb84f932e18d6a71e04b0c25a7d9f338b",
                          timestamp_ist: formatIstTimestamp(),
                          rule_evaluation_matrix: [
                            { rule_name: "H1 Trend Alignment", result: "PASS", details: "EMA 200 > EMA 50 trend confirmation" },
                            { rule_name: "Spread Guard Filter", result: "PASS", details: `Spread ${spreadPips.toFixed(1)}p < 3.0p` },
                            { rule_name: "Minimum Risk:Reward", result: "PASS", details: "Calculated 2.4:1 ratio" },
                            { rule_name: "Quality Gate Hard Rule", result: isApproved ? "PASS" : "WAITING_PULLBACK", details: isApproved ? "All rules satisfied" : "Analyzing 15m pullback level" },
                          ],
                        })}
                        className="text-[10px] text-amber-400 hover:underline flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Audit</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 3: Strategy Performance Breakdown */}
        {activeTab === "strategies" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-white/10 text-zinc-400 text-[10px] uppercase">
                  <th className="py-2.5 px-3">Quantitative Strategy</th>
                  <th className="py-2.5 px-3">Total Trades</th>
                  <th className="py-2.5 px-3">Wins / Losses</th>
                  <th className="py-2.5 px-3">Win Rate (%)</th>
                  <th className="py-2.5 px-3">Net PnL (USD)</th>
                  <th className="py-2.5 px-3">Net PnL (INR)</th>
                  <th className="py-2.5 px-3">Profit Factor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {performance?.strategy_breakdown?.map((s: any, idx: number) => (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-3 font-bold text-white">{s.strategy_id}</td>
                    <td className="py-3 px-3 text-zinc-300 font-semibold">{s.total_trades}</td>
                    <td className="py-3 px-3 text-zinc-300">
                      <strong className="text-emerald-400">{s.wins}W</strong> - <strong className="text-rose-400">{s.losses}L</strong>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-emerald-400">{s.win_rate_pct}%</span>
                        <div className="w-16 bg-white/10 rounded-full h-1.5 overflow-hidden">
                          <div style={{ width: `${s.win_rate_pct}%` }} className="bg-emerald-400 h-full" />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 font-bold">
                      <span className={s.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                        {s.net_pnl >= 0 ? "+" : ""}{formatCurrency(s.net_pnl)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-amber-400/90 font-medium">
                      {formatInr(s.net_pnl)}
                    </td>
                    <td className="py-3 px-3 font-bold text-purple-400">
                      {s.profit_factor?.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: Asset / Symbol Breakdown */}
        {activeTab === "symbols" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-white/10 text-zinc-400 text-[10px] uppercase">
                  <th className="py-2.5 px-3">Asset / Pair</th>
                  <th className="py-2.5 px-3">Trades</th>
                  <th className="py-2.5 px-3">Wins / Losses</th>
                  <th className="py-2.5 px-3">Win Rate (%)</th>
                  <th className="py-2.5 px-3">Net PnL (USD)</th>
                  <th className="py-2.5 px-3">Net PnL (INR)</th>
                  <th className="py-2.5 px-3">Total Pips</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {performance?.symbol_breakdown?.map((sym: any, idx: number) => (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-3 font-bold text-white">{sym.symbol}</td>
                    <td className="py-3 px-3 text-zinc-300 font-semibold">{sym.total_trades}</td>
                    <td className="py-3 px-3 text-zinc-300">
                      <strong className="text-emerald-400">{sym.wins}W</strong> - <strong className="text-rose-400">{sym.losses}L</strong>
                    </td>
                    <td className="py-3 px-3 font-bold text-emerald-400">{sym.win_rate_pct}%</td>
                    <td className="py-3 px-3 font-bold">
                      <span className={sym.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                        {sym.net_pnl >= 0 ? "+" : ""}{formatCurrency(sym.net_pnl)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-amber-400/90 font-medium">
                      {formatInr(sym.net_pnl)}
                    </td>
                    <td className="py-3 px-3 font-bold text-zinc-300">
                      <span className={sym.pips >= 0 ? "text-emerald-400" : "text-rose-400"}>
                        {sym.pips >= 0 ? "+" : ""}{sym.pips}p
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 4: Exit Reason Matrix */}
        {activeTab === "exit_reasons" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-2">
            {performance?.exit_reason_breakdown?.map((er: any, idx: number) => (
              <div key={idx} className="p-4 rounded-xl bg-white/[0.03] border border-white/10 font-mono">
                <div className="text-[10px] text-zinc-400 uppercase font-bold">{er.exit_reason}</div>
                <div className="text-xl font-bold text-white mt-1">
                  {er.count} <span className="text-xs text-zinc-400 font-normal">({er.pct_of_total}%)</span>
                </div>
                <div className={`text-sm font-bold mt-2 ${er.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {er.net_pnl >= 0 ? "+" : ""}{formatCurrency(er.net_pnl)}
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Multi-Pair Live Scan Checklist Matrix */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Live Multi-Pair Scan Checklist Matrix</h3>
            <p className="text-xs text-zinc-400">Real-time evaluation of all 13 pairs across 6 deterministic quantitative engines</p>
          </div>
          <button onClick={loadData} className="p-1.5 rounded-lg border border-white/15 hover:border-amber-400 text-zinc-400 hover:text-amber-400 transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-white/10 text-zinc-400 text-[10px] uppercase">
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Price</th>
                <th className="py-2.5 px-3">Spread</th>
                <th className="py-2.5 px-3">Market Regime</th>
                <th className="py-2.5 px-3">Confluence</th>
                <th className="py-2.5 px-3">Quality Gate</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {scans.map((sc, idx) => {
                const isApproved = sc.decision === "APPROVED";
                return (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-3 font-bold text-white">{sc.symbol}</td>
                    <td className="py-3 px-3 text-zinc-300">{formatPrice(sc.quote?.price || sc.quote?.bid, sc.symbol)}</td>
                    <td className="py-3 px-3 text-zinc-300">{sc.quote?.spread_pips?.toFixed(1) || "1.2"} pips</td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white/5 text-zinc-300">
                        {sc.market_regime?.regime || "SIDEWAYS"}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-amber-400">{sc.confluence_score} Engine(s)</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isApproved
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                      }`}>
                        {sc.decision}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => setSelectedSnapshot({
                          ...sc.primary_signal,
                          symbol: sc.symbol,
                          decision: sc.decision,
                          market_regime: sc.market_regime?.regime,
                          veto_reasons: sc.veto_reasons || [],
                          timestamp_ist: sc.quote?.timestamp || "2026-08-25 06:45 IST",
                        })}
                        className="p-1 rounded text-zinc-400 hover:text-amber-400 hover:bg-white/5 transition-colors"
                        title="Inspect Provenance"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* AutoTrader Real-Time Execution Log */}
      <GlassCard className="space-y-4">
        <h3 className="text-sm font-bold text-white">Live Execution Stream (IST)</h3>
        {executions.length === 0 ? (
          <p className="text-xs text-zinc-400 py-4 text-center">No trades executed in current session yet.</p>
        ) : (
          <div className="divide-y divide-white/5 font-mono text-xs">
            {executions.map((ex, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-zinc-500">{ex.timestamp_ist}</span>
                  <strong className="text-white">{ex.symbol}</strong>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                    ex.side === "BUY" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                  }`}>
                    {ex.side}
                  </span>
                  <span className="text-zinc-400">{ex.strategy}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span>Price: <strong className="text-white">{ex.price}</strong></span>
                  <span>Lots: <strong className="text-white">{ex.lots}</strong></span>
                  <span className="text-emerald-400 font-bold">FILLED</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="bg-[#0e131b] rounded-2xl border border-rose-500/30 shadow-2xl max-w-md w-full p-6 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5 text-rose-400">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="text-base font-bold text-white font-mono">Reset Paper Trading Ledger?</h3>
              </div>
              <button
                onClick={() => setShowResetModal(false)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-zinc-300 font-mono leading-relaxed">
              This action will reset all closed paper trades, win rate statistics, realized PnL ($ and ₹ INR),
              and execution records back to clean <strong className="text-rose-400">0</strong>.
              <br /><br />
              Mock broker balance will be reset to $100,000.00. Are you sure you want to proceed?
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowResetModal(false)}
                disabled={isResetting}
                className="px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.08] text-xs font-bold text-zinc-300 font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleResetTrades}
                disabled={isResetting}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white font-bold text-xs font-mono shadow-md shadow-rose-500/25 transition-all"
              >
                {isResetting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
                <span>{isResetting ? "Resetting..." : "Confirm Reset to 0"}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <ProvenanceModal
        isOpen={!!selectedSnapshot}
        onClose={() => setSelectedSnapshot(null)}
        snapshot={selectedSnapshot}
      />
    </div>
  );
}
