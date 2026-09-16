import React from "react";
import { ThinkingOrb, type CompanionCoreState } from "./ThinkingOrb";

export type { CompanionCoreState };

interface HolographicCoreProps {
  state: CompanionCoreState;
  audioLevel?: number;
  size?: number;
  className?: string;
  onInteractivityClick?: () => void;
}

export const HolographicCore: React.FC<HolographicCoreProps> = ({
  state = "idle",
  audioLevel = 0,
  size = 380,
  className = "",
  onInteractivityClick,
}) => {
  return (
    <ThinkingOrb
      state={state}
      audioLevel={audioLevel}
      size={size}
      className={className}
      onInteractivityClick={onInteractivityClick}
    />
  );
};
