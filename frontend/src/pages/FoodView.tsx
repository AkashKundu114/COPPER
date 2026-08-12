import React from "react";
import { AlertCircle } from "lucide-react";

export const FoodView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Food & Nutrition Organizer</h1>
        <p className="text-xs text-gray-400 font-mono">Meal logs, grocery lists, and budget-conscious food planning</p>
      </div>

      {/* Non-Medical Disclaimer Banner */}
      <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-500/30 text-xs flex items-center gap-2 text-blue-300">
        <AlertCircle size={16} className="text-blue-400 shrink-0" />
        <span>General information disclaimer: COPPER provides food organization and estimates only. Not medical or dietary advice.</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
          <h3 className="font-bold text-white uppercase tracking-wider text-[11px]">Today's Meals Log</h3>
          <div className="space-y-2">
            <div className="p-2.5 rounded bg-black/40 border border-white/5 flex justify-between">
              <span>Breakfast: Oatmeal & Protein Shake</span>
              <span className="text-gray-400">450 kcal</span>
            </div>
            <div className="p-2.5 rounded bg-black/40 border border-white/5 flex justify-between">
              <span>Lunch: Grilled Chicken Salad & Quinoa</span>
              <span className="text-gray-400">650 kcal</span>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
          <h3 className="font-bold text-white uppercase tracking-wider text-[11px]">Grocery Checklist</h3>
          <div className="space-y-1 text-gray-300">
            <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" defaultChecked className="rounded accent-[#ff5722]" /> Oats & Almond Milk</label>
            <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" defaultChecked className="rounded accent-[#ff5722]" /> Chicken Breasts</label>
            <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" className="rounded accent-[#ff5722]" /> Mixed Greens & Olive Oil</label>
          </div>
        </div>
      </div>
    </div>
  );
};
