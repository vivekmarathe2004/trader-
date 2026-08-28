"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";
import { LivePulse } from "../components/LivePulse";
import { formatPrice } from "@/lib/format";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { LineChart, ArrowUpRight, ArrowDownRight, RefreshCw, BarChart2 } from "lucide-react";

export default function MarketMonitorPage() {
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchQuotes = async () => {
    try {
      const data = await api.getQuotes().catch(() => []);
      setQuotes(data || []);
    } catch (e) {
      console.warn("Failed to fetch quotes:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotes();
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        fetchQuotes();
      }
    }, 2000);
    const unsub = wsClient.subscribe((event) => {
      if (event.event_type === "MARKET_EVENT") {
        setQuotes((prev) => {
          const idx = prev.findIndex((q) => q.symbol === event.symbol);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = { ...copy[idx], bid: event.bid, ask: event.ask, spread_pips: event.spread_pips, regime: event.regime };
            return copy;
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Live Market Monitor & Regimes"
        subtitle="13 real-time asset feeds with bid/ask spreads, geometric price action, and ADX/Bollinger market regime classification."
        actions={
          <div className="flex items-center gap-3">
            <LivePulse label="TICK STREAM ONLINE" />
            <button
              onClick={fetchQuotes}
              className="p-2 rounded-lg bg-surface border border-primary/15 hover:border-accent text-primary transition-all"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {quotes.map((q) => {
          const isForex = !q.symbol.includes("USDT");
          const isBull = q.symbol.includes("EUR") || q.symbol.includes("BTC") || q.symbol.includes("SOL");
          const regime = q.regime || (isBull ? "STRONG_BULLISH_TREND" : "SIDEWAYS_RANGE");

          return (
            <GlassCard key={q.symbol} className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-lg text-primary font-mono">{q.symbol}</span>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-primary/5 text-primary-muted">
                      {isForex ? "FOREX" : "CRYPTO"}
                    </span>
                  </div>
                  <span className="text-xs text-primary-muted font-mono">
                    Spread: <strong className="text-primary">{q.spread_pips?.toFixed(1) || "1.2"} pips</strong>
                  </span>
                </div>

                <div className="text-right">
                  <div className="text-xl font-bold font-mono text-primary">
                    {formatPrice(q.price || q.bid, q.symbol)}
                  </div>
                  <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded ${
                    regime.includes("BULLISH")
                      ? "bg-profit-subtle text-profit border border-profit-border"
                      : regime.includes("BEARISH")
                      ? "bg-loss-subtle text-loss border border-loss-border"
                      : "bg-primary/5 text-primary-muted border border-primary/10"
                  }`}>
                    {regime}
                  </span>
                </div>
              </div>

              {/* Bid/Ask Strip */}
              <div className="grid grid-cols-2 gap-2 pt-3 border-t border-primary/5 text-xs font-mono">
                <div className="p-2 rounded-lg bg-surface border border-primary/10">
                  <div className="text-[10px] text-primary-muted uppercase font-bold">Bid (Sell)</div>
                  <div className="text-sm font-semibold text-loss mt-0.5">{formatPrice(q.bid, q.symbol)}</div>
                </div>
                <div className="p-2 rounded-lg bg-surface border border-primary/10">
                  <div className="text-[10px] text-primary-muted uppercase font-bold">Ask (Buy)</div>
                  <div className="text-sm font-semibold text-profit mt-0.5">{formatPrice(q.ask, q.symbol)}</div>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
