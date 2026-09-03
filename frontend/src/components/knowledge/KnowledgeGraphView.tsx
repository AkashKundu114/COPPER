import React, { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import {
  Search,
  RefreshCw,
  Zap,
  Trash2,
  Maximize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  Layers,
  Network,
  X,
  Plus,
} from "lucide-react";
import {
  knowledgeAPI,
  type KnowledgeEntityItem,
  type KnowledgeRelationshipItem,
  type KnowledgeStatsResponse,
} from "../../lib/api";

const ENTITY_TYPE_COLORS: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  PERSON: { bg: "#0284c7", border: "#38bdf8", text: "#e0f2fe", glow: "rgba(56, 189, 248, 0.6)" },
  PROJECT: { bg: "#0891b2", border: "#00f0ff", text: "#ecfeff", glow: "rgba(0, 240, 255, 0.7)" },
  TECHNOLOGY: { bg: "#9333ea", border: "#c084fc", text: "#f3e8ff", glow: "rgba(192, 132, 252, 0.6)" },
  ORGANIZATION: { bg: "#d97706", border: "#fbbf24", text: "#fef3c7", glow: "rgba(251, 191, 36, 0.6)" },
  CONCEPT: { bg: "#059669", border: "#34d399", text: "#ecfdf5", glow: "rgba(52, 211, 153, 0.6)" },
  DATE_EVENT: { bg: "#db2777", border: "#f472b6", text: "#fdf2f8", glow: "rgba(244, 114, 182, 0.6)" },
  LOCATION: { bg: "#e11d48", border: "#fb7185", text: "#fff1f2", glow: "rgba(251, 113, 133, 0.6)" },
  FILE: { bg: "#475569", border: "#94a3b8", text: "#f8fafc", glow: "rgba(148, 163, 184, 0.5)" },
};

const DEFAULT_COLOR = {
  bg: "#1e293b",
  border: "#64748b",
  text: "#f1f5f9",
  glow: "rgba(100, 116, 139, 0.5)",
};

interface D3Node extends d3.SimulationNodeDatum, KnowledgeEntityItem {
  r?: number;
}

type D3Link = Omit<KnowledgeRelationshipItem, "source" | "target"> & d3.SimulationLinkDatum<D3Node>;

export const KnowledgeGraphView: React.FC = () => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [entities, setEntities] = useState<KnowledgeEntityItem[]>([]);
  const [relationships, setRelationships] = useState<KnowledgeRelationshipItem[]>([]);
  const [stats, setStats] = useState<KnowledgeStatsResponse["stats"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedEntity, setSelectedEntity] = useState<KnowledgeEntityItem | null>(null);
  const [focusedEntityName, setFocusedEntityName] = useState<string | null>(null);

  // Extract Modal
  const [isExtractModalOpen, setIsExtractModalOpen] = useState(false);
  const [extractInput, setExtractInput] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);

  // Add Entity Modal
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newEntityName, setNewEntityName] = useState("");
  const [newEntityType, setNewEntityType] = useState("PROJECT");
  const [newEntityContext, setNewEntityContext] = useState("");
  const [newEntityConfidence, setNewEntityConfidence] = useState(0.9);

  // Zoom behavior reference
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const fetchGraphData = async (focusEntity?: string) => {
    setLoading(true);
    try {
      if (focusEntity) {
        const sub = await knowledgeAPI.getSubgraph({ entity: focusEntity, depth: 2, max_nodes: 50 });
        setEntities(sub.nodes);
        setRelationships(sub.links || sub.edges || []);
      } else {
        const sub = await knowledgeAPI.getSubgraph({ depth: 2, max_nodes: 60 });
        setEntities(sub.nodes);
        setRelationships(sub.links || sub.edges || []);
      }
      const st = await knowledgeAPI.getStats();
      setStats(st.stats);
    } catch (err) {
      console.error("[ATLAS Graph] Fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData(focusedEntityName || undefined);
  }, [focusedEntityName]);

  // Filtered nodes based on type & search
  const filteredData = useMemo(() => {
    const matchedNodeNames = new Set<string>();

    const nodes = entities.filter((e) => {
      const typeMatch = selectedType === "ALL" || e.type.toUpperCase() === selectedType;
      const searchMatch =
        !searchQuery ||
        e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.context && e.context.toLowerCase().includes(searchQuery.toLowerCase()));
      const ok = typeMatch && searchMatch;
      if (ok) matchedNodeNames.add(e.canonical_name);
      return ok;
    });

    const links = relationships.filter((r) => {
      const srcCanon = (r.source || "").toLowerCase();
      const tgtCanon = (r.target || "").toLowerCase();
      return matchedNodeNames.has(srcCanon) && matchedNodeNames.has(tgtCanon);
    });

    return { nodes, links };
  }, [entities, relationships, selectedType, searchQuery]);

  // D3 Force Simulation
  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = containerRef.current.clientWidth || 900;
    const height = containerRef.current.clientHeight || 650;

    // Define defs & markers for arrows
    const defs = svg.append("defs");
    defs
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 26)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#00f0ff")
      .attr("opacity", 0.7);

    // Glow filter
    const filter = defs.append("filter").attr("id", "glow");
    filter.append("feGaussianBlur").attr("stdDeviation", "3").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const g = svg.append("g").attr("class", "graph-root");

    // Setup zoom
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    svg.call(zoom);
    zoomRef.current = zoom;

    // Clone data for D3 mutation
    const nodes: D3Node[] = filteredData.nodes.map((d) => ({
      ...d,
      r: Math.max(14, Math.min(26, 14 + (d.evidence_count || 1) * 2 + (d.confidence || 0.8) * 6)),
    }));

    const nodeMap = new Map(nodes.map((n) => [n.canonical_name, n]));

    const links: D3Link[] = [];
    for (const rel of filteredData.links) {
      const srcNode = nodeMap.get((rel.source || "").toLowerCase());
      const tgtNode = nodeMap.get((rel.target || "").toLowerCase());
      if (srcNode && tgtNode) {
        links.push({
          ...rel,
          source: srcNode,
          target: tgtNode,
        });
      }
    }

    // Force Simulation
    const simulation = d3
      .forceSimulation<D3Node>(nodes)
      .force(
        "link",
        d3
          .forceLink<D3Node, D3Link>(links)
          .id((d) => d.canonical_name)
          .distance(120),
      )
      .force("charge", d3.forceManyBody().strength(-240))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<D3Node>().radius((d) => (d.r || 16) + 16));

    // Render Links
    const linkGroup = g.append("g").attr("class", "links");
    const link = linkGroup
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#00f0ff")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", (d) => Math.max(1.2, (d.confidence || 0.8) * 2.2))
      .attr("marker-end", "url(#arrowhead)");

    // Link Labels
    const linkLabelGroup = g.append("g").attr("class", "link-labels");
    const linkLabels = linkLabelGroup
      .selectAll("text")
      .data(links)
      .enter()
      .append("text")
      .attr("font-family", "monospace")
      .attr("font-size", "9px")
      .attr("fill", "#67e8f9")
      .attr("opacity", 0.75)
      .attr("text-anchor", "middle")
      .attr("dy", -3)
      .text((d) => d.type);

    // Render Nodes
    const nodeGroup = g.append("g").attr("class", "nodes");
    const node = nodeGroup
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, D3Node>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      )
      .on("click", (_event, d) => {
        setSelectedEntity(d);
      });

    // Outer glow circle
    node
      .append("circle")
      .attr("r", (d) => (d.r || 16) + 4)
      .attr("fill", "none")
      .attr("stroke", (d) => {
        const c = ENTITY_TYPE_COLORS[d.type.toUpperCase()] || DEFAULT_COLOR;
        return c.border;
      })
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.6)
      .attr("filter", "url(#glow)");

    // Inner filled circle
    node
      .append("circle")
      .attr("r", (d) => d.r || 16)
      .attr("fill", (d) => {
        const c = ENTITY_TYPE_COLORS[d.type.toUpperCase()] || DEFAULT_COLOR;
        return c.bg;
      })
      .attr("stroke", (d) => {
        const c = ENTITY_TYPE_COLORS[d.type.toUpperCase()] || DEFAULT_COLOR;
        return c.border;
      })
      .attr("stroke-width", 2);

    // Node Type Icon / Text
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-family", "monospace")
      .attr("font-size", "10px")
      .attr("font-weight", "bold")
      .attr("fill", "#ffffff")
      .text((d) => d.name.slice(0, 3).toUpperCase());

    // Node Label underneath
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("y", (d) => (d.r || 16) + 14)
      .attr("font-family", "monospace")
      .attr("font-size", "11px")
      .attr("font-weight", "600")
      .attr("fill", "#e2e8f0")
      .text((d) => d.name);

    // Simulation Ticks
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as D3Node).x || 0)
        .attr("y1", (d) => (d.source as D3Node).y || 0)
        .attr("x2", (d) => (d.target as D3Node).x || 0)
        .attr("y2", (d) => (d.target as D3Node).y || 0);

      linkLabels
        .attr("x", (d) => (((d.source as D3Node).x || 0) + ((d.target as D3Node).x || 0)) / 2)
        .attr("y", (d) => (((d.source as D3Node).y || 0) + ((d.target as D3Node).y || 0)) / 2);

      node.attr("transform", (d) => `translate(${d.x || 0},${d.y || 0})`);
    });

    return () => {
      simulation.stop();
    };
  }, [filteredData]);

  const handleZoom = (factor: number) => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(300).call(zoomRef.current.scaleBy, factor);
  };

  const handleResetZoom = () => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(400).call(zoomRef.current.transform, d3.zoomIdentity);
  };

  const handleExtractKnowledge = async () => {
    if (!extractInput.trim()) return;
    setIsExtracting(true);
    try {
      await knowledgeAPI.extractFromText(extractInput);
      setExtractInput("");
      setIsExtractModalOpen(false);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Extract] Failed:", err);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleAddEntity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEntityName.trim()) return;
    try {
      await knowledgeAPI.createEntity({
        name: newEntityName.trim(),
        type: newEntityType,
        confidence: newEntityConfidence,
        context: newEntityContext.trim(),
      });
      setNewEntityName("");
      setNewEntityContext("");
      setIsAddModalOpen(false);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Entity] Add failed:", err);
    }
  };

  const handleDeleteEntity = async (id: number) => {
    try {
      await knowledgeAPI.deleteEntity(id);
      setSelectedEntity(null);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Delete] Failed:", err);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-[#05080e]/95 text-slate-200 select-none font-mono">
      {/* Top HUD Banner */}
      <div className="px-6 py-4 border-b border-cyber-cyan/20 bg-black/40 backdrop-blur-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyber-cyan/15 border border-cyber-cyan/40 flex items-center justify-center text-cyber-cyan shadow-[0_0_15px_rgba(0,240,255,0.25)]">
            <Network size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white font-display tracking-tight">
                ATLAS Knowledge Graph
              </h1>
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-verdigris/15 text-verdigris border border-verdigris/30 animate-pulse">
                LIVE RETRIEVAL
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Entity & Relationship Network • Graph-Augmented RAG Engine
            </p>
          </div>
        </div>

        {/* Global Stats Counter */}
        {stats && (
          <div className="flex items-center gap-3 text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-black/60 border border-cyber-cyan/20">
              <span className="text-zinc-500 block text-[9px] uppercase">Entities</span>
              <span className="text-cyber-cyan font-bold">{stats.total_entities}</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-black/60 border border-cyber-cyan/20">
              <span className="text-zinc-500 block text-[9px] uppercase">Relationships</span>
              <span className="text-accent font-bold">{stats.total_relationships}</span>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExtractModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-cyan/15 hover:bg-cyber-cyan/25 text-cyber-cyan border border-cyber-cyan/40 text-xs font-bold transition-all shadow-sm"
          >
            <Sparkles size={14} />
            <span>Extract (ATLAS)</span>
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-500/20 hover:bg-accent-500/30 text-accent border border-accent-500/40 text-xs font-bold transition-all"
          >
            <Plus size={14} />
            <span>Add Entity</span>
          </button>
          <button
            onClick={() => fetchGraphData(focusedEntityName || undefined)}
            className="p-2 rounded-lg bg-black/50 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all"
            title="Refresh Graph"
          >
            <RefreshCw size={15} className={loading ? "animate-spin text-cyber-cyan" : ""} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="px-6 py-2.5 border-b border-zinc-800/80 bg-black/30 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-zinc-500 text-[11px] uppercase tracking-wider flex items-center gap-1">
            <Layers size={12} /> Filter:
          </span>
          {["ALL", "PERSON", "PROJECT", "TECHNOLOGY", "ORGANIZATION", "CONCEPT"].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                selectedType === t
                  ? "bg-cyber-cyan text-black font-bold shadow-[0_0_10px_rgba(0,240,255,0.4)]"
                  : "bg-black/60 border border-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {t}
            </button>
          ))}
          {focusedEntityName && (
            <button
              onClick={() => setFocusedEntityName(null)}
              className="px-2 py-0.5 rounded text-[10px] bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1 hover:bg-red-500/30"
            >
              <X size={11} /> Reset Focus ({focusedEntityName})
            </button>
          )}
        </div>

        <div className="relative w-64">
          <Search size={13} className="absolute left-2.5 top-2.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search entities or relations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
          />
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="relative flex-1 w-full overflow-hidden" ref={containerRef}>
        <svg ref={svgRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

        {/* Floating Zoom Controls */}
        <div className="absolute bottom-6 right-6 flex flex-col gap-1.5 bg-black/70 border border-zinc-800 p-1.5 rounded-xl backdrop-blur-md shadow-xl z-20">
          <button
            onClick={() => handleZoom(1.25)}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all"
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={() => handleZoom(0.8)}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all"
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all"
            title="Reset View"
          >
            <RotateCcw size={16} />
          </button>
        </div>

        {/* Entity Inspector Side Drawer */}
        {selectedEntity && (
          <div className="absolute top-4 right-4 w-84 max-h-[calc(100%-2rem)] bg-[#05080e]/95 border border-cyber-cyan/30 rounded-2xl shadow-[0_0_30px_rgba(0,0,0,0.8)] backdrop-blur-2xl p-4 overflow-y-auto custom-scrollbar z-30 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor:
                      (ENTITY_TYPE_COLORS[selectedEntity.type.toUpperCase()] || DEFAULT_COLOR).border,
                  }}
                />
                <h3 className="text-sm font-bold text-white font-display truncate max-w-[180px]">
                  {selectedEntity.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEntity(null)}
                className="text-zinc-500 hover:text-white transition-all"
              >
                <X size={15} />
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-zinc-500 uppercase text-[10px]">Type</span>
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold"
                  style={{
                    backgroundColor:
                      (ENTITY_TYPE_COLORS[selectedEntity.type.toUpperCase()] || DEFAULT_COLOR).bg,
                    color:
                      (ENTITY_TYPE_COLORS[selectedEntity.type.toUpperCase()] || DEFAULT_COLOR).text,
                  }}
                >
                  {selectedEntity.type}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-zinc-500 uppercase text-[10px]">Confidence</span>
                <span className="text-verdigris font-bold">
                  {Math.round((selectedEntity.confidence || 0.8) * 100)}%
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-zinc-500 uppercase text-[10px]">Evidence Count</span>
                <span className="text-zinc-300 font-bold">{selectedEntity.evidence_count || 1} observations</span>
              </div>

              {selectedEntity.context && (
                <div className="p-2.5 rounded-lg bg-black/60 border border-zinc-800/80 text-[11px] text-zinc-300">
                  <span className="text-zinc-500 block text-[9px] uppercase mb-1">Context Snippet</span>
                  {selectedEntity.context}
                </div>
              )}
            </div>

            {/* Entity Actions */}
            <div className="pt-2 border-t border-zinc-800 flex gap-2">
              <button
                onClick={() => setFocusedEntityName(selectedEntity.name)}
                className="flex-1 py-1.5 rounded-lg bg-cyber-cyan/15 hover:bg-cyber-cyan/25 text-cyber-cyan border border-cyber-cyan/30 text-xs font-bold transition-all flex items-center justify-center gap-1"
              >
                <Maximize2 size={13} /> Focus Subgraph
              </button>
              <button
                onClick={() => handleDeleteEntity(selectedEntity.id)}
                className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition-all"
                title="Delete Entity"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Extract Modal */}
      {isExtractModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-[#0a0f18] border border-cyber-cyan/30 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-cyber-cyan" />
                <h3 className="text-base font-bold text-white font-display">
                  ATLAS Entity & Relationship Extractor
                </h3>
              </div>
              <button onClick={() => setIsExtractModalOpen(false)} className="text-zinc-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-zinc-400">
              Paste conversation logs, documentation, or technical notes. ATLAS will run the local micro-model to extract entities and relationships, updating the graph automatically.
            </p>

            <textarea
              rows={6}
              value={extractInput}
              onChange={(e) => setExtractInput(e.target.value)}
              placeholder="e.g. Akash is building COPPER, a local AI OS. COPPER uses FastAPI for the backend and ChromaDB for vector storage..."
              className="w-full p-3 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
            />

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsExtractModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-zinc-900 text-zinc-400 hover:text-white text-xs font-bold"
              >
                Cancel
              </button>
              <button
                disabled={isExtracting || !extractInput.trim()}
                onClick={handleExtractKnowledge}
                className="px-4 py-2 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300 disabled:opacity-50 flex items-center gap-1.5 shadow-[0_0_15px_rgba(0,240,255,0.4)]"
              >
                {isExtracting ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Extracting...</span>
                  </>
                ) : (
                  <>
                    <Zap size={14} />
                    <span>Run Extraction</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Entity Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleAddEntity}
            className="w-full max-w-md bg-[#0a0f18] border border-cyber-cyan/30 rounded-2xl p-6 shadow-2xl space-y-4"
          >
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <h3 className="text-base font-bold text-white font-display">Add Knowledge Entity</h3>
              <button type="button" onClick={() => setIsAddModalOpen(false)} className="text-zinc-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div>
              <label className="block text-[11px] text-zinc-400 mb-1">Entity Name</label>
              <input
                type="text"
                required
                value={newEntityName}
                onChange={(e) => setNewEntityName(e.target.value)}
                placeholder="e.g. PyTorch, Akash, COPPER"
                className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Entity Type</label>
                <select
                  value={newEntityType}
                  onChange={(e) => setNewEntityType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
                >
                  <option value="PROJECT">PROJECT</option>
                  <option value="PERSON">PERSON</option>
                  <option value="TECHNOLOGY">TECHNOLOGY</option>
                  <option value="ORGANIZATION">ORGANIZATION</option>
                  <option value="CONCEPT">CONCEPT</option>
                  <option value="DATE_EVENT">DATE_EVENT</option>
                  <option value="LOCATION">LOCATION</option>
                  <option value="FILE">FILE</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">
                  Confidence ({Math.round(newEntityConfidence * 100)}%)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  value={newEntityConfidence}
                  onChange={(e) => setNewEntityConfidence(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 mt-2"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-zinc-400 mb-1">Context / Description</label>
              <input
                type="text"
                value={newEntityContext}
                onChange={(e) => setNewEntityContext(e.target.value)}
                placeholder="Brief description or context"
                className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-zinc-900 text-zinc-400 hover:text-white text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300 shadow-[0_0_15px_rgba(0,240,255,0.4)]"
              >
                Save Entity
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
