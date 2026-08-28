import React from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  badge?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, badge, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3.5 border-b border-white/[0.06]">
      <div className="min-w-0 flex-shrink">
        <div className="flex items-center gap-2.5 flex-wrap">
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight font-sans truncate">{title}</h1>
          {badge && (
            <span className="px-2.5 py-0.5 text-[11px] font-bold rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 font-mono">
              {badge}
            </span>
          )}
        </div>
        {subtitle && <p className="text-xs text-zinc-400 mt-0.5 font-medium truncate sm:max-w-xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap flex-shrink-0">{actions}</div>}
    </div>
  );
}
