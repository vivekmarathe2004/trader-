import React from "react";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export function GlassCard({ children, className = "", hoverEffect = true, ...props }: GlassCardProps) {
  return (
    <div
      className={`relative rounded-3xl bg-gradient-to-b from-[#0F1420]/80 via-[#0A0E17]/80 to-[#080B12]/80 backdrop-blur-2xl border border-white/[0.06] shadow-[0_10px_35px_rgba(0,0,0,0.5)] overflow-hidden transition-all duration-300 p-5 group ${
        hoverEffect
          ? "hover:border-amber-400/25 hover:shadow-[0_16px_45px_rgba(0,0,0,0.7),0_0_25px_rgba(245,158,11,0.06)] hover:-translate-y-0.5"
          : ""
      } ${className}`}
      {...props}
    >
      {/* Subtle Specular Top Arc Highlight */}
      <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/[0.12] to-transparent pointer-events-none" />
      {/* Ambient Top Corner Light Accent */}
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-amber-500/[0.03] rounded-full blur-2xl pointer-events-none group-hover:bg-amber-500/[0.06] transition-all duration-500" />
      {children}
    </div>
  );
}
