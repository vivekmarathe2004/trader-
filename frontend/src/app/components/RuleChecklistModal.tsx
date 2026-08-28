"use client";

import React from "react";
import { X, CheckCircle2, XCircle } from "lucide-react";

interface RuleChecklistModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategyName: string;
  checklist: { rule: string; passed: boolean }[];
}

export function RuleChecklistModal({ isOpen, onClose, strategyName, checklist }: RuleChecklistModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4">
      <div className="bg-surface rounded-2xl border border-primary/15 shadow-elevation max-w-lg w-full p-6 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-primary/10 pb-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-primary">Strategy Rule Verification</h2>
            <p className="text-xs text-primary-muted">{strategyName}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-primary-muted hover:text-primary hover:bg-primary/5">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-2.5 my-4">
          {checklist.map((c, idx) => (
            <div
              key={idx}
              className={`flex items-center justify-between p-3 rounded-xl border text-xs font-mono ${
                c.passed ? "bg-profit-subtle/50 border-profit-border/60 text-primary" : "bg-loss-subtle/50 border-loss-border/60 text-primary"
              }`}
            >
              <div className="flex items-center gap-2.5">
                {c.passed ? <CheckCircle2 className="w-4 h-4 text-profit flex-shrink-0" /> : <XCircle className="w-4 h-4 text-loss flex-shrink-0" />}
                <span>{c.rule}</span>
              </div>
              <span className={`font-bold ${c.passed ? "text-profit" : "text-loss"}`}>
                {c.passed ? "PASSED" : "FAILED"}
              </span>
            </div>
          ))}
        </div>

        <button
          onClick={onClose}
          className="w-full mt-4 py-2.5 rounded-xl bg-primary text-surface font-semibold text-xs hover:bg-primary/90 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
}
