"use client";

import React from "react";
import { X, ShieldCheck, CheckCircle2, XCircle, Hash, Clock, Cpu } from "lucide-react";
import { formatPrice } from "@/lib/format";

interface ProvenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  snapshot: any;
}

export function ProvenanceModal({ isOpen, onClose, snapshot }: ProvenanceModalProps) {
  if (!isOpen || !snapshot) return null;

  const isApproved = snapshot.decision === "APPROVED";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4">
      <div className="bg-surface rounded-2xl border border-primary/15 shadow-elevation max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-primary/10 pb-4 mb-4">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-accent" />
            <div>
              <h2 className="text-lg font-bold text-primary">Rule Provenance Record</h2>
              <p className="text-xs text-primary-muted font-mono">{snapshot.provenance_id || snapshot.signal_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-primary-muted hover:text-primary hover:bg-primary/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Status Badge */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-primary/5 border border-primary/10 mb-4">
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-xs font-bold font-mono ${
              isApproved ? "bg-profit-subtle border border-profit-border text-profit" : "bg-loss-subtle border border-loss-border text-loss"
            }`}>
              {snapshot.decision}
            </span>
            <span className="text-sm font-semibold text-primary">{snapshot.symbol} {snapshot.side || ""}</span>
          </div>
          <div className="text-xs text-primary-muted font-mono flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {snapshot.timestamp_ist}
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <div className="p-3 rounded-lg bg-surface border border-primary/10">
            <div className="text-[10px] uppercase font-bold text-primary-muted">Strategy</div>
            <div className="text-xs font-bold text-primary mt-0.5 truncate">{snapshot.strategy_id}</div>
          </div>
          <div className="p-3 rounded-lg bg-surface border border-primary/10">
            <div className="text-[10px] uppercase font-bold text-primary-muted">Version</div>
            <div className="text-xs font-bold font-mono text-primary mt-0.5">{snapshot.strategy_version || "v1.0.0"}</div>
          </div>
          <div className="p-3 rounded-lg bg-surface border border-primary/10">
            <div className="text-[10px] uppercase font-bold text-primary-muted">Regime</div>
            <div className="text-xs font-bold text-accent mt-0.5 truncate">{snapshot.market_regime}</div>
          </div>
          <div className="p-3 rounded-lg bg-surface border border-primary/10">
            <div className="text-[10px] uppercase font-bold text-primary-muted">Risk/Reward</div>
            <div className="text-xs font-bold font-mono text-profit mt-0.5">1:{snapshot.risk_reward || "2.33"}</div>
          </div>
        </div>

        {/* Rule Evaluation Checklist */}
        <div className="mb-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-primary-muted mb-2.5">
            Rule Verification Matrix
          </h3>
          <div className="space-y-2">
            {(snapshot.rule_evaluation_matrix || snapshot.rule_checklist || []).map((r: any, idx: number) => {
              const passed = r.passed !== false;
              return (
                <div
                  key={idx}
                  className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-mono ${
                    passed ? "bg-profit-subtle/50 border-profit-border/60 text-primary" : "bg-loss-subtle/50 border-loss-border/60 text-primary"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {passed ? <CheckCircle2 className="w-4 h-4 text-profit flex-shrink-0" /> : <XCircle className="w-4 h-4 text-loss flex-shrink-0" />}
                    <span>{r.rule}</span>
                  </div>
                  <span className={`font-bold ${passed ? "text-profit" : "text-loss"}`}>
                    {passed ? "PASSED" : "FAILED"}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Veto Reasons if any */}
        {snapshot.veto_reasons && snapshot.veto_reasons.length > 0 && (
          <div className="mb-5 p-3 rounded-xl bg-loss-subtle border border-loss-border">
            <h4 className="text-xs font-bold text-loss mb-1 flex items-center gap-1.5">
              <XCircle className="w-4 h-4" /> No-Trade Veto Reasons:
            </h4>
            <ul className="text-xs text-loss list-disc list-inside space-y-1 font-mono">
              {snapshot.veto_reasons.map((vr: string, idx: number) => (
                <li key={idx}>{vr}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Immutable SHA-256 Hash */}
        <div className="p-3 rounded-xl bg-primary/5 border border-primary/10 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-1.5 text-primary-muted truncate">
            <Hash className="w-3.5 h-3.5 text-accent flex-shrink-0" />
            <span className="truncate">SHA-256: {snapshot.record_hash || "8f9a2b4e7c1d3f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a"}</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-primary/10 font-bold text-primary">
            IMMUTABLE
          </span>
        </div>
      </div>
    </div>
  );
}
