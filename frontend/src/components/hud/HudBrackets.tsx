import React from "react";

interface HudCardProps {
  children: React.ReactNode;
  className?: string;
  tag?: string;
  subtag?: string;
  active?: boolean;
  glow?: "cyan" | "amber" | "green";
}

export const HudCard: React.FC<HudCardProps> = ({
  children,
  className = "",
  tag,
  subtag,
  active = false,
  glow = "cyan",
}) => {
  const cornerBorder =
    glow === "amber"
      ? "border-[#ffaa00]"
      : glow === "green"
      ? "border-[#00ff88]"
      : "border-cyber-cyan";

  const borderClass =
    glow === "amber"
      ? "border-molten/30 hover:border-molten/60"
      : glow === "green"
      ? "border-verdigris/30 hover:border-verdigris/60"
      : "border-cyber-cyan/25 hover:border-cyber-cyan/50";

  return (
    <div
      className={`relative bg-[#070b13]/85 backdrop-blur-xl border ${borderClass} transition-all duration-300 rounded-xl p-5 shadow-hud ${
        active ? "hud-card-active" : ""
      } ${className}`}
    >
      {/* 4 Tech Corner Brackets */}
      <span className={`absolute -top-[1px] -left-[1px] w-2.5 h-2.5 border-t-2 border-l-2 ${cornerBorder} pointer-events-none rounded-tl-sm`} />
      <span className={`absolute -top-[1px] -right-[1px] w-2.5 h-2.5 border-t-2 border-r-2 ${cornerBorder} pointer-events-none rounded-tr-sm`} />
      <span className={`absolute -bottom-[1px] -left-[1px] w-2.5 h-2.5 border-b-2 border-l-2 ${cornerBorder} pointer-events-none rounded-bl-sm`} />
      <span className={`absolute -bottom-[1px] -right-[1px] w-2.5 h-2.5 border-b-2 border-r-2 ${cornerBorder} pointer-events-none rounded-br-sm`} />

      {/* Optional Top Right Technical Metadata Badge */}
      {(tag || subtag) && (
        <div className="absolute top-2.5 right-3 flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-wider text-text-muted select-none pointer-events-none">
          {tag && (
            <span className="px-1.5 py-0.5 rounded bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan font-semibold">
              {tag}
            </span>
          )}
          {subtag && (
            <span className="text-zinc-500 hidden sm:inline">[{subtag}]</span>
          )}
        </div>
      )}

      {children}
    </div>
  );
};

export const HudCornerMarks: React.FC<{ color?: string }> = ({
  color = "text-cyber-cyan/40",
}) => {
  return (
    <>
      <div className={`absolute top-1 left-1 font-mono text-[8px] ${color} select-none pointer-events-none`}>
        +
      </div>
      <div className={`absolute top-1 right-1 font-mono text-[8px] ${color} select-none pointer-events-none`}>
        +
      </div>
      <div className={`absolute bottom-1 left-1 font-mono text-[8px] ${color} select-none pointer-events-none`}>
        +
      </div>
      <div className={`absolute bottom-1 right-1 font-mono text-[8px] ${color} select-none pointer-events-none`}>
        +
      </div>
    </>
  );
};
