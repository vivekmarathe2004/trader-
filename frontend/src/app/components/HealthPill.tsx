import React from "react";

interface HealthPillProps {
  name: string;
  status: "HEALTHY" | "CONNECTED" | "ARMED" | "RUNNING" | "READY" | "SYNCED" | "STANDBY" | "WARNING_RECONCILIATION" | "ERROR" | "KILL_SWITCH_ACTIVE";
  latency?: number;
}

export function HealthPill({ name, status, latency }: HealthPillProps) {
  const isHealthy = ["HEALTHY", "CONNECTED", "ARMED", "RUNNING", "READY", "SYNCED"].includes(status);
  const isWarning = ["STANDBY", "WARNING_RECONCILIATION"].includes(status);

  let bgClass = "bg-profit-subtle border-profit-border text-profit";
  let dotClass = "bg-profit";

  if (isWarning) {
    bgClass = "bg-warning-subtle border-amber-200 text-warning";
    dotClass = "bg-warning";
  } else if (!isHealthy) {
    bgClass = "bg-loss-subtle border-loss-border text-loss";
    dotClass = "bg-loss";
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-md border text-xs font-mono font-medium ${bgClass}`}>
      <span className={`w-2 h-2 rounded-full ${dotClass}`} />
      <span className="font-semibold text-primary">{name}:</span>
      <span>{status}</span>
      {latency !== undefined && <span className="text-primary-muted text-[10px]">({latency.toFixed(1)}ms)</span>}
    </div>
  );
}
