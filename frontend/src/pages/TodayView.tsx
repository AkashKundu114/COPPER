import React, { useState } from "react";

export const TodayView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"day" | "week" | "month">("day");

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      {}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Schedule & Today Overview</h1>
          <p className="text-xs text-gray-400 font-mono">Day, Week, and Month planning views</p>
        </div>
        <div className="flex gap-1 p-1 bg-[#14141a] rounded-lg border border-white/10 text-xs font-mono">
          {(["day", "week", "month"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 rounded capitalize transition-all ${
                activeTab === tab ? "bg-[#b87333]/30 text-[#ff5722] border border-[#ff5722]/40" : "text-gray-400 hover:text-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Empty State for Recommendations */}
      <div className="p-4 rounded-xl bg-[#14141a] border border-white/5 text-xs text-center text-gray-500 font-mono">
        No active recommendations from C.O.P.P.E.R. at this time.
      </div>

      {/* Empty State for Timeline */}
      <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-4">
        <h3 className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">Today's Timeline</h3>
        <div className="flex flex-col items-center justify-center p-8 text-gray-500 font-mono text-xs">
          <p>Your schedule is clear for today.</p>
        </div>
      </div>
    </div>
  );
};
