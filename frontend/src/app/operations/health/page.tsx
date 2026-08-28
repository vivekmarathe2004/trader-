"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../../components/GlassCard";
import { PageHeader } from "../../components/PageHeader";
import { HealthPill } from "../../components/HealthPill";
import { formatCurrency, formatPercent } from "@/lib/format";
import { api } from "@/lib/api";
import { Activity, RefreshCw, CheckCircle2, DollarSign, PieChart, ShieldCheck } from "lucide-react";

export default function ControlCenterPage() {
  const [healthMatrix, setHealthMatrix] = useState<any>(null);
  const [attribution, setAttribution] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const loadData = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [hm, att] = await Promise.all([
        api.getHealthMatrix().catch(() => null),
        api.getAttribution().catch(() => null),
      ]);
      setHealthMatrix(hm);
      setAttribution(att);
    } catch (e) {
      console.warn("Failed to load health telemetry:", e);
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    loadData(true);
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        loadData(false);
      }
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Control Center & Attribution"
        subtitle="Deep subsystem observability, component latency monitoring, and performance attribution answering 'Why did I make money today?'"
        actions={
          <button
            onClick={() => loadData(true)}
            className="p-2 rounded-lg bg-surface border border-primary/15 hover:border-accent text-primary"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        }
      />

      {/* Subsystems Diagnostics Matrix */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-primary/10 pb-3">
          <div>
            <h3 className="text-sm font-bold text-primary">Core Subsystem Telemetry</h3>
            <p className="text-xs text-primary-muted font-mono">
              Overall Status: <strong className="text-profit">{healthMatrix?.overall_status || "HEALTHY"}</strong>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
          {healthMatrix?.subsystems?.map((sub: any) => (
            <div key={sub.id} className="p-3.5 rounded-xl bg-surface border border-primary/10 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary text-xs">{sub.name}</span>
                <HealthPill name="" status={sub.status} />
              </div>
              <p className="text-[11px] text-primary-muted font-sans leading-tight">{sub.description}</p>
              <div className="flex items-center justify-between text-[10px] text-primary-muted pt-1 border-t border-primary/5">
                <span>Latency: <strong className="text-primary">{sub.latency_ms?.toFixed(1)}ms</strong></span>
                <span>{sub.last_success_ist?.split(" ")[1]} IST</span>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Performance Attribution: "Why did I make money today?" */}
      {attribution && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-mono text-xs">
          {/* Strategy Breakdown */}
          <GlassCard className="lg:col-span-2 space-y-4">
            <h3 className="text-sm font-bold text-primary flex items-center gap-2">
              <PieChart className="w-4 h-4 text-accent" />
              Performance Attribution by Quantitative Class
            </h3>
            <div className="space-y-2.5">
              {Object.entries(attribution.strategy_attribution || {}).map(([stratClass, data]: [string, any]) => (
                <div key={stratClass} className="p-3 rounded-xl bg-surface border border-primary/10 flex items-center justify-between">
                  <div>
                    <strong className="text-primary block">{stratClass.replace(/_/g, " ")}</strong>
                    <span className="text-[10px] text-primary-muted">{data.trades} trades | {data.win_rate_pct}% win rate</span>
                  </div>
                  <div className="text-right">
                    <span className={`text-sm font-bold ${data.pnl_usd >= 0 ? "text-profit" : "text-loss"}`}>
                      {formatCurrency(data.pnl_usd)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Asset & Cost Breakdown */}
          <GlassCard className="space-y-4">
            <h3 className="text-sm font-bold text-primary flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-accent" />
              Alpha & Transaction Costs
            </h3>
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-surface border border-primary/10">
                <span className="text-[10px] text-primary-muted uppercase font-bold block">Best Performing Asset</span>
                <strong className="text-base text-profit font-bold">{attribution.best_performing_asset}</strong>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-primary/10">
                <span className="text-[10px] text-primary-muted uppercase font-bold block">Total Commissions Drag</span>
                <strong className="text-base text-loss font-bold">-{formatCurrency(attribution.transaction_costs?.total_commission_usd)}</strong>
              </div>
              <div className="p-3 rounded-xl bg-profit-subtle border border-profit-border">
                <span className="text-[10px] text-profit uppercase font-bold block">Net Alpha Realized</span>
                <strong className="text-base text-profit font-bold">{formatCurrency(attribution.transaction_costs?.net_alpha_pnl_usd)}</strong>
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
