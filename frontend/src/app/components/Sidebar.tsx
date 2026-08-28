"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useNav } from "@/lib/nav-context";
import { Logo } from "./Logo";
import {
  Compass,
  LineChart,
  Radio,
  PlayCircle,
  Briefcase,
  Key,
  Shield,
  Activity,
  ScrollText,
  TrendingUp,
  Cpu,
  ChevronRight,
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();
  const { activeBroker, liveTradingEnabled } = useNav();

  const navItems = [
    {
      group: "COMMAND & EXECUTION",
      links: [
        {
          href: "/",
          label: "Cockpit Overview",
          icon: Compass,
          iconColor: "text-amber-400",
          bgColor: "bg-amber-500/10",
          borderColor: "border-amber-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(245,158,11,0.25)]",
        },
        {
          href: "/operations/auto-trade",
          label: "AutoTrader Engine",
          icon: PlayCircle,
          iconColor: "text-purple-400",
          bgColor: "bg-purple-500/10",
          borderColor: "border-purple-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(168,85,247,0.25)]",
        },
        {
          href: "/operations/positions",
          label: "Positions & Orders",
          icon: Briefcase,
          iconColor: "text-blue-400",
          bgColor: "bg-blue-500/10",
          borderColor: "border-blue-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(59,130,246,0.25)]",
        },
      ],
    },
    {
      group: "MARKET INTELLIGENCE",
      links: [
        {
          href: "/markets",
          label: "Market Monitor",
          icon: LineChart,
          iconColor: "text-cyan-400",
          bgColor: "bg-cyan-500/10",
          borderColor: "border-cyan-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(6,182,212,0.25)]",
        },
        {
          href: "/signals",
          label: "Signals & Scans",
          icon: Radio,
          iconColor: "text-emerald-400",
          bgColor: "bg-emerald-500/10",
          borderColor: "border-emerald-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(16,185,129,0.25)]",
        },
      ],
    },
    {
      group: "SYSTEM CONTROLS",
      links: [
        {
          href: "/operations/brokers",
          label: "Broker API Keys",
          icon: Key,
          iconColor: "text-yellow-400",
          bgColor: "bg-yellow-500/10",
          borderColor: "border-yellow-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(234,179,8,0.25)]",
        },
        {
          href: "/operations/risk",
          label: "Risk Boundaries",
          icon: Shield,
          iconColor: "text-rose-400",
          bgColor: "bg-rose-500/10",
          borderColor: "border-rose-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(244,63,94,0.25)]",
        },
        {
          href: "/operations/health",
          label: "Control Center",
          icon: Activity,
          iconColor: "text-teal-400",
          bgColor: "bg-teal-500/10",
          borderColor: "border-teal-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(20,184,166,0.25)]",
        },
        {
          href: "/operations/logs",
          label: "Audit Logs",
          icon: ScrollText,
          iconColor: "text-slate-300",
          bgColor: "bg-slate-500/10",
          borderColor: "border-slate-500/30",
          activeGlow: "shadow-[0_0_15px_rgba(148,163,184,0.25)]",
        },
      ],
    },
  ];

  return (
    <aside className="w-64 h-screen flex-shrink-0 bg-[#070A0F]/95 backdrop-blur-2xl border-r border-white/[0.06] flex flex-col justify-between p-4 select-none z-30">
      <div className="space-y-5">
        {/* Brand Header */}
        <Link href="/" className="flex items-center justify-between px-2 py-2 group rounded-2xl hover:bg-white/[0.03] transition-colors">
          <Logo size="md" showText={true} />
        </Link>

        {/* Live Broker Pill Under Logo */}
        <div className="mx-2 px-3 py-1.5 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center justify-between text-[10px] font-mono text-zinc-400">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${liveTradingEnabled ? "bg-rose-400 animate-pulse" : "bg-emerald-400"}`} />
            <span className="font-semibold text-zinc-300">{activeBroker}</span>
          </div>
          <span className={`px-1.5 py-0.2 rounded font-bold ${
            liveTradingEnabled
              ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
              : "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
          }`}>
            {liveTradingEnabled ? "LIVE REAL" : "PAPER MODE"}
          </span>
        </div>

        {/* Navigation Sections */}
        <div className="space-y-4">
          {navItems.map((sec, sIdx) => (
            <div key={sIdx} className="space-y-1">
              <div className="px-2.5 text-[9px] font-bold tracking-widest text-zinc-400 uppercase font-mono">
                {sec.group}
              </div>
              <nav className="space-y-1">
                {sec.links.map((link) => {
                  const Icon = link.icon;
                  const isActive = pathname === link.href;
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      prefetch={true}
                      className={`group flex items-center justify-between px-3 py-2 rounded-2xl text-xs font-semibold transition-all duration-200 border ${
                        isActive
                          ? `bg-gradient-to-r from-white/[0.08] to-white/[0.02] text-white ${link.borderColor} ${link.activeGlow} font-bold shadow-md`
                          : "border-transparent text-zinc-400 hover:text-white hover:bg-white/[0.04] hover:border-white/5"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`w-7 h-7 rounded-xl flex items-center justify-center border transition-all ${
                            link.bgColor
                          } ${link.borderColor} ${
                            isActive ? "scale-105 shadow-sm" : "group-hover:scale-105"
                          }`}
                        >
                          <Icon className={`w-3.5 h-3.5 ${link.iconColor}`} />
                        </div>
                        <span className="font-medium tracking-wide">{link.label}</span>
                      </div>

                      {isActive && (
                        <div className="w-1.5 h-3.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.6)]" />
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>
      </div>

      {/* Footer System Status */}
      <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-zinc-400 px-1">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
          <span className="text-zinc-300 font-medium text-[10px]">Deterministic Core</span>
        </div>
        <span className="text-[9px] text-amber-400 font-bold bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">
          v2.0
        </span>
      </div>
    </aside>
  );
}
