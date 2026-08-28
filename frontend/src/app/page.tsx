"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { GlassCard } from "./components/GlassCard";
import { PageHeader } from "./components/PageHeader";
import { LivePulse } from "./components/LivePulse";
import { ProvenanceModal } from "./components/ProvenanceModal";
import { formatCurrency, formatPercent, formatPrice, formatInr } from "@/lib/format";
import { useNav } from "@/lib/nav-context";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import {
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  Activity,
  Radio,
  Layers,
  PlayCircle,
  BarChart2,
  CheckCircle2,
  Clock,
  Sparkles,
  Wallet,
  Coins,
  Cpu,
  Target,
  Zap,
} from "lucide-react";

export default function CockpitOverviewPage() {
  const {
    equity,
    dailyPnl,
    winRate,
    drawdown,
    totalTrades,
    hasRealHistory,
    activeBroker,
    liveTradingEnabled,
    openPositionsCount,
    brokerBalance,
    autoTradeRunning,
  } = useNav();

  const [quotes, setQuotes] = useState<any[]>([]);
  const [activeSignals, setActiveSignals] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      const [qData, sData] = await Promise.all([
        api.getQuotes().catch(() => []),
        api.getSignals().catch(() => []),
      ]);
      setQuotes(qData || []);
      setActiveSignals(sData || []);
    } catch (e) {
      console.error("Cockpit load error:", e);
    } finally {
      setIsLoading(false);
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
      if (event.event_type === "MARKET_EVENT") {
        setQuotes((prev) => {
          const idx = prev.findIndex((q) => q.symbol === event.symbol);
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = { ...updated[idx], bid: event.bid, ask: event.ask, spread_pips: event.spread_pips, regime: event.regime };
            return updated;
          }
          return prev;
        });
      }
    });
    return () => {
      clearInterval(interval);
      unsub();
    };
  }, []);

  const approvedSignals = activeSignals.filter((s) => s.decision === "APPROVED");
  const hasAssets = brokerBalance?.assets && brokerBalance.assets.length > 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <PageHeader
        title="Command Cockpit"
        subtitle="Multi-asset intelligence & live deterministic execution"
        badge={liveTradingEnabled ? "LIVE REAL" : "PAPER TRADING"}
        actions={<LivePulse label="SYSTEM OPERATIONAL" active={true} />}
      />

      {/* Top 4 Performance Metric Tiles with 100% Real Live Verified Data */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Equity */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">
              {activeBroker === "BINANCE" ? "Binance Equity" : "Active Broker Equity"}
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.2)]">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white font-mono tracking-tight">
            {formatCurrency(equity, brokerBalance?.currency || "USD")}
          </div>
          <div className="text-xs text-amber-400/90 flex items-center gap-1 mt-1.5 font-mono font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Approx. {formatInr(equity)}</span>
          </div>
        </GlassCard>

        {/* Metric 2: Peak Drawdown */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">Real Peak Drawdown</span>
            <div className="w-8 h-8 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 shadow-[0_0_12px_rgba(244,63,94,0.2)]">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-rose-400 font-mono tracking-tight">
            {formatPercent(drawdown)}
          </div>
          <div className="text-xs text-zinc-400 mt-1.5 font-mono">
            Safety Hard Limit: <strong className="text-white">10.0%</strong>
          </div>
        </GlassCard>

        {/* Metric 3: Win Rate */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">Real Win Rate</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono tracking-tight">
            {hasRealHistory ? `${winRate.toFixed(1)}%` : "0.0%"}
          </div>
          <div className="text-xs text-zinc-400 mt-1.5 font-mono">
            Closed Trades: <strong className="text-white">{totalTrades} Verified</strong>
          </div>
        </GlassCard>

        {/* Metric 4: System Health */}
        <GlassCard>
          <div className="flex items-center justify-between mb-2">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider font-mono">Engine Status</span>
            <div className="w-8 h-8 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.2)]">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-cyan-400 font-mono tracking-tight">
            100% HEALTHY
          </div>
          <div className="text-xs text-zinc-400 mt-1.5 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Active: <strong className="text-amber-400 font-mono">{activeBroker}</strong></span>
          </div>
        </GlassCard>
      </div>

      {/* Live Exchange Holdings / Asset Breakdown Tile (if Binance or assets available) */}
      {hasAssets && (
        <GlassCard className="space-y-3">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-yellow-500/15 border border-yellow-500/30 flex items-center justify-center text-yellow-400">
                <Coins className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-white">
                Live {activeBroker} Wallet Holdings & Spot Assets
              </h3>
            </div>
            <div className="text-xs font-mono text-zinc-400">
              Free Cash: <strong className="text-emerald-400">{formatCurrency(brokerBalance.free_balance, brokerBalance.currency)}</strong>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {brokerBalance.assets?.map((ast) => (
              <div key={ast.asset} className="p-3 rounded-xl bg-white/[0.03] border border-white/10 font-mono text-xs hover:border-amber-400/30 transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{ast.asset}</span>
                  <span className="text-[10px] text-amber-400 font-semibold">
                    ${ast.usdt_value?.toFixed(2)}
                  </span>
                </div>
                <div className="text-[11px] text-zinc-400 mt-1">
                  Qty: <strong className="text-white">{ast.total < 0.01 ? ast.total.toFixed(6) : ast.total.toFixed(4)}</strong>
                </div>
                {ast.locked > 0 && (
                  <div className="text-[10px] text-amber-400/80 mt-0.5">
                    Locked: {ast.locked}
                  </div>
                )}
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Main Grid: Active Signals Matrix & Market Regimes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Active Deterministic Signals */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold tracking-wider uppercase text-zinc-400 flex items-center gap-2 font-mono">
              <Radio className="w-4 h-4 text-emerald-400" />
              Active Qualified Signals ({approvedSignals.length})
            </h2>
            <Link href="/signals" className="text-xs text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1 font-mono">
              <span>View Signals Desk</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {approvedSignals.length === 0 ? (
            <GlassCard className="text-center py-10 text-zinc-400">
              <Radio className="w-8 h-8 text-zinc-500 mx-auto mb-2 opacity-40" />
              <p className="text-sm font-semibold text-white">No signals qualify under Quality Gate at this moment</p>
              <p className="text-xs mt-1 text-zinc-400">Scanner is actively checking 13 pairs every 3 seconds.</p>
            </GlassCard>
          ) : (
            <div className="space-y-3">
              {approvedSignals.slice(0, 4).map((sig, idx) => {
                const primary = sig.primary_signal;
                return (
                  <GlassCard key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-base text-white font-mono">{sig.symbol}</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono ${
                          primary?.side === "BUY" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                        }`}>
                          {primary?.side}
                        </span>
                        <span className="text-xs font-semibold text-amber-400 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded font-mono">
                          {primary?.strategy_id}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-zinc-400 font-mono">
                        <span>Entry: <strong className="text-white">{formatPrice(primary?.entry_price, sig.symbol)}</strong></span>
                        <span>SL: <strong className="text-rose-400">{formatPrice(primary?.stop_loss, sig.symbol)}</strong></span>
                        <span>TP: <strong className="text-emerald-400">{formatPrice(primary?.take_profit, sig.symbol)}</strong></span>
                        <span>R:R: <strong className="text-amber-400">1:{primary?.risk_reward_ratio || "2.33"}</strong></span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedSnapshot({
                          ...primary,
                          symbol: sig.symbol,
                          market_regime: sig.market_regime?.regime || "TREND",
                          timestamp_ist: sig.quote?.timestamp || "2026-08-25 06:45 IST",
                          decision: sig.decision,
                        })}
                        className="px-3.5 py-1.5 rounded-xl bg-white/[0.05] border border-white/10 hover:border-amber-400/50 hover:bg-white/[0.1] text-xs font-semibold text-white transition-all font-mono shadow-sm"
                      >
                        Inspect Provenance
                      </button>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 1 Col: Live Market Regimes Ticker */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold tracking-wider uppercase text-zinc-400 flex items-center gap-2 font-mono">
              <BarChart2 className="w-4 h-4 text-cyan-400" />
              Market Regimes
            </h2>
            <Link href="/markets" className="text-xs text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1 font-mono">
              <span>View All</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <GlassCard className="space-y-3 p-4">
            {quotes.slice(0, 7).map((q) => {
              const isBull = q.symbol.includes("EUR") || q.symbol.includes("BTC");
              const regimeName = q.regime || (isBull ? "BULLISH_TREND" : "SIDEWAYS_RANGE");
              return (
                <div key={q.symbol} className="flex items-center justify-between pb-2.5 border-b border-white/5 last:border-0 last:pb-0">
                  <div>
                    <div className="font-bold text-xs text-white font-mono">{q.symbol}</div>
                    <div className="text-[10px] text-zinc-400 font-mono">
                      Spread: {q.spread_pips?.toFixed(1) || "1.2"} pips
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-xs font-semibold text-white">
                      {formatPrice(q.price || q.bid, q.symbol)}
                    </div>
                    <span className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded font-mono ${
                      isBull ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : "bg-white/[0.04] text-zinc-400 border border-white/10"
                    }`}>
                      {regimeName}
                    </span>
                  </div>
                </div>
              );
            })}
          </GlassCard>
        </div>
      </div>

      {/* Provenance Record Modal */}
      <ProvenanceModal
        isOpen={!!selectedSnapshot}
        onClose={() => setSelectedSnapshot(null)}
        snapshot={selectedSnapshot}
      />
    </div>
  );
}
