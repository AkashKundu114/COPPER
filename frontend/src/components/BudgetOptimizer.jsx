import React, { useState } from "react";
import {
  TrendingUp,
  Sliders,
  DollarSign,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  RefreshCw,
} from "lucide-react";

export const BudgetOptimizer = ({
  optimizationData,
  onApplyOptimization,
  onRecalculate,
  campaigns = [],
}) => {
  const [isApplying, setIsApplying] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState(false);
  const [customBudget, setCustomBudget] = useState(
    optimizationData?.total_budget || 8100
  );

  const opt = optimizationData;
  const currentAlloc = opt?.current_allocation || {};
  const optimizedAlloc = opt?.optimized_allocation || {};
  const campaignIds = Object.keys(currentAlloc);

  const getCampaignName = (cid) => {
    const found = campaigns.find((c) => c.campaign_id === cid);
    return found?.campaign_name || cid;
  };

  const handleApply = () => {
    setIsApplying(true);
    setTimeout(() => {
      setIsApplying(false);
      setAppliedSuccess(true);
      if (onApplyOptimization) {
        onApplyOptimization(opt);
      }
      setTimeout(() => setAppliedSuccess(false), 5000);
    }, 800);
  };

  const handleRunOptimize = (e) => {
    e.preventDefault();
    if (onRecalculate) {
      onRecalculate(Number(customBudget));
    }
  };

  // Find max spend across both current and optimized to scale bars
  const maxSpend = Math.max(
    ...Object.values(currentAlloc),
    ...Object.values(optimizedAlloc),
    100
  );

  return (
    <div className="bg-surface-elevated border border-border-subtle rounded-xl p-5 backdrop-blur-md shadow-lg flex flex-col gap-5">
      {/* Header and KPI cards */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 text-white shadow-md shadow-cyan-950/50">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text flex items-center gap-2">
              Autonomous Budget Optimizer (SLSQP Logarithmic Yield)
            </h3>
            <p className="text-xs text-text-secondary">
              DeltaX-style diminishing returns curve fitting to maximize conversions under total budget constraint
            </p>
          </div>
        </div>

        {/* Custom Budget Form */}
        <form onSubmit={handleRunOptimize} className="flex items-center gap-2">
          <div className="relative">
            <span className="absolute left-2.5 top-2 text-xs text-text-tertiary">$</span>
            <input
              type="number"
              value={customBudget}
              onChange={(e) => setCustomBudget(Number(e.target.value))}
              className="bg-canvas border border-border-highlight rounded-lg pl-6 pr-3 py-1.5 text-xs text-text font-mono focus:border-cyan-400 focus:outline-none w-28"
              placeholder="Budget"
            />
          </div>
          <button
            type="submit"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-active hover:bg-surface-spotlight text-text text-xs font-medium rounded-lg border border-border-highlight transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>Recalibrate</span>
          </button>
        </form>
      </div>

      {/* Metrics Highlights Card */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-4 rounded-xl bg-canvas/70 border border-border-subtle flex flex-col justify-between">
          <span className="text-xs text-text-secondary font-medium">Projected Improvement</span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold text-emerald-400 font-mono">
              +{opt?.improvement_percent?.toFixed(1) || "0.0"}%
            </span>
            <span className="text-xs text-emerald-500/80 font-medium flex items-center">
              <TrendingUp className="w-3 h-3 mr-0.5" /> Conversions
            </span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1">
            Zero additional ad budget required
          </span>
        </div>

        <div className="p-4 rounded-xl bg-canvas/70 border border-border-subtle flex flex-col justify-between">
          <span className="text-xs text-text-secondary font-medium">Daily Conversions</span>
          <div className="flex items-center gap-2 mt-2 text-text font-mono">
            <span className="text-xl text-text-secondary">
              {opt?.projected_current_conversions?.toFixed(1) || 0}
            </span>
            <ArrowRight className="w-4 h-4 text-text-tertiary" />
            <span className="text-2xl font-bold text-cyan-400">
              {opt?.projected_optimized_conversions?.toFixed(1) || 0}
            </span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1">
            +
            {(
              (opt?.projected_optimized_conversions || 0) -
              (opt?.projected_current_conversions || 0)
            ).toFixed(1)}{" "}
            incremental daily orders
          </span>
        </div>

        <div className="p-4 rounded-xl bg-canvas/70 border border-border-subtle flex flex-col justify-between">
          <span className="text-xs text-text-secondary font-medium">Total Daily Budget</span>
          <div className="flex items-baseline gap-1 mt-2">
            <span className="text-2xl font-bold text-text font-mono">
              ${opt?.total_budget ? Number(opt.total_budget).toLocaleString() : "0"}
            </span>
            <span className="text-xs text-text-tertiary">/day</span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1">
            Sum constraint strictly preserved
          </span>
        </div>
      </div>

      {/* Allocation Comparison Bar Chart */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between text-xs text-text-secondary">
          <span className="font-semibold uppercase tracking-wider text-text-secondary">
            Current vs Optimized Daily Allocation
          </span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-surface-spotlight"></span>
              Current Spend
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500"></span>
              Optimal Reallocation
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-3 bg-surface-base/50 p-4 rounded-xl border border-border-subtle">
          {campaignIds.map((cid) => {
            const curVal = currentAlloc[cid] || 0;
            const optVal = optimizedAlloc[cid] || 0;
            const delta = optVal - curVal;
            const curPct = (curVal / maxSpend) * 100;
            const optPct = (optVal / maxSpend) * 100;

            return (
              <div key={cid} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-text">
                    {getCampaignName(cid)}
                  </span>
                  <div className="flex items-center gap-3 font-mono">
                    <span className="text-text-secondary">${curVal.toLocaleString()}</span>
                    <ArrowRight className="w-3 h-3 text-text-tertiary" />
                    <span className="text-cyan-300 font-semibold">
                      ${optVal.toLocaleString()}
                    </span>
                    <span
                      className={`text-[11px] font-semibold ${
                        delta > 0
                          ? "text-emerald-400"
                          : delta < 0
                          ? "text-amber-400"
                          : "text-text-tertiary"
                      }`}
                    >
                      ({delta > 0 ? "+" : ""}
                      {delta.toFixed(0)})
                    </span>
                  </div>
                </div>

                <div className="flex flex-col gap-1">
                  {/* Current Bar */}
                  <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-surface-spotlight h-full rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(2, curPct))}%` }}
                    />
                  </div>
                  {/* Optimized Bar */}
                  <div className="w-full bg-surface-elevated rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full rounded-full transition-all duration-500 shadow-sm"
                      style={{ width: `${Math.min(100, Math.max(2, optPct))}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Allocation Reasoning */}
      {opt?.reasoning && opt.reasoning.length > 0 && (
        <div className="flex flex-col gap-2 bg-surface-base p-4 rounded-xl border border-border-subtle">
          <span className="text-xs font-semibold text-text-secondary flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            DeltaX Model Reasoning &amp; Elasticity Analysis:
          </span>
          <ul className="flex flex-col gap-1.5 text-xs text-text-secondary">
            {opt.reasoning.map((r, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-cyan-500 mt-1">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Apply Optimization CTA */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-xs text-text-tertiary">
          *Applies bid cap and daily budget changes directly to simulated campaign ad sets.
        </div>
        <button
          onClick={handleApply}
          disabled={isApplying || appliedSuccess}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs transition-all shadow-lg ${
            appliedSuccess
              ? "bg-emerald-600 text-white shadow-emerald-950/50"
              : "bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white shadow-cyan-950/50"
          }`}
        >
          {appliedSuccess ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              <span>Optimization Applied!</span>
            </>
          ) : (
            <>
              <DollarSign className={`w-4 h-4 ${isApplying ? "animate-spin" : ""}`} />
              <span>{isApplying ? "Reallocating Pacing..." : "Apply Optimization"}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
