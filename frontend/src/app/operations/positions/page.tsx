"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../../components/GlassCard";
import { PageHeader } from "../../components/PageHeader";
import { OrderFlowModal } from "../../components/OrderFlowModal";
import { formatPrice, formatCurrency, formatPips } from "@/lib/format";
import { api } from "@/lib/api";
import { useNav } from "@/lib/nav-context";
import { Briefcase, X, Sliders, ArrowUpRight, ArrowDownRight, Layers, CheckCircle2, Shield } from "lucide-react";

export default function PositionsDeskPage() {
  const { activeBroker, refreshTelemetry } = useNav();
  const [positions, setPositions] = useState<any[]>([]);
  const [selectedOrderFlow, setSelectedOrderFlow] = useState<string | null>(null);
  const [modifyPos, setModifyPos] = useState<any | null>(null);
  const [newSl, setNewSl] = useState<number>(0);
  const [newTp, setNewTp] = useState<number>(0);

  const loadPositions = async () => {
    try {
      const data = await api.getPositions().catch(() => ({ positions: [] }));
      setPositions(data?.positions || []);
    } catch (e) {
      console.warn("Failed to load positions:", e);
    }
  };

  useEffect(() => {
    loadPositions();
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        loadPositions();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleClose = async (posId: string) => {
    try {
      await api.closePosition(posId);
      await loadPositions();
      await refreshTelemetry();
    } catch (e) {
      console.error(e);
    }
  };

  const handleModify = async () => {
    if (!modifyPos) return;
    try {
      await api.modifyPosition(modifyPos.position_id, newSl, newTp);
      setModifyPos(null);
      await loadPositions();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Positions Desk & Order Flow"
        subtitle="Manage open market positions across brokers with Dynamic Break-Even tracking, SL/TP modifications, and state machine audit."
        badge={`${positions.length} OPEN POSITIONS`}
      />

      {positions.length === 0 ? (
        <GlassCard className="text-center py-16 text-primary-muted">
          <Briefcase className="w-10 h-10 text-primary-muted mx-auto mb-2 opacity-50" />
          <p className="text-sm font-semibold">No active open positions on {activeBroker}</p>
          <p className="text-xs mt-1">Positions will appear when signals qualify or manual orders are submitted.</p>
        </GlassCard>
      ) : (
        <div className="space-y-4">
          {positions.map((pos) => {
            const isProfit = pos.unrealized_pnl >= 0;
            return (
              <GlassCard key={pos.position_id} className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-primary/10 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-lg font-mono text-primary">{pos.symbol}</span>
                    <span className={`px-2.5 py-0.5 rounded text-xs font-bold font-mono ${
                      pos.side === "BUY" ? "bg-profit-subtle text-profit border border-profit-border" : "bg-loss-subtle text-loss border border-loss-border"
                    }`}>
                      {pos.side}
                    </span>
                    <span className="text-xs font-mono text-primary-muted">
                      Lots: <strong className="text-primary">{pos.lots}</strong>
                    </span>
                    {pos.break_even_active && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-accent/10 text-accent border border-accent/20 flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        <span>BREAK-EVEN LOCKED (+1p)</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right font-mono">
                      <div className="text-[10px] text-primary-muted uppercase font-bold">Unrealized PnL</div>
                      <div className={`text-base font-bold ${isProfit ? "text-profit" : "text-loss"}`}>
                        {formatCurrency(pos.unrealized_pnl)}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setModifyPos(pos);
                          setNewSl(pos.stop_loss || pos.entry_price);
                          setNewTp(pos.take_profit || pos.entry_price);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-surface border border-primary/15 hover:border-accent text-xs font-semibold text-primary transition-all"
                      >
                        Modify SL/TP
                      </button>

                      <button
                        onClick={() => setSelectedOrderFlow(pos.position_id)}
                        className="px-3 py-1.5 rounded-lg bg-surface border border-primary/15 hover:border-accent text-xs font-semibold text-primary transition-all font-mono"
                      >
                        Flow State
                      </button>

                      <button
                        onClick={() => handleClose(pos.position_id)}
                        className="px-3 py-1.5 rounded-lg bg-loss-subtle border border-loss-border text-loss hover:bg-loss hover:text-white text-xs font-bold transition-all"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>

                {/* Price Levels Strip */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-2.5 rounded-lg bg-surface border border-primary/10">
                    <span className="text-[10px] text-primary-muted block uppercase font-bold">Entry Price</span>
                    <strong className="text-primary text-sm">{formatPrice(pos.entry_price, pos.symbol)}</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-primary/10">
                    <span className="text-[10px] text-primary-muted block uppercase font-bold">Current Price</span>
                    <strong className="text-primary text-sm">{formatPrice(pos.current_price, pos.symbol)}</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-primary/10">
                    <span className="text-[10px] text-primary-muted block uppercase font-bold">Stop Loss</span>
                    <strong className="text-loss text-sm">{formatPrice(pos.stop_loss, pos.symbol)}</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-primary/10">
                    <span className="text-[10px] text-primary-muted block uppercase font-bold">Take Profit</span>
                    <strong className="text-profit text-sm">{formatPrice(pos.take_profit, pos.symbol)}</strong>
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>
      )}

      {/* Modify SL/TP Modal */}
      {modifyPos && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4">
          <div className="bg-surface rounded-2xl border border-primary/15 shadow-elevation max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-primary/10 pb-3">
              <h3 className="text-base font-bold text-primary">Modify {modifyPos.symbol} Position</h3>
              <button onClick={() => setModifyPos(null)} className="p-1 rounded-lg text-primary-muted hover:text-primary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-primary-muted font-bold block mb-1">New Stop Loss</label>
                <input
                  type="number"
                  step="0.0001"
                  value={newSl}
                  onChange={(e) => setNewSl(parseFloat(e.target.value))}
                  className="w-full p-2.5 rounded-lg bg-surface border border-primary/15 font-bold"
                />
              </div>

              <div>
                <label className="text-primary-muted font-bold block mb-1">New Take Profit</label>
                <input
                  type="number"
                  step="0.0001"
                  value={newTp}
                  onChange={(e) => setNewTp(parseFloat(e.target.value))}
                  className="w-full p-2.5 rounded-lg bg-surface border border-primary/15 font-bold"
                />
              </div>
            </div>

            <button
              onClick={handleModify}
              className="w-full py-2.5 rounded-xl bg-accent text-white font-bold text-xs hover:bg-accent-hover transition-colors shadow-sm"
            >
              SAVE MODIFICATIONS
            </button>
          </div>
        </div>
      )}

      {/* Order Flow State Machine Modal */}
      <OrderFlowModal
        isOpen={!!selectedOrderFlow}
        onClose={() => setSelectedOrderFlow(null)}
        orderId={selectedOrderFlow || ""}
        currentState={
          (() => {
            const pos = positions.find((p) => p.position_id === selectedOrderFlow);
            if (!pos) return "POSITION_OPEN";
            // Break-even active means the position has been modified after opening
            if (pos.break_even_active) return "POSITION_MODIFIED";
            return "POSITION_OPEN";
          })()
        }
      />
    </div>
  );
}
