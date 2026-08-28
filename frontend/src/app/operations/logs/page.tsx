"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../../components/GlassCard";
import { PageHeader } from "../../components/PageHeader";
import { api } from "@/lib/api";
import { ScrollText, Search, RefreshCw, Filter, ShieldCheck, Hash } from "lucide-react";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [search, setSearch] = useState<string>("");
  const [levelFilter, setLevelFilter] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const fetchLogs = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const data = await api.getLogs(150, levelFilter || undefined, search || undefined).catch(() => []);
      setLogs(data || []);
    } catch (e) {
      console.warn("Failed to fetch logs:", e);
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(true);
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        fetchLogs(false);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [levelFilter, search]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Audit Logs & Cryptographic Trail"
        subtitle="Append-only immutable audit trail recording every order transition, signal evaluation, and risk decision with SHA-256 hashes."
        actions={
          <button
            onClick={() => fetchLogs(true)}
            className="p-2 rounded-lg bg-surface border border-primary/15 hover:border-accent text-primary"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        }
      />

      {/* Filter & Search Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 relative min-w-[240px]">
          <Search className="w-4 h-4 text-primary-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search audit trail by symbol, strategy, or order ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface border border-primary/15 text-xs text-primary font-mono"
          />
        </div>

        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="p-2 rounded-lg bg-surface border border-primary/15 text-xs font-mono font-semibold text-primary"
        >
          <option value="">All Severity Levels</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
      </div>

      {/* Log Feed */}
      <GlassCard className="space-y-2 p-4 font-mono text-xs max-h-[70vh] overflow-y-auto">
        {logs.length === 0 ? (
          <div className="py-12 text-center text-primary-muted">No audit logs matching query.</div>
        ) : (
          <div className="divide-y divide-primary/5">
            {logs.map((l, idx) => {
              const isError = l.level === "ERROR" || l.level === "CRITICAL";
              const isWarning = l.level === "WARNING";

              return (
                <div key={idx} className="py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-primary/5 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-primary-muted">{l.timestamp}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                      isError
                        ? "bg-loss text-white"
                        : isWarning
                        ? "bg-amber-500 text-white"
                        : "bg-primary/10 text-primary"
                    }`}>
                      {l.level}
                    </span>
                    <span className="text-primary font-medium">{l.message}</span>
                  </div>
                  <div className="text-[10px] text-primary-muted flex items-center gap-1.5">
                    <Hash className="w-3 h-3 text-accent" />
                    <span>{l.module}:{l.line}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
