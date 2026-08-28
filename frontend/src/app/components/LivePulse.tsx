"use client";

import React from "react";
import { useNav } from "@/lib/nav-context";
import { Play, Square, Bot } from "lucide-react";

interface LivePulseProps {
  label?: string;
  active?: boolean;
}

export function LivePulse({ label, active }: LivePulseProps) {
  const { autoTradeRunning, toggleAutoTrade } = useNav();
  const isRunning = active !== undefined ? active : autoTradeRunning;

  return (
    <button
      onClick={toggleAutoTrade}
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-xl font-mono text-xs font-bold transition-all border shadow-sm ${
        isRunning
          ? "bg-purple-500/15 border-purple-500/30 text-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.3)] hover:bg-purple-500/25"
          : "bg-white/[0.04] border-white/10 text-zinc-400 hover:text-white hover:bg-white/[0.08]"
      }`}
      title="Click to toggle AutoTrader ON / OFF"
    >
      <span className="relative flex h-2 w-2">
        {isRunning && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${isRunning ? "bg-purple-400 shadow-[0_0_8px_rgba(168,85,247,0.8)]" : "bg-zinc-600"}`}></span>
      </span>
      <span>{label || (isRunning ? "AUTOTRADER ON (ACTIVE)" : "AUTOTRADER OFF")}</span>
    </button>
  );
}
