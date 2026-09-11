import React, { useState, useEffect } from "react";
import { causalAPI } from "../../services/api";
import { Search, Link as LinkIcon, Activity, Info, BarChart2 } from "lucide-react";

export const CausalExplorerTab: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [whyResult, setWhyResult] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [inferring, setInferring] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [eventsRes, statsRes] = await Promise.all([
        causalAPI.getEvents(24, "", 20),
        causalAPI.getStats()
      ]);
      setEvents(eventsRes.data || []);
      setStats(statsRes.data || null);
    } catch (err) {
      console.error("Failed to load causal data", err);
    }
  };

  const handleWhy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await causalAPI.queryWhy(question);
      setWhyResult(res.data);
    } catch (err) {
      console.error("Why query failed", err);
    } finally {
      setLoading(false);
    }
  };

  const handleInfer = async () => {
    setInferring(true);
    try {
      await causalAPI.inferLinks();
      await fetchData();
    } catch (err) {
      console.error("Failed to infer links", err);
    } finally {
      setInferring(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto w-full custom-scrollbar text-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight font-sans">
            Causal Explorer
          </h1>
          <p className="text-xs text-slate-400">
            Query and analyze causality between events and actions.
          </p>
        </div>
        <div className="flex gap-2">
          {stats && (
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
              <BarChart2 size={14} />
              <span>Events: {stats.total_events}</span>
              <span>Links: {stats.total_links}</span>
            </div>
          )}
          <button
            onClick={handleInfer}
            disabled={inferring}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-accent-500/10 text-accent-400 border border-accent-500/40 hover:bg-accent-500/20 text-xs font-bold transition-all disabled:opacity-50"
          >
            <LinkIcon size={14} />
            <span>{inferring ? "Inferring..." : "Infer Links"}</span>
          </button>
        </div>
      </div>

      {/* Why Query Box */}
      <form onSubmit={handleWhy} className="flex gap-3 items-center w-full">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Ask 'Why?' (e.g. Why did the build fail?)"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white outline-none focus:border-accent-500 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2 rounded-xl bg-cyber-cyan text-black font-bold shadow-[0_0_15px_rgba(0,240,255,0.4)] text-sm disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {/* Causal Chain Visualization */}
      {whyResult && (
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity size={16} className="text-cyber-cyan" />
            Causal Explanation
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800/50">
            {whyResult.explanation}
          </p>
          
          {whyResult.chain && whyResult.chain.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-xs font-semibold text-slate-400">Event Chain:</h4>
              <div className="flex flex-col gap-2">
                {whyResult.chain.map((item: any, idx: number) => (
                  <div key={idx} className="flex flex-col gap-1">
                    <div className="flex items-center gap-3 p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">
                      <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold shrink-0">
                        {idx + 1}
                      </div>
                      <span className="text-sm text-white flex-1">{item.event}</span>
                      {item.confidence && (
                        <span className="text-xs px-2 py-1 bg-cyber-cyan/10 text-cyber-cyan rounded-md border border-cyber-cyan/20">
                          {Math.round(item.confidence * 100)}% Match
                        </span>
                      )}
                    </div>
                    {idx < whyResult.chain.length - 1 && (
                      <div className="w-full flex justify-center py-1">
                        <div className="w-0.5 h-4 bg-slate-700"></div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Events Stream */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Info size={16} className="text-slate-400" />
          Recent Causal Events
        </h3>
        {events.length === 0 ? (
          <div className="p-8 text-center text-slate-500 bg-slate-900/60 rounded-2xl border border-slate-800">
            No recent events recorded.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {events.map((ev, idx) => (
              <div key={idx} className="p-4 bg-slate-900/50 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col gap-2 text-sm">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-medium px-2 py-0.5 bg-slate-800 text-slate-300 rounded uppercase tracking-wider">
                    {ev.category || 'General'}
                  </span>
                  <span className="text-[10px] text-slate-500">{new Date(ev.timestamp || Date.now()).toLocaleString()}</span>
                </div>
                <p className="text-white text-sm mt-1">{ev.description}</p>
                {ev.source && (
                  <span className="text-xs text-slate-400">Source: {ev.source}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
