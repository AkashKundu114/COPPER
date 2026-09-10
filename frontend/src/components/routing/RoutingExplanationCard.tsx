import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Clock,
  Compass,
  Layers,
  ShieldAlert,
  Sparkles,
  BarChart3,
  Search,
  FilterX,
  Cpu,
  Info,
} from "lucide-react";

export interface RoutingScoreItem {
  agent: string;
  agent_name: string;
  codename: string;
  score: number;
  percentage: number;
  is_winner: boolean;
}

export interface KeywordMatchTerm {
  term: string;
  start: number;
  end: number;
  agent: string;
}

export interface SuppressedRuleItem {
  agent: string;
  agent_name: string;
  codename: string;
  pattern: string;
  matched_text: string;
  penalty: number;
  reason: string;
}

export interface StageProgressionItem {
  stage_id: string;
  stage_number: number;
  name: string;
  status: "matched" | "passed" | "bypassed" | "evaluated" | string;
  decision: string;
}

export interface ConfidenceCalibrationData {
  raw_confidence: number;
  calibrated_confidence: number;
  calibrated_pct: number;
  certainty_tier: string;
  certainty_description: string;
  routing_entropy: number;
  runner_up_margin: number;
  is_consequential: boolean;
  cascade_risk: number;
}

export interface RoutingExplanationData {
  id?: string;
  timestamp?: number;
  prompt?: string;
  agent: string;
  agent_codename?: string;
  agent_display?: string;
  decision_summary: string;
  confidence: number;
  confidence_pct?: number;
  latency_ms: number;
  route_stage: string;
  scores?: Record<string, number>;
  score_breakdown?: RoutingScoreItem[];
  matched_keywords?: string[];
  matched_terms?: KeywordMatchTerm[];
  suppressed_rules?: SuppressedRuleItem[];
  stage_progression?: StageProgressionItem[];
  is_consequential?: boolean;
  cascade_risk?: number;
  sub_tasks?: string[];
  confidence_calibration?: ConfidenceCalibrationData;
}

interface Props {
  data: RoutingExplanationData;
  initialExpanded?: boolean;
}

const AGENT_COLORS: Record<string, { bg: string; text: string; border: string; bar: string }> = {
  coding: { bg: "bg-blue-950/60", text: "text-blue-400", border: "border-blue-500/40", bar: "bg-gradient-to-r from-blue-600 to-cyan-400" },
  automation: { bg: "bg-amber-950/60", text: "text-amber-400", border: "border-amber-500/40", bar: "bg-gradient-to-r from-amber-600 to-yellow-400" },
  research: { bg: "bg-purple-950/60", text: "text-purple-400", border: "border-purple-500/40", bar: "bg-gradient-to-r from-purple-600 to-indigo-400" },
  document: { bg: "bg-emerald-950/60", text: "text-emerald-400", border: "border-emerald-500/40", bar: "bg-gradient-to-r from-emerald-600 to-teal-400" },
  reminder: { bg: "bg-rose-950/60", text: "text-rose-400", border: "border-rose-500/40", bar: "bg-gradient-to-r from-rose-600 to-pink-400" },
  vision: { bg: "bg-cyan-950/60", text: "text-cyan-400", border: "border-cyan-500/40", bar: "bg-gradient-to-r from-cyan-600 to-blue-400" },
  image: { bg: "bg-fuchsia-950/60", text: "text-fuchsia-400", border: "border-fuchsia-500/40", bar: "bg-gradient-to-r from-fuchsia-600 to-pink-400" },
  planner: { bg: "bg-indigo-950/60", text: "text-indigo-400", border: "border-indigo-500/40", bar: "bg-gradient-to-r from-indigo-600 to-purple-400" },
  chat: { bg: "bg-slate-800/80", text: "text-accent-400", border: "border-slate-700", bar: "bg-gradient-to-r from-slate-600 to-slate-400" },
};

export const RoutingExplanationCard: React.FC<Props> = ({ data, initialExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(initialExpanded);
  const [activeTab, setActiveTab] = useState<"scores" | "keywords" | "stages" | "calibration">("scores");

  const agentKey = (data.agent || "chat").toLowerCase();
  const colorScheme = AGENT_COLORS[agentKey] || AGENT_COLORS.chat;
  const codename = data.agent_codename || agentKey.toUpperCase();
  const confPct = data.confidence_pct ?? Math.round(data.confidence * 100);

  // Render prompt with highlighted keyword spans
  const renderHighlightedPrompt = (promptText: string, terms: KeywordMatchTerm[]) => {
    if (!terms || terms.length === 0) {
      return <span className="text-slate-300">{promptText}</span>;
    }

    // Sort terms by start offset
    const sorted = [...terms].sort((a, b) => a.start - b.start);
    const segments: React.ReactNode[] = [];
    let lastIdx = 0;

    sorted.forEach((term, idx) => {
      if (term.start > lastIdx) {
        segments.push(
          <span key={`text-${lastIdx}`} className="text-slate-300">
            {promptText.slice(lastIdx, term.start)}
          </span>
        );
      }
      if (term.start >= lastIdx && term.end <= promptText.length) {
        segments.push(
          <mark
            key={`highlight-${idx}`}
            className="bg-purple-500/30 text-purple-200 border-b-2 border-purple-400 px-1 py-0.5 rounded font-bold shadow-sm inline-block mx-0.5"
            title={`Matched keyword trigger: '${term.term}' for ${term.agent}`}
          >
            {promptText.slice(term.start, term.end)}
          </mark>
        );
        lastIdx = term.end;
      }
    });

    if (lastIdx < promptText.length) {
      segments.push(
        <span key={`text-end`} className="text-slate-300">
          {promptText.slice(lastIdx)}
        </span>
      );
    }

    return <>{segments}</>;
  };

  return (
    <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden hover:border-slate-700/80 transition-all font-sans text-xs">
      {/* Header Bar */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-4 cursor-pointer select-none flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-slate-950/80 hover:bg-slate-850 transition-colors"
      >
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-xl border ${colorScheme.bg} ${colorScheme.border} mt-0.5`}>
            <Compass size={16} className={colorScheme.text} />
          </div>
          <div>
            <div className="flex items-center flex-wrap gap-2">
              <span className={`px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider text-[10px] border ${colorScheme.bg} ${colorScheme.text} ${colorScheme.border}`}>
                {codename}
              </span>
              <span className="font-semibold text-white text-xs">
                {data.agent_display || codename}
              </span>
              <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300">
                <Sparkles size={11} className="text-amber-400" />
                {confPct}% conf
              </span>
              <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-400">
                <Clock size={10} />
                {data.latency_ms.toFixed(2)}ms
              </span>
              {data.is_consequential && (
                <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md bg-rose-950/80 border border-rose-600/40 text-rose-300">
                  <ShieldAlert size={11} />
                  Guardian Gate
                </span>
              )}
            </div>

            {/* Decision Summary Text */}
            <p className="text-slate-300 text-xs mt-1.5 font-medium leading-relaxed">
              {data.decision_summary}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
            {data.route_stage.replace(/_/g, " ")}
          </span>
          <div className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors">
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </div>
        </div>
      </div>

      {/* Expandable PRISM Drawer */}
      {isExpanded && (
        <div className="border-t border-slate-800/80 bg-slate-950/80 p-4 space-y-4">
          {/* Drawer Sub-tabs */}
          <div className="flex flex-wrap gap-1.5 border-b border-slate-800/80 pb-2.5">
            <button
              onClick={() => setActiveTab("scores")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "scores"
                  ? "bg-purple-950/70 text-purple-300 border border-purple-700/50 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <BarChart3 size={13} />
              <span>Score Breakdown</span>
            </button>
            <button
              onClick={() => setActiveTab("keywords")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "keywords"
                  ? "bg-purple-950/70 text-purple-300 border border-purple-700/50 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Search size={13} />
              <span>Keyword Highlights</span>
              {data.matched_terms && data.matched_terms.length > 0 && (
                <span className="px-1.5 py-0.2 bg-purple-500/20 rounded-full text-[10px] font-bold text-purple-300">
                  {data.matched_terms.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("stages")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "stages"
                  ? "bg-purple-950/70 text-purple-300 border border-purple-700/50 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Layers size={13} />
              <span>5-Stage Pipeline</span>
            </button>
            <button
              onClick={() => setActiveTab("calibration")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "calibration"
                  ? "bg-purple-950/70 text-purple-300 border border-purple-700/50 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Cpu size={13} />
              <span>Calibration & Entropy</span>
            </button>
          </div>

          {/* TAB 1: Horizontal Score Breakdown Bar Chart */}
          {activeTab === "scores" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Domain Affinity Distribution</span>
                <span className="font-mono text-[10px]">Deterministic Weighted Pattern Scorer</span>
              </div>

              <div className="space-y-2">
                {data.score_breakdown && data.score_breakdown.length > 0 ? (
                  data.score_breakdown.map((item) => {
                    const agentColors = AGENT_COLORS[item.agent] || AGENT_COLORS.chat;
                    return (
                      <div key={item.agent} className="space-y-1">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <div className="flex items-center gap-2">
                            <span className={`font-bold ${item.is_winner ? agentColors.text : "text-slate-400"}`}>
                              {item.codename}
                            </span>
                            <span className="text-slate-400 text-[11px] font-sans">
                              {item.agent_name}
                            </span>
                            {item.is_winner && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-950 border border-purple-700/50 text-purple-300 font-bold">
                                WINNER
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-400 font-mono text-[11px]">
                              {item.score.toFixed(1)} pts
                            </span>
                            <span className="text-white font-mono font-semibold w-12 text-right">
                              {item.percentage.toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        {/* Animated Bar */}
                        <div className="h-2 w-full rounded-full bg-slate-900 overflow-hidden border border-slate-800">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              item.is_winner ? agentColors.bar : "bg-slate-700/50"
                            }`}
                            style={{ width: `${Math.max(2, item.percentage)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-slate-500 text-center py-4">No score breakdown available.</div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Keyword Highlights & Suppressed Rules */}
          {activeTab === "keywords" && (
            <div className="space-y-4">
              {/* Highlighted Prompt */}
              {data.prompt && (
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
                  <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Info size={11} className="text-purple-400" />
                    <span>Matched In Query</span>
                  </div>
                  <div className="text-xs font-mono leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                    {renderHighlightedPrompt(data.prompt, data.matched_terms || [])}
                  </div>
                </div>
              )}

              {/* Matched Keywords Badges */}
              <div className="space-y-2">
                <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                  Triggered Pattern Rules ({data.matched_keywords?.length || 0})
                </div>
                {data.matched_keywords && data.matched_keywords.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {data.matched_keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 rounded-md bg-purple-950/50 border border-purple-700/40 text-purple-300 font-mono text-[11px]"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-[11px]">No specific domain regex patterns fired (resolved via stage shortcut or fallback).</p>
                )}
              </div>

              {/* Suppressed Rules / Negative Patterns */}
              {data.suppressed_rules && data.suppressed_rules.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-xs">
                    <FilterX size={14} />
                    <span>Negative Pattern Suppressions ({data.suppressed_rules.length})</span>
                  </div>
                  <p className="text-[11px] text-slate-300">
                    Alternative agent candidates were penalized to prevent misclassification:
                  </p>
                  <div className="space-y-1.5">
                    {data.suppressed_rules.map((rule, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded-lg bg-slate-950/70 border border-amber-900/30 flex items-center justify-between text-xs font-mono"
                      >
                        <div>
                          <span className="text-amber-300 font-semibold">{rule.agent_name || rule.agent}</span>
                          <span className="text-slate-400 ml-2 text-[11px]">
                            matched '{rule.matched_text}'
                          </span>
                        </div>
                        <span className="text-rose-400 font-bold">-{rule.penalty} pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: 5-Stage Pipeline Progression */}
          {activeTab === "stages" && (
            <div className="space-y-3">
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Multi-Stage Decision Lifecycle
              </div>
              <div className="space-y-2">
                {data.stage_progression?.map((st) => {
                  const isMatched = st.status === "matched";
                  const isBypassed = st.status === "bypassed";
                  const isEvaluated = st.status === "evaluated";

                  return (
                    <div
                      key={st.stage_id}
                      className={`p-3 rounded-xl border flex items-start gap-3 transition-all ${
                        isMatched
                          ? "bg-purple-950/40 border-purple-600/50 shadow-md shadow-purple-950/30"
                          : isBypassed
                          ? "bg-slate-950/40 border-slate-900 opacity-60"
                          : isEvaluated
                          ? "bg-slate-900/80 border-slate-800"
                          : "bg-slate-900/60 border-slate-800"
                      }`}
                    >
                      <div
                        className={`p-1.5 rounded-lg text-[10px] font-mono font-bold mt-0.5 ${
                          isMatched
                            ? "bg-purple-500 text-white"
                            : isBypassed
                            ? "bg-slate-800 text-slate-500"
                            : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        S{st.stage_number}
                      </div>
                      <div className="flex-1 space-y-0.5">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white text-xs">
                            {st.name}
                          </span>
                          <span
                            className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full font-bold ${
                              isMatched
                                ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                                : isBypassed
                                ? "bg-slate-800 text-slate-500"
                                : "bg-emerald-950/50 text-emerald-400 border border-emerald-800/40"
                            }`}
                          >
                            {st.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-normal">
                          {st.decision}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: Confidence Calibration & Information Metrics */}
          {activeTab === "calibration" && data.confidence_calibration && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Certainty Tier</div>
                  <div className="text-xs font-bold text-purple-300">
                    {data.confidence_calibration.certainty_tier}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {data.confidence_calibration.certainty_description}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Routing Entropy</div>
                  <div className="text-xs font-bold text-cyan-300 font-mono">
                    {data.confidence_calibration.routing_entropy.toFixed(3)} bits
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Shannon entropy H(R) ambiguity
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Runner-Up Margin</div>
                  <div className="text-xs font-bold text-emerald-300 font-mono">
                    +{data.confidence_calibration.runner_up_margin.toFixed(2)} pts
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Distance to 2nd candidate
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Cascade Risk</div>
                  <div className="text-xs font-bold text-amber-300 font-mono">
                    {(data.confidence_calibration.cascade_risk * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500">
                    TFP-Router DAG failure risk
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Raw Confidence vs Calibrated:</span>
                <span className="font-mono text-white">
                  {Math.round(data.confidence_calibration.raw_confidence * 100)}% raw ➔{" "}
                  <span className="text-purple-300 font-bold">{data.confidence_calibration.calibrated_pct}% calibrated</span>
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
