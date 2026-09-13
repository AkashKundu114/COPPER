import React, { useState, useEffect } from "react";
import {
  Wrench,
  Search,
  ChevronDown,
  ChevronUp,
  Play,
  FileCode,
} from "lucide-react";
import { catalogAPI, type CatalogTool } from "../../services/api";

export const ActiveToolsTab: React.FC = () => {
  const [tools, setTools] = useState<CatalogTool[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedGuardianLevel, setSelectedGuardianLevel] = useState<number | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  // Diagram Studio Live State
  const [diagramType, setDiagramType] = useState<string>("flowchart");
  const [diagramTitle, setDiagramTitle] = useState<string>("Autonomous Agent Mesh");
  const [diagramSpec, setDiagramSpec] = useState<string>("User -> Router -> Core Fleet -> Output");
  const [diagramResult, setDiagramResult] = useState<string | null>(null);
  const [diagramRendering, setDiagramRendering] = useState(false);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    setLoading(true);
    try {
      const res = await catalogAPI.getTools();
      if (res.data?.tools) {
        setTools(res.data.tools);
        const cats = Array.from(new Set(res.data.tools.map((t) => t.category))).filter(Boolean);
        setCategories(cats);
      }
    } catch (err) {
      console.error("Failed to load tools catalog:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRenderDiagram = async () => {
    setDiagramRendering(true);
    try {
      const res = await catalogAPI.renderDiagram(diagramType, diagramTitle, diagramSpec);
      if (res.data?.diagram) {
        setDiagramResult(res.data.diagram);
      } else if (typeof res.data === "string") {
        setDiagramResult(res.data);
      } else {
        setDiagramResult(JSON.stringify(res.data, null, 2));
      }
    } catch (err: any) {
      setDiagramResult(`Error rendering diagram: ${err.message}`);
    } finally {
      setDiagramRendering(false);
    }
  };

  const filteredTools = tools.filter((t) => {
    const matchesCat = selectedCategory === "all" || t.category === selectedCategory;
    const matchesGuardian =
      selectedGuardianLevel === "all" || t.guardian_level === selectedGuardianLevel;
    const matchesSearch =
      searchQuery.trim() === "" ||
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesGuardian && matchesSearch;
  });

  const getGuardianBadge = (level: number) => {
    switch (level) {
      case 0:
        return {
          label: "Level 0: Autonomous",
          badge: "bg-emerald-950/60 text-emerald-400 border-emerald-800/40",
          dot: "bg-emerald-400",
        };
      case 1:
        return {
          label: "Level 1: Suggestion",
          badge: "bg-cyan-950/60 text-cyan-400 border-cyan-800/40",
          dot: "bg-cyan-400",
        };
      case 2:
        return {
          label: "Level 2: Guardian Gate",
          badge: "bg-amber-950/60 text-amber-400 border-amber-800/40",
          dot: "bg-amber-400",
        };
      default:
        return {
          label: "Level 3: Dual-Key Safety",
          badge: "bg-rose-950/60 text-rose-400 border-rose-800/40",
          dot: "bg-rose-400",
        };
    }
  };

  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Header & Filter Controls */}
      <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Wrench size={18} className="text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">
                Active Tool Armor & Execution Schemas
              </h2>
              <p className="text-[11px] text-slate-400">
                {tools.length} Registered System, Codebase, Stealth Scraping & Visual Tools
              </p>
            </div>
          </div>

          {/* Search Box */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl focus-within:border-cyan-500/50 transition-all w-full md:w-80">
            <Search size={14} className="text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tool name, schema, or purpose..."
              className="bg-transparent text-white placeholder:text-slate-500 outline-none text-xs w-full font-sans"
            />
          </div>
        </div>

        {/* Guardian Level & Category Selectors */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            <button
              onClick={() => setSelectedCategory("all")}
              className={`px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === "all"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20"
                  : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              All Categories
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  selectedCategory === cat
                    ? "bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20"
                    : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Guardian Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[10px] font-mono text-slate-500 mr-1">Guardian:</span>
            {[
              { id: "all", label: "All" },
              { id: 0, label: "L0 Direct" },
              { id: 2, label: "L2 Gate" },
            ].map((g) => (
              <button
                key={String(g.id)}
                onClick={() => setSelectedGuardianLevel(g.id as any)}
                className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-semibold transition-all ${
                  selectedGuardianLevel === g.id
                    ? "bg-slate-700 text-white border border-slate-600"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {g.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Embedded Live Tool Studio (Diagram & Architecture Renderer) */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCode size={16} className="text-cyan-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Live Tool Studio: Workflow & Architecture Diagram Renderer
            </h3>
          </div>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded-full">
            diagram_tools.workflow_diagram_render
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">Diagram Type</label>
            <select
              value={diagramType}
              onChange={(e) => setDiagramType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500/50"
            >
              <option value="flowchart">Flowchart</option>
              <option value="sequence">Sequence Diagram</option>
              <option value="er">Entity-Relationship (ER)</option>
              <option value="architecture">System Architecture</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">Diagram Title</label>
            <input
              type="text"
              value={diagramTitle}
              onChange={(e) => setDiagramTitle(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500/50"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-slate-400 block mb-1">Workflow Specification</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={diagramSpec}
                onChange={(e) => setDiagramSpec(e.target.value)}
                placeholder="Nodes and edges specification..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500/50"
              />
              <button
                onClick={handleRenderDiagram}
                disabled={diagramRendering}
                className="px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1 shrink-0 disabled:opacity-50"
              >
                <Play size={11} fill="white" />
                <span>{diagramRendering ? "..." : "Render"}</span>
              </button>
            </div>
          </div>
        </div>

        {diagramResult && (
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1 font-mono text-xs">
            <div className="flex items-center justify-between text-[10px] text-slate-500">
              <span>RENDER OUTPUT ({diagramType.toUpperCase()}):</span>
              <button
                onClick={() => setDiagramResult(null)}
                className="hover:text-white"
              >
                Clear
              </button>
            </div>
            <pre className="text-cyan-300 text-[11px] whitespace-pre-wrap overflow-x-auto select-text">
              {diagramResult}
            </pre>
          </div>
        )}
      </div>

      {/* Grid of Tool Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-32 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse p-4"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredTools.map((t) => {
            const isExpanded = expandedTool === t.name;
            const g = getGuardianBadge(t.guardian_level);

            return (
              <div
                key={t.name}
                className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white">
                          {t.name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 bg-slate-950 px-2 py-0.5 rounded-full border border-slate-800">
                          {t.category}
                        </span>
                      </div>
                    </div>

                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1.5 ${g.badge}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${g.dot}`} />
                      <span>{g.label.split(":")[0]}</span>
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {t.description}
                  </p>

                  <div className="text-[11px] font-mono text-slate-500">
                    Returns: <span className="text-slate-400">{t.return_description}</span>
                  </div>
                </div>

                {/* Parameters Accordion */}
                <div className="pt-2 border-t border-slate-800/80">
                  <button
                    onClick={() => setExpandedTool(isExpanded ? null : t.name)}
                    className="flex items-center justify-between w-full text-[11px] font-mono text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    <span>
                      Schema Parameters ({t.parameter_count || t.parameters?.length || 0})
                    </span>
                    {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>

                  {isExpanded && (
                    <div className="mt-2.5 space-y-2 bg-slate-950 p-3 rounded-xl border border-slate-800/80 font-mono text-[11px]">
                      {t.parameters && t.parameters.length > 0 ? (
                        t.parameters.map((p) => (
                          <div key={p.name} className="border-b border-slate-900 pb-1.5 last:border-0 last:pb-0">
                            <div className="flex items-center gap-2">
                              <span className="text-white font-bold">{p.name}</span>
                              <span className="text-[10px] text-cyan-400 bg-cyan-950/60 px-1.5 py-0.2 rounded border border-cyan-900">
                                {p.type}
                              </span>
                              {p.required && (
                                <span className="text-[9px] text-amber-400 font-semibold uppercase">
                                  required
                                </span>
                              )}
                            </div>
                            {p.description && (
                              <p className="text-slate-400 text-[10px] mt-0.5 font-sans">
                                {p.description}
                              </p>
                            )}
                          </div>
                        ))
                      ) : (
                        <span className="text-slate-500">No parameters required.</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
