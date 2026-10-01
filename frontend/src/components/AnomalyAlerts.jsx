import React, { useState } from "react";
import {
  AlertTriangle,
  ShieldAlert,
  Info,
  Wrench,
  CheckCircle2,
  Clock,
  Sparkles,
  Zap,
} from "lucide-react";

export const AnomalyAlerts = ({ anomalies = [], onAutoFixApplied }) => {
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [fixedAlerts, setFixedAlerts] = useState({});
  const [fixingId, setFixingId] = useState(null);

  const filtered = anomalies.filter((a) => {
    if (filterSeverity === "all") return true;
    return a.severity === filterSeverity;
  });

  const handleAutoFix = (idx, anom) => {
    setFixingId(idx);
    setTimeout(() => {
      setFixedAlerts((prev) => ({
        ...prev,
        [idx]: "Resolved: Bid adjustments applied via simulated ad-tech actuator.",
      }));
      setFixingId(null);
      if (onAutoFixApplied) {
        onAutoFixApplied(anom);
      }
    }, 700);
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case "critical":
        return {
          icon: ShieldAlert,
          bg: "bg-red-500/10 text-red-400 border-red-500/30",
          iconColor: "text-red-400",
        };
      case "warning":
        return {
          icon: AlertTriangle,
          bg: "bg-amber-500/10 text-amber-400 border-amber-500/30",
          iconColor: "text-amber-400",
        };
      default:
        return {
          icon: Info,
          bg: "bg-blue-500/10 text-blue-400 border-blue-500/30",
          iconColor: "text-blue-400",
        };
    }
  };

  return (
    <div className="bg-surface-elevated border border-border-subtle rounded-xl p-5 backdrop-blur-md shadow-lg flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
            <Zap className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text">
              Live Anomaly Feed ({anomalies.length})
            </h3>
            <p className="text-xs text-text-secondary">
              DeltaX automated detection: Statistical Z-Score, Trend MA, &amp; Burn Projection
            </p>
          </div>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-1 bg-canvas p-1 rounded-lg border border-border-subtle text-xs font-medium">
          {["all", "critical", "warning", "info"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2.5 py-1 rounded capitalize transition-all ${
                filterSeverity === sev
                  ? "bg-surface-active text-text shadow-sm"
                  : "text-text-secondary hover:text-text"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mb-2 opacity-80" />
          <p className="text-sm font-medium text-text">No active anomalies detected</p>
          <p className="text-xs text-text-tertiary max-w-sm mt-1">
            All advertising campaigns are performing within calibrated historical baselines.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3 max-h-[460px] overflow-y-auto pr-1">
          {filtered.map((anom, idx) => {
            const badge = getSeverityBadge(anom.severity);
            const Icon = badge.icon;
            const isFixed = Boolean(fixedAlerts[idx]);
            const isFixing = fixingId === idx;

            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition-all ${
                  isFixed
                    ? "bg-surface-base border-emerald-900/40 opacity-75"
                    : "bg-surface-base border-border-subtle/90 hover:border-border-highlight"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className={`p-1.5 rounded-lg border ${badge.bg}`}>
                      <Icon className="w-4 h-4" />
                    </div>

                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-semibold text-text">
                          {anom.campaign_name}
                        </span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full border uppercase font-mono tracking-wider font-semibold ${badge.bg}`}
                        >
                          {anom.severity}
                        </span>
                        <span className="text-xs text-text-tertiary font-mono">
                          {anom.metric_name} ({anom.deviation_percent > 0 ? "+" : ""}
                          {anom.deviation_percent}%)
                        </span>
                      </div>

                      <div className="mt-1 text-xs text-text-secondary">
                        <span className="text-text-secondary">Current: </span>
                        <span className="font-mono font-medium text-text">
                          {anom.current_value}
                        </span>
                        <span className="text-text-tertiary"> vs Expected: </span>
                        <span className="font-mono text-text-secondary">{anom.expected_value}</span>
                      </div>

                      <div className="mt-2 text-xs bg-surface-elevated border border-border-subtle rounded-lg p-2 text-cyan-300/90 flex items-start gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-cyan-400" />
                        <span>{anom.recommendation}</span>
                      </div>

                      {isFixed && (
                        <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{fixedAlerts[idx]}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Auto-Fix button */}
                  {anom.auto_fixable && !isFixed && (
                    <button
                      onClick={() => handleAutoFix(idx, anom)}
                      disabled={isFixing}
                      className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md shadow-cyan-950/40 disabled:opacity-50"
                    >
                      <Wrench className={`w-3.5 h-3.5 ${isFixing ? "animate-spin" : ""}`} />
                      <span>{isFixing ? "Applying..." : "Auto-Fix"}</span>
                    </button>
                  )}
                </div>

                <div className="mt-2.5 pt-2 border-t border-border-subtle flex items-center justify-between text-[11px] text-text-tertiary">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(anom.detected_at).toLocaleString()}
                  </span>
                  <span className="font-mono uppercase text-[10px] text-text-tertiary">
                    ID: {anom.campaign_id} • TYPE: {anom.anomaly_type}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
