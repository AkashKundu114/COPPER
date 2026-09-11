import React, { useState } from "react";
import { type BranchItem } from "../../services/api";

interface BranchGraphProps {
  branches: BranchItem[];
  activeBranchId: string;
  onSelectBranch: (branchId: string) => void;
  maxHeight?: number;
}

const COLORS = [
  "text-accent-400", // Main
  "text-amber-400",
  "text-emerald-400",
  "text-rose-400",
  "text-cyan-400",
];

const STROKE_COLORS = [
  "stroke-accent-400", // Main
  "stroke-amber-400",
  "stroke-emerald-400",
  "stroke-rose-400",
  "stroke-cyan-400",
];

const FILL_COLORS = [
  "fill-accent-400", // Main
  "fill-amber-400",
  "fill-emerald-400",
  "fill-rose-400",
  "fill-cyan-400",
];

export const BranchGraph: React.FC<BranchGraphProps> = ({
  branches,
  activeBranchId,
  onSelectBranch,
  maxHeight = 300,
}) => {
  const [hoveredBranchId, setHoveredBranchId] = useState<string | null>(null);

  // Sorting branches: main first, then by divergence index
  const sortedBranches = [...branches].sort((a, b) => {
    if (a.is_main) return -1;
    if (b.is_main) return 1;
    return (a.divergence_index || 0) - (b.divergence_index || 0);
  });

  const branchLanes = new Map<string, number>();
  sortedBranches.forEach((b, i) => {
    branchLanes.set(b.branch_id, i);
  });

  // Calculate layout parameters
  const Y_SPACING = 30;
  const X_SPACING = 40;
  const NODE_RADIUS = 5;
  const MARGIN_X = 20;
  const MARGIN_Y = 20;

  // Find max messages count for the height
  const maxMessages = Math.max(...sortedBranches.map((b) => b.messages_count || 1), 5);
  const totalHeight = maxMessages * Y_SPACING + MARGIN_Y * 2;
  const totalWidth = Math.max(sortedBranches.length * X_SPACING + MARGIN_X * 2, 200);

  const getLaneX = (lane: number) => MARGIN_X + lane * X_SPACING;
  const getY = (index: number) => MARGIN_Y + index * Y_SPACING;

  return (
    <div 
      className="w-full overflow-auto bg-slate-950/80 border-b border-slate-800 custom-scrollbar" 
      style={{ maxHeight: `${maxHeight}px` }}
    >
      <div className="relative min-w-max p-4" style={{ height: `${totalHeight}px` }}>
        <svg
          width={totalWidth}
          height={totalHeight}
          className="absolute top-0 left-0"
          role="img"
          aria-label="Conversation branch graph visualization"
        >
          {/* Draw paths first so they appear under nodes */}
          {sortedBranches.map((branch) => {
            const lane = branchLanes.get(branch.branch_id) || 0;
            const isMain = lane === 0;
            const colorClass = STROKE_COLORS[lane % STROKE_COLORS.length];
            const isActive = branch.branch_id === activeBranchId;
            
            const startYIndex = branch.divergence_index || 0;
            const endYIndex = (branch.messages_count || 1) - 1;
            
            let d = "";
            if (isMain) {
              d = `M ${getLaneX(lane)} ${getY(0)} L ${getLaneX(lane)} ${getY(endYIndex)}`;
            } else {
              // Find parent lane (default to main)
              const parentBranch = sortedBranches.find((b) => b.branch_id === branch.parent_session_id) || sortedBranches[0];
              const parentLane = parentBranch ? (branchLanes.get(parentBranch.branch_id) || 0) : 0;
              
              const startX = getLaneX(parentLane);
              const targetX = getLaneX(lane);
              const branchY = getY(startYIndex);
              
              d = `M ${startX} ${branchY} C ${targetX} ${branchY}, ${targetX} ${branchY + Y_SPACING/2}, ${targetX} ${branchY + Y_SPACING} L ${targetX} ${getY(endYIndex)}`;
              
              // If merged, curve back to main (assuming merges back to main for simplicity if status is merged)
              if (branch.status === "merged") {
                d += ` C ${targetX} ${getY(endYIndex) + Y_SPACING/2}, ${startX} ${getY(endYIndex) + Y_SPACING/2}, ${startX} ${getY(endYIndex) + Y_SPACING}`;
              }
            }

            return (
              <path
                key={`path-${branch.branch_id}`}
                d={d}
                fill="none"
                strokeWidth={isActive ? 3 : 2}
                className={`${colorClass} ${isActive ? "opacity-100" : "opacity-50"} transition-all`}
              />
            );
          })}

          {/* Draw nodes */}
          {sortedBranches.map((branch) => {
            const lane = branchLanes.get(branch.branch_id) || 0;
            const isMain = lane === 0;
            const strokeColor = STROKE_COLORS[lane % STROKE_COLORS.length];
            const fillColor = FILL_COLORS[lane % FILL_COLORS.length];
            const isActive = branch.branch_id === activeBranchId;
            
            const startYIndex = branch.divergence_index || 0;
            const endYIndex = (branch.messages_count || 1) - 1;
            
            const nodes = [];
            
            // For main branch, draw nodes from 0 to endYIndex
            // For other branches, draw from startYIndex + 1 to endYIndex
            const startNodeIdx = isMain ? 0 : startYIndex;
            
            for (let i = startNodeIdx; i <= endYIndex; i++) {
              const x = getLaneX(lane);
              const y = getY(i);
              
              // Draw divergence diamond at divergence index
              if (!isMain && i === startYIndex) {
                // The divergence point is actually on the parent lane, so we draw it there
                const parentBranch = sortedBranches.find((b) => b.branch_id === branch.parent_session_id) || sortedBranches[0];
                const parentLane = parentBranch ? (branchLanes.get(parentBranch.branch_id) || 0) : 0;
                
                nodes.push(
                  <rect
                    key={`div-${branch.branch_id}-${i}`}
                    x={getLaneX(parentLane) - 6}
                    y={y - 6}
                    width={12}
                    height={12}
                    transform={`rotate(45 ${getLaneX(parentLane)} ${y})`}
                    className={`${fillColor} cursor-pointer transition-all ${isActive ? "scale-125" : ""}`}
                    onClick={() => onSelectBranch(branch.branch_id)}
                    onMouseEnter={() => setHoveredBranchId(branch.branch_id)}
                    onMouseLeave={() => setHoveredBranchId(null)}
                  />
                );
                continue;
              }
              
              nodes.push(
                <circle
                  key={`node-${branch.branch_id}-${i}`}
                  cx={x}
                  cy={y}
                  r={isActive ? NODE_RADIUS + 1 : NODE_RADIUS}
                  className={`cursor-pointer transition-all ${isActive ? fillColor : "fill-slate-900"} ${strokeColor} stroke-2`}
                  onClick={() => onSelectBranch(branch.branch_id)}
                  onMouseEnter={() => setHoveredBranchId(branch.branch_id)}
                  onMouseLeave={() => setHoveredBranchId(null)}
                />
              );
            }
            return <g key={`nodes-${branch.branch_id}`}>{nodes}</g>;
          })}
        </svg>

        {/* HTML overlay for tooltips/interactions */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
          {sortedBranches.map((branch) => {
            const lane = branchLanes.get(branch.branch_id) || 0;
            const isMain = lane === 0;
            const isActive = branch.branch_id === activeBranchId;
            const isHovered = hoveredBranchId === branch.branch_id;
            
            // Place label near the last node
            const endYIndex = (branch.messages_count || 1) - 1;
            const x = getLaneX(lane);
            const y = getY(endYIndex);
            
            const colorText = COLORS[lane % COLORS.length];
            const colorBorder = STROKE_COLORS[lane % STROKE_COLORS.length].replace("stroke-", "border-");

            return (
              <div 
                key={`html-${branch.branch_id}`}
                className="absolute"
                style={{ left: `${x + 15}px`, top: `${y - 10}px` }}
              >
                <div 
                  className={`pointer-events-auto flex items-center gap-2 px-2 py-1 rounded bg-slate-900 border ${
                    isActive ? colorBorder : "border-slate-800"
                  } shadow-md transition-all cursor-pointer ${
                    isHovered || isActive ? "opacity-100" : "opacity-60"
                  }`}
                  onClick={() => onSelectBranch(branch.branch_id)}
                  onMouseEnter={() => setHoveredBranchId(branch.branch_id)}
                  onMouseLeave={() => setHoveredBranchId(null)}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select branch ${branch.title}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectBranch(branch.branch_id);
                    }
                  }}
                >
                  <span className={`text-[10px] font-sans font-bold whitespace-nowrap ${colorText}`}>
                    {branch.title}
                  </span>
                  <span className="text-[9px] font-mono text-slate-400 bg-slate-950 px-1 rounded">
                    {branch.messages_count || 0}
                  </span>
                </div>
                
                {/* Detailed Tooltip on Hover */}
                {isHovered && branch.divergence_message && !isMain && (
                  <div className="absolute top-full mt-1 left-0 z-50 w-48 p-2 rounded-lg bg-slate-950 border border-slate-700 shadow-xl pointer-events-none">
                    <div className="text-[9px] uppercase font-bold text-slate-500 mb-1">Diverged at</div>
                    <div className="text-[10px] text-slate-300 font-sans line-clamp-3 leading-snug">
                      "{branch.divergence_message.content}"
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
