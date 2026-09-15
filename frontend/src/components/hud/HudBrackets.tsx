import React from "react";

interface HudCardProps {
  children: React.ReactNode;
  className?: string;
  tag?: string;
  subtag?: string;
  active?: boolean;
  glow?: "blush" | "copper" | "cyan" | "amber" | "green";
}

export const HudCard: React.FC<HudCardProps> = ({
  children,
  className = "",
  tag,
  subtag,
  active = false,
  glow = "blush",
}) => {
  const cornerBorder =
    glow === "copper"
      ? "border-accent"
      : glow === "amber"
      ? "border-[#ffaa00]"
      : glow === "green"
      ? "border-[#5fa88f]"
      : glow === "cyan"
      ? "border-cyber-cyan"
      : "border-blush-100";

  const borderClass =
    glow === "copper"
      ? "border-accent/35 hover:border-accent/65"
      : glow === "amber"
      ? "border-molten/30 hover:border-molten/60"
      : glow === "green"
      ? "border-verdigris/30 hover:border-verdigris/60"
      : glow === "cyan"
      ? "border-cyber-cyan/25 hover:border-cyber-cyan/50"
      : "border-blush-100/20 hover:border-blush-100/45";

  return (
    <div
      className={`relative bg-[#1A0A0F]/85 backdrop-blur-2xl border ${borderClass} transition-all duration-200 rounded-2xl p-5 shadow-[0_12px_36px_rgba(10,3,6,0.35),inset_0_1px_0_rgba(246,230,234,0.1)] ${
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
        <div className="absolute top-3 right-3 flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-wider text-text-muted select-none pointer-events-none">
          {tag && (
            <span className="px-2 py-0.5 rounded-md bg-blush-100/10 border border-blush-100/25 text-blush-100 font-semibold shadow-sm">
              {tag}
            </span>
          )}
          {subtag && (
            <span className="text-blush-300/40 hidden sm:inline">[{subtag}]</span>
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
