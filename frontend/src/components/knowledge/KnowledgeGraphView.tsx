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
  Link as LinkIcon,
  Play,
  Pause,
  Download,
  Waypoints,
  Edit3,
  Database,
  ArrowRight,
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

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  id: number;
  source: D3Node;
  target: D3Node;
  source_name?: string;
  target_name?: string;
  type: string;
  confidence: number;
  context?: string;
  evidence_count: number;
  metadata?: Record<string, unknown>;
  linkNum?: number;
  totalLinks?: number;
}

export const KnowledgeGraphView: React.FC = () => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const simulationRef = useRef<d3.Simulation<D3Node, D3Link> | null>(null);

  const [entities, setEntities] = useState<KnowledgeEntityItem[]>([]);
  const [relationships, setRelationships] = useState<KnowledgeRelationshipItem[]>([]);
  const [stats, setStats] = useState<KnowledgeStatsResponse["stats"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("ALL");

  // Selection Drawers
  const [selectedEntity, setSelectedEntity] = useState<KnowledgeEntityItem | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<KnowledgeRelationshipItem | null>(null);
  const [focusedEntityName, setFocusedEntityName] = useState<string | null>(null);

  // Physics state
  const [isPhysicsRunning, setIsPhysicsRunning] = useState(true);

  // Modals
  const [isExtractModalOpen, setIsExtractModalOpen] = useState(false);
  const [extractInput, setExtractInput] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);

  const [isAddEntityModalOpen, setIsAddEntityModalOpen] = useState(false);
  const [newEntityName, setNewEntityName] = useState("");
  const [newEntityType, setNewEntityType] = useState("PROJECT");
  const [newEntityContext, setNewEntityContext] = useState("");
  const [newEntityConfidence, setNewEntityConfidence] = useState(0.9);

  const [isAddRelModalOpen, setIsAddRelModalOpen] = useState(false);
  const [relSource, setRelSource] = useState("");
  const [relTarget, setRelTarget] = useState("");
  const [relType, setRelType] = useState("USES");
  const [relConfidence, setRelConfidence] = useState(0.9);
  const [relContext, setRelContext] = useState("");

  // Path Finder Tool
  const [isPathModalOpen, setIsPathModalOpen] = useState(false);
  const [pathSource, setPathSource] = useState("");
  const [pathTarget, setPathTarget] = useState("");
  const [activePath, setActivePath] = useState<any[] | null>(null);
  const [pathSearching, setPathSearching] = useState(false);
  const [pathError, setPathError] = useState<string | null>(null);

  // Inline editing state
  const [isEditingEntity, setIsEditingEntity] = useState(false);
  const [editEntityName, setEditEntityName] = useState("");
  const [editEntityType, setEditEntityType] = useState("");
  const [editEntityConf, setEditEntityConf] = useState(0.8);
  const [editEntityContext, setEditEntityContext] = useState("");

  const [isEditingRel, setIsEditingRel] = useState(false);
  const [editRelType, setEditRelType] = useState("");
  const [editRelConf, setEditRelConf] = useState(0.8);
  const [editRelContext, setEditRelContext] = useState("");

  // Zoom reference
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const fetchGraphData = async (focusEntity?: string) => {
    setLoading(true);
    try {
      if (focusEntity) {
        const sub = await knowledgeAPI.getSubgraph({ entity: focusEntity, depth: 2, max_nodes: 80 });
        setEntities(sub.nodes);
        setRelationships(sub.links || sub.edges || []);
      } else {
        const sub = await knowledgeAPI.getSubgraph({ depth: 2, max_nodes: 100 });
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

  // When selectedEntity changes, prepare edit fields
  useEffect(() => {
    if (selectedEntity) {
      setEditEntityName(selectedEntity.name);
      setEditEntityType(selectedEntity.type);
      setEditEntityConf(selectedEntity.confidence || 0.8);
      setEditEntityContext(selectedEntity.context || "");
      setIsEditingEntity(false);
      setSelectedRelationship(null);
    }
  }, [selectedEntity]);

  // When selectedRelationship changes, prepare edit fields
  useEffect(() => {
    if (selectedRelationship) {
      setEditRelType(selectedRelationship.type);
      setEditRelConf(selectedRelationship.confidence || 0.8);
      setEditRelContext(selectedRelationship.context || "");
      setIsEditingRel(false);
      setSelectedEntity(null);
    }
  }, [selectedRelationship]);

  // Filtered nodes & links
  const filteredData = useMemo(() => {
    const matchedNodeNames = new Set<string>();

    const nodes = entities.filter((e) => {
      const typeMatch = selectedType === "ALL" || e.type.toUpperCase() === selectedType;
      const searchMatch =
        !searchQuery ||
        e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.context && e.context.toLowerCase().includes(searchQuery.toLowerCase()));
      const ok = typeMatch && searchMatch;
      if (ok) matchedNodeNames.add((e.canonical_name || e.name).toLowerCase().trim());
      return ok;
    });

    const links = relationships.filter((r) => {
      const srcCanon = (r.source_canonical || r.source || "").toLowerCase().trim();
      const tgtCanon = (r.target_canonical || r.target || "").toLowerCase().trim();
      return matchedNodeNames.has(srcCanon) && matchedNodeNames.has(tgtCanon);
    });

    return { nodes, links };
  }, [entities, relationships, selectedType, searchQuery]);

  // D3 Force Simulation with curved multi-edges and interactive inspect
  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = containerRef.current.clientWidth || 900;
    const height = containerRef.current.clientHeight || 650;

    // Defs & Arrowheads
    const defs = svg.append("defs");

    // Standard arrow
    defs
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 10)
      .attr("refY", 0)
      .attr("markerWidth", 5)
      .attr("markerHeight", 5)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#00f0ff")
      .attr("opacity", 0.7);

    // Golden path arrow
    defs
      .append("marker")
      .attr("id", "arrowhead-path")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 10)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#fbbf24")
      .attr("opacity", 0.95);

    // Glow filter
    const filter = defs.append("filter").attr("id", "glow");
    filter.append("feGaussianBlur").attr("stdDeviation", "3").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const g = svg.append("g").attr("class", "graph-root");

    // Zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.15, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    svg.call(zoom);
    zoomRef.current = zoom;

    // Build Node Map
    const nodes: D3Node[] = filteredData.nodes.map((d) => ({
      ...d,
      r: Math.max(16, Math.min(30, 15 + (d.evidence_count || 1) * 1.8 + (d.confidence || 0.8) * 5)),
    }));

    const nodeMap = new Map<string, D3Node>();
    for (const n of nodes) {
      nodeMap.set((n.canonical_name || n.name).toLowerCase().trim(), n);
      nodeMap.set(n.name.toLowerCase().trim(), n);
    }

    // Process Links & Group for Curved Paths
    const rawLinks: { rel: KnowledgeRelationshipItem; srcNode: D3Node; tgtNode: D3Node; pairKey: string }[] = [];
    const pairGroups: Record<string, number> = {};

    for (const rel of filteredData.links) {
      const sKey = (rel.source_canonical || rel.source || "").toLowerCase().trim();
      const tKey = (rel.target_canonical || rel.target || "").toLowerCase().trim();
      const srcNode = nodeMap.get(sKey);
      const tgtNode = nodeMap.get(tKey);
      if (srcNode && tgtNode) {
        const pairKey = [srcNode.canonical_name, tgtNode.canonical_name].sort().join("---");
        pairGroups[pairKey] = (pairGroups[pairKey] || 0) + 1;
        rawLinks.push({ rel, srcNode, tgtNode, pairKey });
      }
    }

    const pairIndices: Record<string, number> = {};
    const links: D3Link[] = rawLinks.map(({ rel, srcNode, tgtNode, pairKey }) => {
      const idx = pairIndices[pairKey] || 0;
      pairIndices[pairKey] = idx + 1;
      return {
        id: rel.id,
        source: srcNode,
        target: tgtNode,
        source_name: rel.source,
        target_name: rel.target,
        type: rel.type,
        confidence: rel.confidence,
        context: rel.context,
        evidence_count: rel.evidence_count,
        metadata: rel.metadata,
        linkNum: idx,
        totalLinks: pairGroups[pairKey] || 1,
      };
    });

    // Active path node/link canonical sets
    const pathNodeCanons = new Set<string>();
    const pathLinkKeys = new Set<string>();
    if (activePath && activePath.length > 0) {
      for (let i = 0; i < activePath.length; i++) {
        const step = activePath[i];
        if (step.entity && step.entity.canonical_name) {
          pathNodeCanons.add(step.entity.canonical_name.toLowerCase());
        }
        if (step.relationship_to_next) {
          const r = step.relationship_to_next;
          const k1 = `${(r.source || "").toLowerCase()}->${(r.target || "").toLowerCase()}`;
          const k2 = `${(r.target || "").toLowerCase()}->${(r.source || "").toLowerCase()}`;
          pathLinkKeys.add(k1);
          pathLinkKeys.add(k2);
        }
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
          .distance(130),
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<D3Node>().radius((d) => (d.r || 18) + 18));

    simulationRef.current = simulation;

    // Render Links as Curved Paths
    const linkGroup = g.append("g").attr("class", "links");
    const linkPath = linkGroup
      .selectAll("path")
      .data(links)
      .enter()
      .append("path")
      .attr("fill", "none")
      .attr("stroke", (d) => {
        const isPath =
          pathLinkKeys.has(`${d.source.canonical_name}->${d.target.canonical_name}`) ||
          pathLinkKeys.has(`${d.target.canonical_name}->${d.source.canonical_name}`);
        if (isPath) return "#fbbf24";
        if (selectedRelationship && selectedRelationship.id === d.id) return "#00f0ff";
        return "#00f0ff";
      })
      .attr("stroke-opacity", (d) => {
        const isPath =
          pathLinkKeys.has(`${d.source.canonical_name}->${d.target.canonical_name}`) ||
          pathLinkKeys.has(`${d.target.canonical_name}->${d.source.canonical_name}`);
        if (isPath) return 0.95;
        if (selectedRelationship && selectedRelationship.id === d.id) return 0.95;
        return 0.4;
      })
      .attr("stroke-width", (d) => {
        const isPath =
          pathLinkKeys.has(`${d.source.canonical_name}->${d.target.canonical_name}`) ||
          pathLinkKeys.has(`${d.target.canonical_name}->${d.source.canonical_name}`);
        if (isPath) return 3;
        if (selectedRelationship && selectedRelationship.id === d.id) return 2.5;
        return Math.max(1.3, (d.confidence || 0.8) * 2.2);
      })
      .attr("marker-end", (d) => {
        const isPath =
          pathLinkKeys.has(`${d.source.canonical_name}->${d.target.canonical_name}`) ||
          pathLinkKeys.has(`${d.target.canonical_name}->${d.source.canonical_name}`);
        return isPath ? "url(#arrowhead-path)" : "url(#arrowhead)";
      })
      .attr("cursor", "pointer")
      .on("click", (_event, d) => {
        _event.stopPropagation();
        setSelectedRelationship({
          id: d.id,
          source: d.source_name || d.source.name,
          target: d.target_name || d.target.name,
          type: d.type,
          confidence: d.confidence,
          context: d.context,
          evidence_count: d.evidence_count,
          metadata: d.metadata,
        });
      });

    // Link Labels
    const linkLabelGroup = g.append("g").attr("class", "link-labels");
    const linkLabels = linkLabelGroup
      .selectAll("text")
      .data(links)
      .enter()
      .append("text")
      .attr("font-family", "'Oxanium', monospace")
      .attr("font-size", "9px")
      .attr("font-weight", "600")
      .attr("fill", (d) => {
        const isPath =
          pathLinkKeys.has(`${d.source.canonical_name}->${d.target.canonical_name}`) ||
          pathLinkKeys.has(`${d.target.canonical_name}->${d.source.canonical_name}`);
        return isPath ? "#fde047" : "#67e8f9";
      })
      .attr("opacity", 0.8)
      .attr("text-anchor", "middle")
      .attr("cursor", "pointer")
      .text((d) => d.type)
      .on("click", (_event, d) => {
        _event.stopPropagation();
        setSelectedRelationship({
          id: d.id,
          source: d.source_name || d.source.name,
          target: d.target_name || d.target.name,
          type: d.type,
          confidence: d.confidence,
          context: d.context,
          evidence_count: d.evidence_count,
          metadata: d.metadata,
        });
      });

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
            if (!event.active && isPhysicsRunning) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (_event, d) => {
            if (!isPhysicsRunning) return;
            // Node stays pinned at drop location; double-click unpins
            d.fx = d.x;
            d.fy = d.y;
          }),
      )
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedEntity(d);
      })
      .on("dblclick", (event, d) => {
        event.stopPropagation();
        d.fx = null;
        d.fy = null;
        if (isPhysicsRunning) simulation.alpha(0.2).restart();
      });

    // Outer glow circle
    node
      .append("circle")
      .attr("r", (d) => (d.r || 18) + 4)
      .attr("fill", "none")
      .attr("stroke", (d) => {
        if (pathNodeCanons.has(d.canonical_name.toLowerCase())) return "#fbbf24";
        const c = ENTITY_TYPE_COLORS[d.type.toUpperCase()] || DEFAULT_COLOR;
        return c.border;
      })
      .attr("stroke-width", (d) => (pathNodeCanons.has(d.canonical_name.toLowerCase()) ? 2.5 : 1.5))
      .attr("opacity", 0.7)
      .attr("filter", "url(#glow)");

    // Inner filled circle
    node
      .append("circle")
      .attr("r", (d) => d.r || 18)
      .attr("fill", (d) => {
        const c = ENTITY_TYPE_COLORS[d.type.toUpperCase()] || DEFAULT_COLOR;
        return c.bg;
      })
      .attr("stroke", (d) => {
        if (pathNodeCanons.has(d.canonical_name.toLowerCase())) return "#fbbf24";
        const c = ENTITY_TYPE_COLORS[d.type.toUpperCase()] || DEFAULT_COLOR;
        return c.border;
      })
      .attr("stroke-width", 2);

    // Node Type Initials
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-family", "'Oxanium', monospace")
      .attr("font-size", "10px")
      .attr("font-weight", "bold")
      .attr("fill", "#ffffff")
      .text((d) => d.name.slice(0, 3).toUpperCase());

    // Node Label underneath
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("y", (d) => (d.r || 18) + 14)
      .attr("font-family", "'Oxanium', sans-serif")
      .attr("font-size", "11px")
      .attr("font-weight", "600")
      .attr("fill", (d) => (pathNodeCanons.has(d.canonical_name.toLowerCase()) ? "#fbbf24" : "#e2e8f0"))
      .text((d) => d.name);

    // Canvas click clears selection
    svg.on("click", () => {
      setSelectedEntity(null);
      setSelectedRelationship(null);
    });

    // Curved Path Generator in Simulation Tick
    simulation.on("tick", () => {
      linkPath.attr("d", (d) => {
        const x1 = d.source.x || 0;
        const y1 = d.source.y || 0;
        const x2 = d.target.x || 0;
        const y2 = d.target.y || 0;

        const dx = x2 - x1;
        const dy = y2 - y1;
        const dr = Math.sqrt(dx * dx + dy * dy) || 1;

        // Trim endpoints to touch node borders cleanly
        const r1 = d.source.r || 18;
        const r2 = d.target.r || 18;
        const ux = dx / dr;
        const uy = dy / dr;

        const sx = x1 + ux * r1;
        const sy = y1 + uy * r1;
        const tx = x2 - ux * (r2 + 4);
        const ty = y2 - uy * (r2 + 4);

        const total = d.totalLinks || 1;
        const num = d.linkNum || 0;

        if (total === 1) {
          return `M ${sx} ${sy} L ${tx} ${ty}`;
        }

        // Quadratic Bézier curve with normal offset
        const nx = -dy / dr;
        const ny = dx / dr;
        const offset = (num - (total - 1) / 2) * 26;
        const cx = (sx + tx) / 2 + nx * offset;
        const cy = (sy + ty) / 2 + ny * offset;

        return `M ${sx} ${sy} Q ${cx} ${cy} ${tx} ${ty}`;
      });

      linkLabels
        .attr("x", (d) => {
          const x1 = d.source.x || 0;
          const y1 = d.source.y || 0;
          const x2 = d.target.x || 0;
          const y2 = d.target.y || 0;
          const dx = x2 - x1;
          const dy = y2 - y1;
          const dr = Math.sqrt(dx * dx + dy * dy) || 1;
          const total = d.totalLinks || 1;
          const num = d.linkNum || 0;
          if (total === 1) return (x1 + x2) / 2;
          const nx = -dy / dr;
          const offset = (num - (total - 1) / 2) * 26;
          return (x1 + x2) / 2 + nx * (offset * 0.6);
        })
        .attr("y", (d) => {
          const x1 = d.source.x || 0;
          const y1 = d.source.y || 0;
          const x2 = d.target.x || 0;
          const y2 = d.target.y || 0;
          const dx = x2 - x1;
          const dy = y2 - y1;
          const dr = Math.sqrt(dx * dx + dy * dy) || 1;
          const total = d.totalLinks || 1;
          const num = d.linkNum || 0;
          if (total === 1) return (y1 + y2) / 2;
          const ny = dx / dr;
          const offset = (num - (total - 1) / 2) * 26;
          return (y1 + y2) / 2 + ny * (offset * 0.6);
        });

      node.attr("transform", (d) => `translate(${d.x || 0},${d.y || 0})`);
    });

    return () => {
      simulation.stop();
    };
  }, [filteredData, activePath, selectedRelationship]);

  // Zoom controls
  const handleZoom = (factor: number) => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(300).call(zoomRef.current.scaleBy, factor);
  };

  const handleResetZoom = () => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(400).call(zoomRef.current.transform, d3.zoomIdentity);
  };

  const togglePhysics = () => {
    if (!simulationRef.current) return;
    if (isPhysicsRunning) {
      simulationRef.current.stop();
      setIsPhysicsRunning(false);
    } else {
      simulationRef.current.restart().alphaTarget(0.1);
      setTimeout(() => {
        simulationRef.current?.alphaTarget(0);
      }, 500);
      setIsPhysicsRunning(true);
    }
  };

  // Seed default graph
  const handleSeedDefaults = async () => {
    setLoading(true);
    try {
      await knowledgeAPI.seedDefaults();
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Seed] Failed:", err);
    } finally {
      setLoading(false);
    }
  };

  // Sync epistemic memories
  const handleSyncMemories = async () => {
    setLoading(true);
    try {
      await knowledgeAPI.syncMemories();
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Sync] Failed:", err);
    } finally {
      setLoading(false);
    }
  };

  // Export graph
  const handleExportGraph = async () => {
    try {
      const data = await knowledgeAPI.exportGraph();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `copper_knowledge_graph_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[ATLAS Export] Failed:", err);
    }
  };

  // Entity operations
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
      setIsAddEntityModalOpen(false);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Entity] Add failed:", err);
    }
  };

  const handleUpdateEntity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEntity || !editEntityName.trim()) return;
    try {
      const res = await knowledgeAPI.updateEntity(selectedEntity.id, {
        name: editEntityName.trim(),
        type: editEntityType,
        confidence: editEntityConf,
        context: editEntityContext.trim(),
      });
      setSelectedEntity(res.entity);
      setIsEditingEntity(false);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Entity] Update failed:", err);
    }
  };

  const handleDeleteEntity = async (id: number) => {
    try {
      await knowledgeAPI.deleteEntity(id);
      setSelectedEntity(null);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Entity] Delete failed:", err);
    }
  };

  // Relationship operations
  const handleAddRelationship = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!relSource.trim() || !relTarget.trim()) return;
    try {
      await knowledgeAPI.createRelationship({
        source: relSource.trim(),
        target: relTarget.trim(),
        type: relType,
        confidence: relConfidence,
        context: relContext.trim(),
      });
      setRelSource("");
      setRelTarget("");
      setRelContext("");
      setIsAddRelModalOpen(false);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Rel] Add failed:", err);
    }
  };

  const handleUpdateRelationship = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRelationship) return;
    try {
      const res = await knowledgeAPI.updateRelationship(selectedRelationship.id, {
        type: editRelType,
        confidence: editRelConf,
        context: editRelContext.trim(),
      });
      setSelectedRelationship(res.relationship);
      setIsEditingRel(false);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Rel] Update failed:", err);
    }
  };

  const handleDeleteRelationship = async (id: number) => {
    try {
      await knowledgeAPI.deleteRelationship(id);
      setSelectedRelationship(null);
      await fetchGraphData(focusedEntityName || undefined);
    } catch (err) {
      console.error("[ATLAS Rel] Delete failed:", err);
    }
  };

  // Path Finder
  const handleFindPath = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pathSource.trim() || !pathTarget.trim()) return;
    setPathSearching(true);
    setPathError(null);
    try {
      const res = await knowledgeAPI.getPath(pathSource.trim(), pathTarget.trim());
      setActivePath(res.path || []);
    } catch (err: any) {
      setActivePath(null);
      setPathError(err?.response?.data?.detail || "No traversal path found between these entities.");
    } finally {
      setPathSearching(false);
    }
  };

  // Text Extraction
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

  // Neighbors of currently selected entity
  const selectedEntityNeighbors = useMemo(() => {
    if (!selectedEntity) return [];
    const canon = (selectedEntity.canonical_name || selectedEntity.name).toLowerCase();
    const neighborMap = new Map<string, { entityName: string; relationType: string; isOutgoing: boolean }>();
    for (const r of relationships) {
      const s = (r.source_canonical || r.source || "").toLowerCase();
      const t = (r.target_canonical || r.target || "").toLowerCase();
      if (s === canon) {
        neighborMap.set(t, { entityName: r.target, relationType: r.type, isOutgoing: true });
      } else if (t === canon) {
        neighborMap.set(s, { entityName: r.source, relationType: r.type, isOutgoing: false });
      }
    }
    return Array.from(neighborMap.values());
  }, [selectedEntity, relationships]);

  return (
    <div className="flex flex-col h-full w-full bg-[#05080e]/95 text-slate-200 select-none font-mono">
      {/* Top HUD Banner */}
      <div className="px-6 py-3.5 border-b border-cyber-cyan/20 bg-black/40 backdrop-blur-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyber-cyan/15 border border-cyber-cyan/40 flex items-center justify-center text-cyber-cyan shadow-[0_0_15px_rgba(0,240,255,0.25)]">
            <Network size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white font-display tracking-tight">
                ATLAS Memory Graph
              </h1>
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-verdigris/15 text-verdigris border border-verdigris/30 animate-pulse">
                v2.0 TOPOLOGICAL
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Multi-directed Entity & Causal Network • Graph-Augmented Bayesian Context
            </p>
          </div>
        </div>

        {/* Global Stats Counter */}
        {stats && (
          <div className="flex items-center gap-2.5 text-xs">
            <div className="px-2.5 py-1 rounded-lg bg-black/60 border border-cyber-cyan/20">
              <span className="text-zinc-500 block text-[8px] uppercase font-mono">Entities</span>
              <span className="text-cyber-cyan font-bold">{stats.total_entities}</span>
            </div>
            <div className="px-2.5 py-1 rounded-lg bg-black/60 border border-cyber-cyan/20">
              <span className="text-zinc-500 block text-[8px] uppercase font-mono">Relationships</span>
              <span className="text-accent-400 font-bold">{stats.total_relationships}</span>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setIsAddEntityModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-cyan/15 hover:bg-cyber-cyan/25 text-cyber-cyan border border-cyber-cyan/40 text-xs font-bold transition-all shadow-sm cursor-pointer"
          >
            <Plus size={13} />
            <span>Entity</span>
          </button>
          <button
            onClick={() => setIsAddRelModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-900/30 hover:bg-cyan-900/50 text-cyan-300 border border-cyan-700/50 text-xs font-bold transition-all shadow-sm cursor-pointer"
          >
            <LinkIcon size={13} />
            <span>Relationship</span>
          </button>
          <button
            onClick={() => setIsPathModalOpen(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm cursor-pointer border ${
              activePath
                ? "bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-[0_0_10px_rgba(245,158,11,0.3)]"
                : "bg-zinc-900/80 text-zinc-300 border-zinc-700/60 hover:bg-zinc-800"
            }`}
          >
            <Waypoints size={13} />
            <span>{activePath ? `Path Active (${activePath.length})` : "Find Path"}</span>
          </button>
          <button
            onClick={() => setIsExtractModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-950/40 hover:bg-purple-900/40 text-purple-300 border border-purple-800/50 text-xs font-bold transition-all cursor-pointer"
          >
            <Sparkles size={13} />
            <span>Extract</span>
          </button>
          <button
            onClick={handleSyncMemories}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/40 text-emerald-300 border border-emerald-800/50 text-xs font-bold transition-all cursor-pointer"
            title="Sync active Epistemic Memories into graph"
          >
            <Database size={13} />
            <span>Sync</span>
          </button>
          <button
            onClick={handleExportGraph}
            className="p-1.5 rounded-lg bg-black/50 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all cursor-pointer"
            title="Export Graph JSON"
          >
            <Download size={14} />
          </button>
          <button
            onClick={() => fetchGraphData(focusedEntityName || undefined)}
            className="p-1.5 rounded-lg bg-black/50 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all cursor-pointer"
            title="Refresh Graph"
          >
            <RefreshCw size={14} className={loading ? "animate-spin text-cyber-cyan" : ""} />
          </button>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="px-6 py-2.5 border-b border-zinc-800/80 bg-black/30 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-zinc-500 text-[11px] uppercase tracking-wider flex items-center gap-1">
            <Layers size={12} /> Filter:
          </span>
          {["ALL", "PROJECT", "TECHNOLOGY", "PERSON", "CONCEPT", "ORGANIZATION"].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all cursor-pointer ${
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
              className="px-2 py-0.5 rounded text-[10px] bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1 hover:bg-red-500/30 cursor-pointer"
            >
              <X size={11} /> Reset Focus ({focusedEntityName})
            </button>
          )}
          {activePath && (
            <button
              onClick={() => setActivePath(null)}
              className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 hover:bg-amber-500/30 cursor-pointer"
            >
              <X size={11} /> Clear Path
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

      {/* Main Graph Canvas Area */}
      <div className="relative flex-1 w-full overflow-hidden" ref={containerRef}>
        <svg ref={svgRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

        {/* Empty State Overlay */}
        {!loading && filteredData.nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none p-6 text-center">
            <div className="p-8 rounded-2xl bg-black/80 border border-cyber-cyan/30 backdrop-blur-2xl max-w-md pointer-events-auto space-y-4 shadow-[0_0_40px_rgba(0,0,0,0.8)]">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-cyber-cyan/15 border border-cyber-cyan/40 flex items-center justify-center text-cyber-cyan shadow-[0_0_20px_rgba(0,240,255,0.2)]">
                <Network size={26} />
              </div>
              <div>
                <h3 className="text-base font-bold text-white font-display">Knowledge Graph Is Sparse</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Populate your local system graph with COPPER's default architectural entities, or extract relationships directly from notes.
                </p>
              </div>
              <div className="flex gap-2 justify-center pt-2">
                <button
                  onClick={handleSeedDefaults}
                  className="px-4 py-2 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300 transition-all shadow-[0_0_15px_rgba(0,240,255,0.4)] cursor-pointer"
                >
                  Seed Architecture Graph
                </button>
                <button
                  onClick={() => setIsAddEntityModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-700 text-white text-xs hover:bg-zinc-800 transition-all cursor-pointer"
                >
                  Add Entity
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Floating Zoom & Simulation Controls */}
        <div className="absolute bottom-6 right-6 flex flex-col gap-1.5 bg-black/70 border border-zinc-800 p-1.5 rounded-xl backdrop-blur-md shadow-xl z-20">
          <button
            onClick={() => handleZoom(1.25)}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn size={15} />
          </button>
          <button
            onClick={() => handleZoom(0.8)}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut size={15} />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all cursor-pointer"
            title="Reset View"
          >
            <RotateCcw size={15} />
          </button>
          <div className="w-full h-px bg-zinc-800 my-0.5" />
          <button
            onClick={togglePhysics}
            className={`p-2 rounded-lg transition-all cursor-pointer ${
              isPhysicsRunning ? "text-cyber-cyan hover:bg-cyber-cyan/15" : "text-zinc-500 hover:bg-zinc-800"
            }`}
            title={isPhysicsRunning ? "Pause Physics Simulation" : "Resume Physics Simulation"}
          >
            {isPhysicsRunning ? <Pause size={15} /> : <Play size={15} />}
          </button>
        </div>

        {/* Entity Inspector Side Drawer */}
        {selectedEntity && (
          <div className="absolute top-4 right-4 w-88 max-h-[calc(100%-2rem)] bg-[#05080e]/95 border border-cyber-cyan/30 rounded-2xl shadow-[0_0_35px_rgba(0,0,0,0.85)] backdrop-blur-2xl p-4 overflow-y-auto custom-scrollbar z-30 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: (ENTITY_TYPE_COLORS[selectedEntity.type.toUpperCase()] || DEFAULT_COLOR).border,
                  }}
                />
                <h3 className="text-sm font-bold text-white font-display truncate max-w-[190px]">
                  {selectedEntity.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEntity(null)}
                className="text-zinc-500 hover:text-white transition-all cursor-pointer"
              >
                <X size={15} />
              </button>
            </div>

            {isEditingEntity ? (
              <form onSubmit={handleUpdateEntity} className="space-y-3 text-xs">
                <div>
                  <label className="text-zinc-400 block text-[10px] uppercase mb-1">Entity Name</label>
                  <input
                    type="text"
                    required
                    value={editEntityName}
                    onChange={(e) => setEditEntityName(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-black/70 border border-zinc-800 text-white outline-none focus:border-cyber-cyan text-xs"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-zinc-400 block text-[10px] uppercase mb-1">Type</label>
                    <select
                      value={editEntityType}
                      onChange={(e) => setEditEntityType(e.target.value)}
                      className="w-full px-2 py-1.5 rounded-lg bg-black/70 border border-zinc-800 text-white outline-none focus:border-cyber-cyan text-xs"
                    >
                      {Object.keys(ENTITY_TYPE_COLORS).map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-zinc-400 block text-[10px] uppercase mb-1">
                      Conf ({Math.round(editEntityConf * 100)}%)
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="1.0"
                      step="0.05"
                      value={editEntityConf}
                      onChange={(e) => setEditEntityConf(parseFloat(e.target.value))}
                      className="w-full accent-cyber-cyan mt-1"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-zinc-400 block text-[10px] uppercase mb-1">Context</label>
                  <textarea
                    rows={3}
                    value={editEntityContext}
                    onChange={(e) => setEditEntityContext(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-black/70 border border-zinc-800 text-white outline-none focus:border-cyber-cyan text-xs resize-none"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setIsEditingEntity(false)}
                    className="px-3 py-1 rounded-lg bg-zinc-900 text-zinc-400 hover:text-white text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 rounded-lg bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-500 uppercase text-[10px]">Type</span>
                  <span
                    className="px-2 py-0.5 rounded text-[10px] font-bold"
                    style={{
                      backgroundColor: (ENTITY_TYPE_COLORS[selectedEntity.type.toUpperCase()] || DEFAULT_COLOR).bg,
                      color: (ENTITY_TYPE_COLORS[selectedEntity.type.toUpperCase()] || DEFAULT_COLOR).text,
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
                  <span className="text-zinc-500 uppercase text-[10px]">Evidence Observations</span>
                  <span className="text-zinc-300 font-bold">{selectedEntity.evidence_count || 1}x</span>
                </div>

                {selectedEntity.context && (
                  <div className="p-2.5 rounded-lg bg-black/60 border border-zinc-800/80 text-[11px] text-zinc-300 leading-relaxed font-sans">
                    <span className="text-zinc-500 block text-[9px] uppercase mb-1 font-mono">Context Snippet</span>
                    {selectedEntity.context}
                  </div>
                )}

                {/* Connected Neighbors List */}
                {selectedEntityNeighbors.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-zinc-500 block text-[10px] uppercase">Connected Network ({selectedEntityNeighbors.length})</span>
                    <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto custom-scrollbar">
                      {selectedEntityNeighbors.map((n, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            const found = entities.find(
                              (e) => (e.canonical_name || e.name).toLowerCase() === n.entityName.toLowerCase(),
                            );
                            if (found) setSelectedEntity(found);
                          }}
                          className="px-2 py-1 rounded bg-zinc-900/90 border border-zinc-800 hover:border-cyber-cyan/50 text-[10px] flex items-center gap-1 text-zinc-300 hover:text-white transition-all cursor-pointer"
                        >
                          <span className="text-zinc-500 text-[8px]">{n.isOutgoing ? "→" : "←"} {n.relationType}</span>
                          <span className="font-semibold">{n.entityName}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Entity Actions */}
            {!isEditingEntity && (
              <div className="pt-2 border-t border-zinc-800 flex flex-wrap gap-1.5">
                <button
                  onClick={() => setIsEditingEntity(true)}
                  className="flex-1 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-750 text-xs font-bold transition-all flex items-center justify-center gap-1 cursor-pointer"
                >
                  <Edit3 size={13} /> Edit
                </button>
                <button
                  onClick={() => setFocusedEntityName(selectedEntity.name)}
                  className="flex-1 py-1.5 rounded-lg bg-cyber-cyan/15 hover:bg-cyber-cyan/25 text-cyber-cyan border border-cyber-cyan/30 text-xs font-bold transition-all flex items-center justify-center gap-1 cursor-pointer"
                >
                  <Maximize2 size={13} /> Focus
                </button>
                <button
                  onClick={() => {
                    setPathSource(selectedEntity.name);
                    setIsPathModalOpen(true);
                  }}
                  className="p-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 transition-all cursor-pointer"
                  title="Find Path From Here"
                >
                  <Waypoints size={14} />
                </button>
                <button
                  onClick={() => handleDeleteEntity(selectedEntity.id)}
                  className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition-all cursor-pointer"
                  title="Delete Entity"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Relationship Inspector Side Drawer */}
        {selectedRelationship && (
          <div className="absolute top-4 right-4 w-88 max-h-[calc(100%-2rem)] bg-[#05080e]/95 border border-cyber-cyan/30 rounded-2xl shadow-[0_0_35px_rgba(0,0,0,0.85)] backdrop-blur-2xl p-4 overflow-y-auto custom-scrollbar z-30 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center gap-2">
                <LinkIcon size={16} className="text-cyber-cyan" />
                <h3 className="text-sm font-bold text-white font-display truncate max-w-[200px]">
                  Relationship Inspector
                </h3>
              </div>
              <button
                onClick={() => setSelectedRelationship(null)}
                className="text-zinc-500 hover:text-white transition-all cursor-pointer"
              >
                <X size={15} />
              </button>
            </div>

            {isEditingRel ? (
              <form onSubmit={handleUpdateRelationship} className="space-y-3 text-xs">
                <div>
                  <label className="text-zinc-400 block text-[10px] uppercase mb-1">Relation Type</label>
                  <select
                    value={editRelType}
                    onChange={(e) => setEditRelType(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-black/70 border border-zinc-800 text-white outline-none focus:border-cyber-cyan text-xs"
                  >
                    {["WORKS_ON", "USES", "DEPENDS_ON", "CREATED_BY", "PART_OF", "KNOWS", "RELATED_TO"].map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-zinc-400 block text-[10px] uppercase mb-1">
                    Confidence ({Math.round(editRelConf * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.0"
                    step="0.05"
                    value={editRelConf}
                    onChange={(e) => setEditRelConf(parseFloat(e.target.value))}
                    className="w-full accent-cyber-cyan mt-1"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block text-[10px] uppercase mb-1">Context Notes</label>
                  <textarea
                    rows={3}
                    value={editRelContext}
                    onChange={(e) => setEditRelContext(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-black/70 border border-zinc-800 text-white outline-none focus:border-cyber-cyan text-xs resize-none"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setIsEditingRel(false)}
                    className="px-3 py-1 rounded-lg bg-zinc-900 text-zinc-400 hover:text-white text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 rounded-lg bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3.5 text-xs">
                {/* Edge endpoints */}
                <div className="p-3 rounded-xl bg-black/60 border border-zinc-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-zinc-500 uppercase">Source</span>
                    <span className="font-bold text-cyber-cyan text-xs">{selectedRelationship.source}</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-300 border border-zinc-700">
                      —[{selectedRelationship.type}]→
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-zinc-500 uppercase">Target</span>
                    <span className="font-bold text-accent-400 text-xs">{selectedRelationship.target}</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-zinc-500 uppercase text-[10px]">Confidence</span>
                  <span className="text-verdigris font-bold">
                    {Math.round((selectedRelationship.confidence || 0.8) * 100)}%
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-zinc-500 uppercase text-[10px]">Reinforcement Count</span>
                  <span className="text-zinc-300 font-bold">{selectedRelationship.evidence_count || 1} observations</span>
                </div>

                {selectedRelationship.context && (
                  <div className="p-2.5 rounded-lg bg-black/60 border border-zinc-800/80 text-[11px] text-zinc-300 leading-relaxed font-sans">
                    <span className="text-zinc-500 block text-[9px] uppercase mb-1 font-mono">Context Note</span>
                    {selectedRelationship.context}
                  </div>
                )}
              </div>
            )}

            {/* Relationship Actions */}
            {!isEditingRel && (
              <div className="pt-2 border-t border-zinc-800 flex gap-2">
                <button
                  onClick={() => setIsEditingRel(true)}
                  className="flex-1 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-750 text-xs font-bold transition-all flex items-center justify-center gap-1 cursor-pointer"
                >
                  <Edit3 size={13} /> Edit Link
                </button>
                <button
                  onClick={() => handleDeleteRelationship(selectedRelationship.id)}
                  className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition-all cursor-pointer"
                  title="Delete Relationship"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Path Finder Modal */}
      {isPathModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#0a0f18] border border-amber-500/30 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <Waypoints size={18} className="text-amber-400" />
                <h3 className="text-base font-bold text-white font-display">Shortest Path Finder</h3>
              </div>
              <button onClick={() => setIsPathModalOpen(false)} className="text-zinc-400 hover:text-white cursor-pointer">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleFindPath} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-zinc-400 mb-1">Source Entity</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Akash Kundu"
                    value={pathSource}
                    onChange={(e) => setPathSource(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white outline-none focus:border-amber-400"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-zinc-400 mb-1">Target Entity</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Whisper Large v3"
                    value={pathTarget}
                    onChange={(e) => setPathTarget(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white outline-none focus:border-amber-400"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="submit"
                  disabled={pathSearching || !pathSource || !pathTarget}
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs disabled:opacity-50 flex items-center gap-1.5 shadow-[0_0_15px_rgba(245,158,11,0.3)] cursor-pointer"
                >
                  <Zap size={14} />
                  <span>{pathSearching ? "Traversing..." : "Compute Path"}</span>
                </button>
              </div>
            </form>

            {pathError && (
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-800/40 text-red-300 text-xs">
                {pathError}
              </div>
            )}

            {activePath && activePath.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-zinc-800 text-xs">
                <span className="text-zinc-400 text-[10px] uppercase block">
                  Shortest Route ({activePath.length} nodes):
                </span>
                <div className="p-3 rounded-xl bg-black/80 border border-amber-500/30 space-y-2">
                  {activePath.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center text-[10px] font-bold border border-amber-500/40">
                        {idx + 1}
                      </span>
                      <span className="font-bold text-white">{step.entity.name}</span>
                      {step.relationship_to_next && (
                        <span className="text-[10px] text-zinc-400 font-mono flex items-center gap-1">
                          <ArrowRight size={10} className="text-amber-400" />
                          [{step.relationship_to_next.type}]
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Entity Modal */}
      {isAddEntityModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleAddEntity}
            className="w-full max-w-md bg-[#0a0f18] border border-cyber-cyan/30 rounded-2xl p-6 shadow-2xl space-y-4"
          >
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <h3 className="text-base font-bold text-white font-display">Add Knowledge Entity</h3>
              <button
                type="button"
                onClick={() => setIsAddEntityModalOpen(false)}
                className="text-zinc-400 hover:text-white cursor-pointer"
              >
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
                placeholder="e.g. PyTorch, Akash Kundu, COPPER"
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
                onClick={() => setIsAddEntityModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-zinc-900 text-zinc-400 hover:text-white text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300 shadow-[0_0_15px_rgba(0,240,255,0.4)] cursor-pointer"
              >
                Save Entity
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Add Relationship Modal */}
      {isAddRelModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleAddRelationship}
            className="w-full max-w-md bg-[#0a0f18] border border-cyber-cyan/30 rounded-2xl p-6 shadow-2xl space-y-4"
          >
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <h3 className="text-base font-bold text-white font-display">Add Knowledge Relationship</h3>
              <button
                type="button"
                onClick={() => setIsAddRelModalOpen(false)}
                className="text-zinc-400 hover:text-white cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Source Entity</label>
                <input
                  type="text"
                  required
                  value={relSource}
                  onChange={(e) => setRelSource(e.target.value)}
                  placeholder="e.g. COPPER"
                  className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
                />
              </div>
              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Target Entity</label>
                <input
                  type="text"
                  required
                  value={relTarget}
                  onChange={(e) => setRelTarget(e.target.value)}
                  placeholder="e.g. FastAPI"
                  className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Relationship Type</label>
                <select
                  value={relType}
                  onChange={(e) => setRelType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
                >
                  <option value="WORKS_ON">WORKS_ON</option>
                  <option value="USES">USES</option>
                  <option value="DEPENDS_ON">DEPENDS_ON</option>
                  <option value="CREATED_BY">CREATED_BY</option>
                  <option value="PART_OF">PART_OF</option>
                  <option value="KNOWS">KNOWS</option>
                  <option value="RELATED_TO">RELATED_TO</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">
                  Confidence ({Math.round(relConfidence * 100)}%)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  value={relConfidence}
                  onChange={(e) => setRelConfidence(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 mt-2"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-zinc-400 mb-1">Context / Explanation</label>
              <input
                type="text"
                value={relContext}
                onChange={(e) => setRelContext(e.target.value)}
                placeholder="e.g. Core web framework for offline API routing"
                className="w-full px-3 py-2 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsAddRelModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-zinc-900 text-zinc-400 hover:text-white text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300 shadow-[0_0_15px_rgba(0,240,255,0.4)] cursor-pointer"
              >
                Connect Entities
              </button>
            </div>
          </form>
        </div>
      )}

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
              <button onClick={() => setIsExtractModalOpen(false)} className="text-zinc-400 hover:text-white cursor-pointer">
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
              placeholder="e.g. Akash Kundu is architecting COPPER, a 100% offline personal AI OS. COPPER uses FastAPI for the backend, ChromaDB for vector storage, and React 19 for the frontend interface..."
              className="w-full p-3 rounded-xl bg-black/70 border border-zinc-800 text-white text-xs outline-none focus:border-cyber-cyan"
            />

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsExtractModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-zinc-900 text-zinc-400 hover:text-white text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                disabled={isExtracting || !extractInput.trim()}
                onClick={handleExtractKnowledge}
                className="px-4 py-2 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:bg-cyan-300 disabled:opacity-50 flex items-center gap-1.5 shadow-[0_0_15px_rgba(0,240,255,0.4)] cursor-pointer"
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
    </div>
  );
};
