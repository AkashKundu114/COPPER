import React, { useState, useEffect } from "react";
import { provenanceAPI } from "../../services/api";
import { Search, ShieldAlert, CheckCircle2, XCircle, HelpCircle, History, Tag } from "lucide-react";

export const MemoryProvenanceTab: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [facts, setFacts] = useState<any[]>([]);
  const [uncertainFacts, setUncertainFacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [explaining, setExplaining] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<any>(null);

  const fetchFacts = async (q = "") => {
    setLoading(true);
    try {
      const res = await provenanceAPI.searchFacts(q);
      setFacts(res.data || []);
      const unc = await provenanceAPI.getUncertain();
      setUncertainFacts(unc.data || []);
    } catch (err) {
      console.error("Failed to fetch facts", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFacts();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFacts(searchQuery);
  };

  const handleConfirm = async (id: string) => {
    try {
      await provenanceAPI.confirmFact(id, "user_manual_confirm");
      fetchFacts(searchQuery);
    } catch (err) {
      console.error("Failed to confirm fact", err);
    }
  };

  const handleContradict = async (id: string) => {
    try {
      await provenanceAPI.contradictFact(id, "user_manual_contradict", "User indicated this is incorrect.");
      fetchFacts(searchQuery);
    } catch (err) {
      console.error("Failed to contradict fact", err);
    }
  };

  const handleExplain = async (factId: string, factContent: string) => {
    setExplaining(factId);
    setExplanation(null);
    try {
      const res = await provenanceAPI.explainBelief(factContent);
      setExplanation(res.data);
    } catch (err) {
      console.error("Failed to explain belief", err);
    } finally {
      setExplaining(null);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto w-full custom-scrollbar text-text">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight font-sans">
            Memory Provenance
          </h1>
          <p className="text-xs text-text-secondary">
            Audit trail, sources, and belief confidence for system knowledge.
          </p>
        </div>
        {uncertainFacts.length > 0 && (
          <div className="flex items-center gap-2 bg-amber-950/40 text-amber-500 px-3 py-1.5 rounded-xl border border-amber-500/20 text-xs font-medium">
            <ShieldAlert size={14} />
            <span>{uncertainFacts.length} Uncertain Facts</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSearch} className="relative w-full">
        <Search size={14} className="absolute left-3 top-3 text-text-tertiary" />
        <input
          type="text"
          placeholder="Search facts audit trail..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2 rounded-xl bg-surface-elevated border border-border-subtle text-white outline-none focus:border-accent-500 text-sm"
        />
      </form>

      {/* Facts List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-8 text-center text-text-tertiary bg-surface-elevated/60 rounded-2xl border border-border-subtle">
            Loading provenance records...
          </div>
        ) : facts.length === 0 ? (
          <div className="p-8 text-center text-text-tertiary bg-surface-elevated/60 rounded-2xl border border-border-subtle">
            No records found.
          </div>
        ) : (
          facts.map((fact) => (
            <div key={fact.id} className="p-4 bg-surface-elevated rounded-2xl border border-border-subtle space-y-3">
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm font-medium text-white flex-1 leading-relaxed">
                  {fact.fact}
                </p>
                <div className="flex flex-col items-end gap-1 shrink-0 text-xs">
                  <span className="text-text-secondary">Score: <strong className="text-white">{Math.round(fact.confidence * 100)}%</strong></span>
                  {fact.initial_confidence && (
                    <span className="text-text-tertiary text-[10px]">Initial: {Math.round(fact.initial_confidence * 100)}%</span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-text-secondary flex-wrap">
                <span className="flex items-center gap-1.5 bg-canvas px-2 py-1 rounded-md border border-border-subtle">
                  <Tag size={12} />
                  {fact.source_type}
                </span>
                <span className="truncate max-w-[200px]" title={fact.source_id}>
                  ID: {fact.source_id}
                </span>
                {fact.revisions && fact.revisions.length > 0 && (
                  <span className="flex items-center gap-1 text-cyber-cyan">
                    <History size={12} />
                    {fact.revisions.length} Revisions
                  </span>
                )}
              </div>

              <div className="flex gap-2 pt-3 border-t border-border-subtle">
                <button
                  onClick={() => handleConfirm(fact.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-xs font-medium transition-colors border border-emerald-500/20"
                >
                  <CheckCircle2 size={14} />
                  Confirm Fact
                </button>
                <button
                  onClick={() => handleContradict(fact.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-xs font-medium transition-colors border border-red-500/20"
                >
                  <XCircle size={14} />
                  Contradict
                </button>
                <button
                  onClick={() => handleExplain(fact.id, fact.fact)}
                  disabled={explaining === fact.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-active hover:bg-surface-spotlight text-text-secondary rounded-lg text-xs font-medium transition-colors ml-auto border border-border-highlight"
                >
                  <HelpCircle size={14} />
                  {explaining === fact.id ? "Analyzing..." : "Explain Belief"}
                </button>
              </div>

              {/* Explanation Dropdown */}
              {explanation && explaining !== fact.id && explanation.fact === fact.fact && (
                <div className="mt-3 p-3 bg-canvas rounded-xl border border-border-subtle text-sm text-text-secondary leading-relaxed">
                  <strong className="text-white block mb-1">Belief Explanation:</strong>
                  {explanation.explanation}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
