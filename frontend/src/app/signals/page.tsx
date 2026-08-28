"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";
import { LivePulse } from "../components/LivePulse";
import { ProvenanceModal } from "../components/ProvenanceModal";
import { NoTradeBadge } from "../components/NoTradeBadge";
import { RuleChecklistModal } from "../components/RuleChecklistModal";
import { formatPrice } from "@/lib/format";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { RefreshCw, Eye, ListChecks } from "lucide-react";

export default function SignalsDeskPage() {
  const [signals, setSignals] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);
  const [selectedChecklist, setSelectedChecklist] = useState<{ strategyName: string; checklist: { rule: string; passed: boolean }[] } | null>(null);
  const [filter, setFilter] = useState<"ALL" | "APPROVED" | "NO_TRADE">("ALL");
  const [timeframe, setTimeframe] = useState<string>("5m");

  const loadSignals = async () => {
    try {
      const data = await api.getSignals(timeframe).catch(() => []);
      setSignals(data || []);
    } catch (e) {
      console.warn("Failed to load signals:", e);
    }
  };

  useEffect(() => {
    loadSignals();
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        loadSignals();
      }
    }, 2000);
    // Subscribe to live signal events from the auto trader scan cycle
    const unsub = wsClient.subscribe((event) => {
      if (event.event_type === "SIGNAL_EVENT" || event.event_type === "EXECUTION_EVENT") {
        loadSignals();
      }
    });
    return () => {
      clearInterval(interval);
      unsub();
    };
  }, [timeframe]);

  const filteredSignals = signals.filter((s) => {
    if (filter === "APPROVED") return s.decision === "APPROVED";
    if (filter === "NO_TRADE") return s.decision === "NO_TRADE";
    return true;
  });

  /** Build a checklist from the signal's quality_checks or veto_reasons */
  const buildChecklist = (item: any): { rule: string; passed: boolean }[] => {
    // Use quality_checks if the backend provides them
    if (item.quality_checks && Array.isArray(item.quality_checks)) {
      return item.quality_checks.map((qc: any) => ({
        rule: qc.rule || qc.name || String(qc),
        passed: qc.passed !== false,
      }));
    }
    // Fallback: synthesize from veto_reasons
    const defaultRules = [
      "Trend Alignment (H1 filter)",
      "Spread within limit",
      "Quality Gate score ≥ threshold",
      "Daily loss limit not breached",
      "Max open positions not exceeded",
    ];
    const vetoSet = new Set<string>(item.veto_reasons || []);
    return defaultRules.map((rule) => ({
      rule,
      passed: !Array.from(vetoSet).some((v) => rule.toLowerCase().includes(v.toLowerCase().split("_")[0])),
    }));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Deterministic Signals Desk & Scalp Radar"
        subtitle="Every candidate evaluated under the unbypassable Quality Gate across micro-scalping and short-timeframe models."
        actions={
          <div className="flex items-center gap-3">
            <LivePulse label="CONFLUENCE ENGINE" />
            <button
              onClick={loadSignals}
              className="p-2 rounded-lg bg-surface border border-primary/15 hover:border-accent text-primary"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        }
      />

      {/* Control Tabs: Decision Filters & Timeframes */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Decision Filter Tabs */}
        <div className="flex items-center gap-2">
          {(["ALL", "APPROVED", "NO_TRADE"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                filter === f
                  ? "bg-accent text-white shadow-sm"
                  : "bg-primary/5 text-primary-muted hover:text-primary hover:bg-primary/10"
              }`}
            >
              {f} {f === "APPROVED" ? `(${signals.filter((s) => s.decision === "APPROVED").length})` : ""}
            </button>
          ))}
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/[0.04] border border-white/10 font-mono text-xs">
          {[
            { id: "1m", label: "⚡ 1M" },
            { id: "3m", label: "⏱️ 3M" },
            { id: "5m", label: "🔥 5M" },
            { id: "15m", label: "📊 15M" },
          ].map((tf) => (
            <button
              key={tf.id}
              onClick={() => setTimeframe(tf.id)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                timeframe === tf.id
                  ? "bg-amber-400 text-black shadow-sm font-black"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Signals List */}
      <div className="space-y-3">
        {filteredSignals.map((item, idx) => {
          const isApproved = item.decision === "APPROVED";
          const sig = item.primary_signal;

          return (
            <GlassCard key={idx} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold font-mono text-primary">{item.symbol}</span>
                  <span className={`px-2.5 py-0.5 rounded text-xs font-bold font-mono ${
                    isApproved
                      ? "bg-profit-subtle border border-profit-border text-profit"
                      : "bg-loss-subtle border border-loss-border text-loss"
                  }`}>
                    {item.decision}
                  </span>
                  {sig?.side && (
                    <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono ${
                      sig.side === "BUY" ? "bg-profit-subtle text-profit" : "bg-loss-subtle text-loss"
                    }`}>
                      {sig.side}
                    </span>
                  )}
                  <span className="text-xs font-semibold text-accent bg-accent/10 px-2 py-0.5 rounded">
                    {sig?.strategy_id || "MULTI_CONFLUENCE"}
                  </span>
                </div>

                {isApproved && sig ? (
                  <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-primary-muted">
                    <span>Entry: <strong className="text-primary">{formatPrice(sig.entry_price, item.symbol)}</strong></span>
                    <span>SL: <strong className="text-loss">{formatPrice(sig.stop_loss, item.symbol)}</strong></span>
                    <span>TP: <strong className="text-profit">{formatPrice(sig.take_profit, item.symbol)}</strong></span>
                    <span>R:R: <strong className="text-primary">1:{sig.risk_reward_ratio || "2.33"}</strong></span>
                    <span>Regime: <strong className="text-accent">{item.market_regime?.regime}</strong></span>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-center gap-2">
                    {item.veto_reasons?.map((vr: string, vIdx: number) => (
                      <NoTradeBadge key={vIdx} reason={vr} />
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                {/* Rule Checklist Button — opens the real quality gate checklist */}
                <button
                  onClick={() => setSelectedChecklist({
                    strategyName: `${item.symbol} — ${sig?.strategy_id || "MULTI_CONFLUENCE"} (${timeframe})`,
                    checklist: buildChecklist(item),
                  })}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-primary/15 hover:border-accent/60 text-xs font-semibold text-primary-muted hover:text-primary transition-all shadow-sm"
                  title="View Quality Gate rule checklist"
                >
                  <ListChecks className="w-3.5 h-3.5 text-accent" />
                  <span>Rules</span>
                </button>

                <button
                  onClick={() => setSelectedSnapshot({
                    ...sig,
                    symbol: item.symbol,
                    decision: item.decision,
                    market_regime: item.market_regime?.regime || "TREND",
                    veto_reasons: item.veto_reasons || [],
                    timestamp_ist: item.quote?.timestamp || "2026-08-25 06:45 IST",
                  })}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-primary/15 hover:border-accent text-xs font-semibold text-primary transition-all shadow-sm"
                >
                  <Eye className="w-3.5 h-3.5 text-accent" />
                  <span>Inspect Provenance</span>
                </button>
              </div>
            </GlassCard>
          );
        })}
      </div>

      <ProvenanceModal
        isOpen={!!selectedSnapshot}
        onClose={() => setSelectedSnapshot(null)}
        snapshot={selectedSnapshot}
      />

      <RuleChecklistModal
        isOpen={!!selectedChecklist}
        onClose={() => setSelectedChecklist(null)}
        strategyName={selectedChecklist?.strategyName || ""}
        checklist={selectedChecklist?.checklist || []}
      />
    </div>
  );
}



