import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  Users,
  Sparkles,
  Check,
  ChevronRight,
} from "lucide-react";
import { catalogAPI, type AgencyPersona } from "../../services/api";
import { PersonaDossierModal } from "./PersonaDossierModal";

interface AgencyPersonasTabProps {
  onInjectPersona?: (persona: AgencyPersona) => void;
}

export const AgencyPersonasTab: React.FC<AgencyPersonasTabProps> = ({
  onInjectPersona,
}) => {
  const [personas, setPersonas] = useState<AgencyPersona[]>([]);
  const [divisions, setDivisions] = useState<Array<{ id: string; label: string; count: number }>>([]);
  const [selectedDivision, setSelectedDivision] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedPersona, setSelectedPersona] = useState<AgencyPersona | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 24;

  useEffect(() => {
    // Load divisions
    catalogAPI
      .getDivisions()
      .then((res) => {
        if (Array.isArray(res.data)) {
          setDivisions(res.data);
        }
      })
      .catch(() => {});

    // Load initial batch of personas
    loadPersonas();
  }, []);

  const loadPersonas = async (div = "all", search = "") => {
    setLoading(true);
    try {
      const res = await catalogAPI.getPersonas({
        division: div === "all" ? undefined : div,
        search: search.trim() || undefined,
        limit: 300,
      });
      if (res.data?.personas) {
        setPersonas(res.data.personas);
      }
    } catch (err) {
      console.error("Failed to load agency personas:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDivisionChange = (div: string) => {
    setSelectedDivision(div);
    setPage(1);
    loadPersonas(div, searchQuery);
  };

  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    setPage(1);
    loadPersonas(selectedDivision, val);
  };

  const handleCopyDirective = (p: AgencyPersona, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(p.system_prompt_preview || p.description);
    setCopiedId(p.id);
    setTimeout(() => setCopiedId(null), 1800);
  };

  const openDossier = async (p: AgencyPersona) => {
    try {
      const res = await catalogAPI.getPersonaDetail(p.id);
      setSelectedPersona(res.data || p);
    } catch {
      setSelectedPersona(p);
    }
  };

  const paginatedPersonas = useMemo(() => {
    const start = (page - 1) * pageSize;
    return personas.slice(start, start + pageSize);
  }, [personas, page]);

  const totalPages = Math.ceil(personas.length / pageSize) || 1;

  const getDivisionBadgeColor = (div: string) => {
    switch (div.toLowerCase()) {
      case "engineering":
        return "bg-cyan-950/60 text-cyan-400 border-cyan-800/40";
      case "security":
        return "bg-rose-950/60 text-rose-400 border-rose-800/40";
      case "gis":
        return "bg-emerald-950/60 text-emerald-400 border-emerald-800/40";
      case "finance":
        return "bg-amber-950/60 text-amber-400 border-amber-800/40";
      case "design":
        return "bg-fuchsia-950/60 text-fuchsia-400 border-fuchsia-800/40";
      case "academic":
        return "bg-violet-950/60 text-violet-400 border-violet-800/40";
      case "marketing":
        return "bg-orange-950/60 text-orange-400 border-orange-800/40";
      case "operations":
        return "bg-sky-950/60 text-sky-400 border-sky-800/40";
      case "health":
        return "bg-teal-950/60 text-teal-400 border-teal-800/40";
      default:
        return "bg-indigo-950/60 text-indigo-400 border-indigo-800/40";
    }
  };

  return (
    <div className="space-y-4 animate-fade-in font-sans">
      {/* Search & Division Filter Header */}
      <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Users size={18} className="text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">
                Agency Specialist Squad
              </h2>
              <p className="text-[11px] text-slate-400">
                264 Autonomous Specialized Personas across 18 operational divisions
              </p>
            </div>
          </div>

          {/* Search Box */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl focus-within:border-cyan-500/50 transition-all w-full md:w-80">
            <Search size={14} className="text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search by role, vibe, or skill..."
              className="bg-transparent text-white placeholder:text-slate-500 outline-none text-xs w-full font-sans"
            />
          </div>
        </div>

        {/* Division Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none pt-1">
          <button
            onClick={() => handleDivisionChange("all")}
            className={`px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              selectedDivision === "all"
                ? "bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20"
                : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
            }`}
          >
            <span>All Divisions</span>
            <span className="text-[10px] opacity-75">({personas.length})</span>
          </button>

          {divisions.map((div) => {
            const isSelected = selectedDivision.toLowerCase() === div.id.toLowerCase();
            return (
              <button
                key={div.id}
                onClick={() => handleDivisionChange(div.id)}
                className={`px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? "bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20"
                    : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                <span>{div.label}</span>
                <span className="text-[10px] opacity-75">({div.count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid of Persona Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-8">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-44 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse p-4 space-y-3"
            >
              <div className="h-4 bg-slate-800 rounded w-2/3" />
              <div className="h-3 bg-slate-800/60 rounded w-1/3" />
              <div className="h-16 bg-slate-800/40 rounded w-full" />
            </div>
          ))}
        </div>
      ) : personas.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-2xl space-y-2">
          <Sparkles className="mx-auto text-slate-600 mb-2" size={32} />
          <h3 className="text-white font-bold text-sm">No Personas Found</h3>
          <p className="text-slate-400 text-xs">
            Try adjusting your search terms or division filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {paginatedPersonas.map((p) => {
            const badgeColor = getDivisionBadgeColor(p.division);
            return (
              <div
                key={p.id}
                onClick={() => openDossier(p)}
                className="group p-4 rounded-2xl bg-slate-900/70 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer flex flex-col justify-between space-y-3 shadow-md hover:shadow-xl hover:shadow-cyan-950/10"
              >
                <div className="space-y-2">
                  {/* Card Header: Division Tag + Role */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span
                        className={`text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded-full border ${badgeColor}`}
                      >
                        {p.division_label || p.division}
                      </span>
                      <h3 className="font-bold text-white text-sm tracking-tight mt-1.5 group-hover:text-cyan-300 transition-colors">
                        {p.name}
                      </h3>
                    </div>

                    <button
                      onClick={(e) => handleCopyDirective(p, e)}
                      title="Quick Copy Persona Directive"
                      className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white transition-all"
                    >
                      {copiedId === p.id ? (
                        <Check size={12} className="text-emerald-400" />
                      ) : (
                        <Sparkles size={12} />
                      )}
                    </button>
                  </div>

                  {/* Vibe Badge */}
                  {p.vibe && (
                    <div className="text-[11px] text-cyan-400/90 font-mono bg-cyan-950/30 px-2 py-0.5 rounded-lg border border-cyan-800/30 line-clamp-1">
                      "{p.vibe}"
                    </div>
                  )}

                  {/* Mission / Description */}
                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed font-sans">
                    {p.description}
                  </p>
                </div>

                {/* Card Footer Actions */}
                <div className="pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span className="truncate max-w-[140px] opacity-75">{p.id.split(":")[1] || p.id}</span>
                  <div className="flex items-center gap-1 text-cyan-400 group-hover:translate-x-0.5 transition-transform font-bold">
                    <span>Inspect Dossier</span>
                    <ChevronRight size={13} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs">
          <span className="text-slate-400 font-mono">
            Showing {(page - 1) * pageSize + 1}–
            {Math.min(page * pageSize, personas.length)} of {personas.length} personas
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 font-semibold"
            >
              Previous
            </button>
            <span className="text-slate-400 font-mono">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 font-semibold"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Dossier Modal */}
      <PersonaDossierModal
        persona={selectedPersona}
        onClose={() => setSelectedPersona(null)}
        onActivate={onInjectPersona}
      />
    </div>
  );
};
