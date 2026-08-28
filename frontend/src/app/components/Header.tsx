"use client";

import React, { useState, useEffect } from "react";
import { useNav } from "@/lib/nav-context";
import { formatIstTimestamp, formatCurrency, formatInr } from "@/lib/format";
import {
  ShieldAlert,
  Power,
  ChevronDown,
  Layers,
  Clock,
  Lock,
  Unlock,
  Wallet,
  Play,
  Square,
  Bot,
} from "lucide-react";

export function Header() {
  const {
    activeBroker,
    setActiveBroker,
    liveTradingEnabled,
    setLiveTradingEnabled,
    emergencyKillActive,
    triggerEmergencyStop,
    resetEmergencyStop,
    autoTradeRunning,
    toggleAutoTrade,
    equity,
    brokerBalance,
  } = useNav();

  const [istTime, setIstTime] = useState<string>("");
  const [brokerMenuOpen, setBrokerMenuOpen] = useState<boolean>(false);

  useEffect(() => {
    setIstTime(formatIstTimestamp());
    const timer = setInterval(() => setIstTime(formatIstTimestamp()), 1000);
    return () => clearInterval(timer);
  }, []);

  const brokers = [
    { id: "BINANCE", name: "Binance Spot Live", tag: "CRYPTO" },
    { id: "MOCK_BROKER", name: "Simulated Paper Engine", tag: "SIMULATOR" },
    { id: "OANDA", name: "OANDA v20 REST", tag: "FOREX" },
    { id: "DERIV", name: "Deriv WebSocket", tag: "SYNTHETIC" },
    { id: "MT5", name: "MetaTrader 5 Bridge", tag: "DESKTOP" },
  ];

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-6 py-2.5 bg-[#070A0F]/90 backdrop-blur-2xl border-b border-white/[0.06] shadow-sm">
      {/* Left: Live Portfolio Balance & Active Route Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-2xl bg-gradient-to-r from-white/[0.05] via-white/[0.02] to-transparent border border-white/[0.06] shadow-inner">
          <div className="w-7 h-7 rounded-xl bg-amber-400/15 border border-amber-400/30 flex items-center justify-center text-amber-400">
            <Wallet className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-[9px] uppercase font-bold text-zinc-400 font-mono flex items-center gap-1.5 leading-none">
              <span>{activeBroker} Balance</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div className="text-sm font-black font-mono text-white flex items-center gap-2 mt-0.5 leading-tight">
              <span>{formatCurrency(equity, brokerBalance?.currency || "USD")}</span>
              <span className="text-xs text-amber-400/90 font-medium">({formatInr(equity)})</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Broker Switcher, Live Gate, Kill Switch, Clock */}
      <div className="flex items-center gap-2">
        {/* Active Broker Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setBrokerMenuOpen(!brokerMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:border-amber-400/40 hover:bg-white/[0.06] text-xs font-semibold text-white transition-all shadow-sm font-mono"
          >
            <Layers className="w-3.5 h-3.5 text-amber-400" />
            <span>{activeBroker}</span>
            <ChevronDown className="w-3 h-3 text-zinc-400" />
          </button>

          {brokerMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-[#0D1117] border border-white/10 shadow-[0_12px_35px_rgba(0,0,0,0.8)] py-1.5 z-50 animate-in fade-in zoom-in-95 backdrop-blur-2xl">
              <div className="px-3 py-1 text-[10px] font-bold text-zinc-400 uppercase font-mono border-b border-white/10 mb-1">
                Select Execution Route
              </div>
              {brokers.map((b) => (
                <button
                  key={b.id}
                  onClick={() => {
                    setActiveBroker(b.id);
                    setBrokerMenuOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs transition-colors flex items-center justify-between ${
                    activeBroker === b.id
                      ? "bg-amber-400/15 text-amber-400 font-bold"
                      : "text-zinc-300 hover:bg-white/[0.06] hover:text-white"
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{b.name}</span>
                    <span className="text-[9px] text-zinc-400 font-mono">{b.tag}</span>
                  </div>
                  {activeBroker === b.id && <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)]" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Master Live Trading Safety Gate Toggle */}
        <button
          onClick={() => setLiveTradingEnabled(!liveTradingEnabled)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-2xl text-xs font-bold font-mono transition-all border shadow-sm ${
            liveTradingEnabled
              ? "bg-rose-600 text-white border-rose-500 shadow-[0_0_15px_rgba(225,29,72,0.4)] animate-pulse"
              : "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25"
          }`}
        >
          {liveTradingEnabled ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
          <span>{liveTradingEnabled ? "LIVE REAL" : "PAPER MODE"}</span>
        </button>

        {/* Emergency Kill Switch */}
        {emergencyKillActive ? (
          <button
            onClick={resetEmergencyStop}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-rose-600 text-white border border-rose-500 font-bold text-xs shadow-[0_0_20px_rgba(225,29,72,0.6)] hover:bg-rose-500 transition-all animate-bounce font-mono"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>RESET ESTOP</span>
          </button>
        ) : (
          <button
            onClick={triggerEmergencyStop}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold text-xs transition-all shadow-sm font-mono"
            title="Emergency Kill Switch: Stops scanning and flattens positions"
          >
            <Power className="w-3.5 h-3.5" />
            <span>KILL SWITCH</span>
          </button>
        )}

        {/* Live IST Time */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-white/[0.02] border border-white/[0.05] text-xs font-mono text-zinc-400">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          <span>{istTime || "Loading..."}</span>
        </div>
      </div>
    </header>
  );
}
