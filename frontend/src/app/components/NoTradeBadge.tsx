import React from "react";
import { AlertCircle, Ban } from "lucide-react";

interface NoTradeBadgeProps {
  reason: string;
}

export function NoTradeBadge({ reason }: NoTradeBadgeProps) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-loss-subtle border border-loss-border text-loss text-xs font-mono font-medium">
      <Ban className="w-3.5 h-3.5 flex-shrink-0" />
      <span>{reason}</span>
    </div>
  );
}
