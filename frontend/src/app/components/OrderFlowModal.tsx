"use client";

import React from "react";
import { X, ArrowRight, CheckCircle, Clock, AlertTriangle } from "lucide-react";

interface OrderFlowModalProps {
  isOpen: boolean;
  onClose: () => void;
  orderId: string;
  currentState: string;
}

const FLOW_STEPS = [
  "SIGNAL",
  "RISK_CHECK",
  "ORDER_CREATED",
  "ORDER_SUBMITTED",
  "FILLED",
  "POSITION_OPEN",
  "POSITION_MODIFIED",
  "CLOSING",
  "CLOSED",
  "RECONCILED",
];

export function OrderFlowModal({ isOpen, onClose, orderId, currentState }: OrderFlowModalProps) {
  if (!isOpen) return null;

  const currentIndex = FLOW_STEPS.indexOf(currentState);
  const isFailed = ["REJECTED", "CANCELLED", "EXPIRED", "BROKER_ERROR", "RECONCILIATION_FAILED"].includes(currentState);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4">
      <div className="bg-surface rounded-2xl border border-primary/15 shadow-elevation max-w-xl w-full p-6 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-primary/10 pb-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-primary">Order State Machine Progression</h2>
            <p className="text-xs text-primary-muted font-mono">{orderId}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-primary-muted hover:text-primary hover:bg-primary/5">
            <X className="w-5 h-5" />
          </button>
        </div>

        {isFailed && (
          <div className="mb-4 p-3 rounded-xl bg-loss-subtle border border-loss-border flex items-center gap-2 text-xs font-mono text-loss">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Order terminated in failure state: <strong>{currentState}</strong></span>
          </div>
        )}

        <div className="space-y-2.5 my-4">
          {FLOW_STEPS.map((step, idx) => {
            const isCompleted = currentIndex >= idx;
            const isCurrent = currentState === step;

            return (
              <div
                key={step}
                className={`flex items-center justify-between p-3 rounded-xl border text-xs font-mono transition-all ${
                  isCurrent
                    ? "bg-accent/10 border-accent text-accent font-bold shadow-sm"
                    : isCompleted
                    ? "bg-profit-subtle/40 border-profit-border/60 text-primary"
                    : "bg-primary/5 border-primary/10 text-primary-muted opacity-50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isCurrent ? "bg-accent text-white" : isCompleted ? "bg-profit text-white" : "bg-primary/20 text-primary-muted"
                  }`}>
                    {idx + 1}
                  </div>
                  <span>{step}</span>
                </div>
                <div>
                  {isCurrent ? (
                    <span className="px-2 py-0.5 rounded bg-accent text-white text-[10px]">ACTIVE</span>
                  ) : isCompleted ? (
                    <CheckCircle className="w-4 h-4 text-profit" />
                  ) : (
                    <Clock className="w-4 h-4 text-primary-muted" />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <button
          onClick={onClose}
          className="w-full mt-4 py-2.5 rounded-xl bg-primary text-surface font-semibold text-xs hover:bg-primary/90 transition-colors"
        >
          Close State Machine Inspector
        </button>
      </div>
    </div>
  );
}
