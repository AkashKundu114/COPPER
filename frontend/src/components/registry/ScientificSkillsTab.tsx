import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  BookOpen,
  FlaskConical,
  Atom,
  ChevronRight,
} from "lucide-react";
import { catalogAPI, type ScientificSkill } from "../../services/api";
import { ScientificSkillModal } from "./ScientificSkillModal";

interface ScientificSkillsTabProps {
  onAttachSkill?: (skill: ScientificSkill) => void;
}

export const ScientificSkillsTab: React.FC<ScientificSkillsTabProps> = ({
  onAttachSkill,
}) => {
  const [skills, setSkills] = useState<ScientificSkill[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedSkill, setSelectedSkill] = useState<ScientificSkill | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 24;

  useEffect(() => {
    // Load skills
    loadSkills();
  }, []);

  const loadSkills = async (cat = "all", search = "") => {
    setLoading(true);
    try {
      const res = await catalogAPI.getScientificSkills({
        category: cat === "all" ? undefined : cat,
        search: search.trim() || undefined,
        limit: 200,
      });
      if (res.data?.skills) {
        setSkills(res.data.skills);
        // Extract unique categories
        const cats = Array.from(new Set(res.data.skills.map((s) => s.category))).filter(Boolean);
        if (categories.length === 0) setCategories(cats);
      }
    } catch (err) {
      console.error("Failed to load scientific skills:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat);
    setPage(1);
    loadSkills(cat, searchQuery);
  };

  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    setPage(1);
    loadSkills(selectedCategory, val);
  };

  const openSkillDetail = async (s: ScientificSkill) => {
    try {
      const res = await catalogAPI.getScientificSkillDetail(s.id);
      setSelectedSkill(res.data || s);
    } catch {
      setSelectedSkill(s);
    }
  };

  const paginatedSkills = useMemo(() => {
    const start = (page - 1) * pageSize;
    return skills.slice(start, start + pageSize);
  }, [skills, page]);

  const totalPages = Math.ceil(skills.length / pageSize) || 1;

  return (
    <div className="space-y-4 animate-fade-in font-sans">
      {/* Header & Category Filters */}
      <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <FlaskConical size={18} className="text-emerald-400" />
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">
                Scientific Intelligence & Protocol Engine
              </h2>
              <p className="text-[11px] text-slate-400">
                165 Verified Scientific Agent Skills across Life Sciences, Genomics, Chemistry & Analytics
              </p>
            </div>
          </div>

          {/* Search Box */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl focus-within:border-emerald-500/50 transition-all w-full md:w-80">
            <Search size={14} className="text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search tool, database, protein, or technique..."
              className="bg-transparent text-white placeholder:text-slate-500 outline-none text-xs w-full font-sans"
            />
          </div>
        </div>

        {/* Category Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none pt-1">
          <button
            onClick={() => handleCategoryChange("all")}
            className={`px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              selectedCategory === "all"
                ? "bg-emerald-500 text-slate-950 font-bold shadow-lg shadow-emerald-500/20"
                : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
            }`}
          >
            <span>All Disciplines</span>
            <span className="text-[10px] opacity-75">({skills.length})</span>
          </button>

          {categories.map((cat) => {
            const isSelected = selectedCategory.toLowerCase() === cat.toLowerCase();
            return (
              <button
                key={cat}
                onClick={() => handleCategoryChange(cat)}
                className={`px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? "bg-emerald-500 text-slate-950 font-bold shadow-lg shadow-emerald-500/20"
                    : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                <span>{cat}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid of Scientific Skill Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-8">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-40 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse p-4 space-y-3"
            >
              <div className="h-4 bg-slate-800 rounded w-1/2" />
              <div className="h-3 bg-slate-800/60 rounded w-1/4" />
              <div className="h-16 bg-slate-800/40 rounded w-full" />
            </div>
          ))}
        </div>
      ) : skills.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-2xl space-y-2">
          <Atom className="mx-auto text-slate-600 mb-2" size={32} />
          <h3 className="text-white font-bold text-sm">No Scientific Skills Found</h3>
          <p className="text-slate-400 text-xs">
            Try searching for terms like "AlphaFold", "ChEMBL", "arXiv", "PubMed", or "Variant".
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {paginatedSkills.map((s) => (
            <div
              key={s.id}
              onClick={() => openSkillDetail(s)}
              className="group p-4 rounded-2xl bg-slate-900/70 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer flex flex-col justify-between space-y-3 shadow-md hover:shadow-xl hover:shadow-emerald-950/10"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded-full border bg-emerald-950/60 text-emerald-400 border-emerald-800/40">
                      {s.category}
                    </span>
                    <h3 className="font-bold text-white text-sm tracking-tight mt-1.5 group-hover:text-emerald-300 transition-colors">
                      {s.name}
                    </h3>
                  </div>

                  <div className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-emerald-400">
                    <BookOpen size={13} />
                  </div>
                </div>

                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed font-sans">
                  {s.description}
                </p>
              </div>

              <div className="pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span className="truncate max-w-[140px] opacity-75">{s.id}</span>
                <div className="flex items-center gap-1 text-emerald-400 group-hover:translate-x-0.5 transition-transform font-bold">
                  <span>View Protocols</span>
                  <ChevronRight size={13} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs">
          <span className="text-slate-400 font-mono">
            Showing {(page - 1) * pageSize + 1}–
            {Math.min(page * pageSize, skills.length)} of {skills.length} skills
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

      {/* Skill Modal */}
      <ScientificSkillModal
        skill={selectedSkill}
        onClose={() => setSelectedSkill(null)}
        onAttachToResearch={onAttachSkill}
      />
    </div>
  );
};
