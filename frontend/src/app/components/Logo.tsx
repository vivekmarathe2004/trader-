import React from "react";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

export function Logo({ size = "md", showText = true, className = "" }: LogoProps) {
  const dimensions = {
    sm: { icon: "w-7 h-7", text: "text-xs", badge: "text-[9px]" },
    md: { icon: "w-9 h-9", text: "text-sm", badge: "text-[10px]" },
    lg: { icon: "w-11 h-11", text: "text-lg", badge: "text-xs" },
  }[size];

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Futuristic Quantum Hex-Prism Emblem */}
      <div className={`relative ${dimensions.icon} rounded-2xl bg-gradient-to-br from-amber-400 via-amber-500 to-yellow-600 p-[1.5px] shadow-[0_0_20px_rgba(245,158,11,0.35)] flex-shrink-0 group-hover:shadow-[0_0_28px_rgba(245,158,11,0.55)] transition-all duration-300`}>
        <div className="w-full h-full rounded-[14px] bg-[#0A0D14] flex items-center justify-center relative overflow-hidden">
          {/* Ambient Inner Gradient Mesh */}
          <div className="absolute inset-0 bg-gradient-to-br from-amber-400/20 via-transparent to-emerald-400/10 pointer-events-none" />
          
          <svg
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-5 h-5 relative z-10"
          >
            {/* Dynamic Geometric Delta / Energy Chevron */}
            <path
              d="M12 3L20 8.5V15.5L12 21L4 15.5V8.5L12 3Z"
              stroke="url(#valexis_gold)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="opacity-70"
            />
            <path
              d="M12 7L16.5 12L12 17L7.5 12L12 7Z"
              fill="url(#valexis_gold)"
              className="drop-shadow-[0_0_6px_rgba(245,158,11,0.8)]"
            />
            <path
              d="M7.5 12H16.5M12 7V17"
              stroke="#0A0D14"
              strokeWidth="1.2"
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id="valexis_gold" x1="4" y1="3" x2="20" y2="21" gradientUnits="userSpaceOnUse">
                <stop stopColor="#FBBF24" />
                <stop offset="0.5" stopColor="#F59E0B" />
                <stop offset="1" stopColor="#10B981" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5 leading-none">
            <span className={`font-black tracking-wider text-white ${dimensions.text} font-mono`}>
              VALEXIS
            </span>
            <span className={`px-1.5 py-0.5 rounded-md bg-amber-500/15 text-amber-400 font-mono font-bold border border-amber-500/30 ${dimensions.badge}`}>
              QUANT
            </span>
          </div>
          <span className="text-[9px] text-zinc-400 font-mono tracking-widest uppercase mt-0.5">
            Autonomous Matrix
          </span>
        </div>
      )}
    </div>
  );
}
