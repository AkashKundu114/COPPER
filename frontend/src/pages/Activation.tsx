import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Key, ShieldCheck, Zap, AlertCircle, CheckCircle2 } from "lucide-react";
import axios from "axios";

interface ActivationProps {
  onActivated: () => void;
}

export function Activation({ onActivated }: ActivationProps) {
  const [mode, setMode] = useState<"choose" | "local" | "owner">("choose");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ownerCode, setOwnerCode] = useState("");
  const [fingerprint, setFingerprint] = useState<{
    gpu_name: string;
    gpu_vram_mb: number;
    activation_code: string;
  } | null>(null);

  useEffect(() => {
    axios
      .get("/api/activation/fingerprint")
      .then((res) => setFingerprint(res.data))
      .catch(() => {});
  }, []);

  const handleActivateLocal = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post("/api/activation/activate/local");
      if (res.data.activated) {
        onActivated();
      } else {
        setError("Failed to verify local hardware requirements.");
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Local activation failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleActivateOwner = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ownerCode.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post("/api/activation/activate/owner-code", {
        code: ownerCode.trim(),
      });
      if (res.data.activated) {
        onActivated();
      } else {
        setError("Invalid activation code.");
      }
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || "Invalid activation code. Please check with Akash for access."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/95 text-slate-100 p-6 backdrop-blur-xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-orange-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-amber-500/20 text-amber-400 rounded-2xl border border-amber-500/30">
            <ShieldCheck size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">C.O.P.P.E.R. Authorization</h1>
            <p className="text-sm text-slate-400">Offline Sovereign Intelligence Hardware Gate</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-950/50 border border-red-800/80 rounded-2xl flex items-center gap-3 text-red-200 text-sm">
            <AlertCircle size={20} className="text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {mode === "choose" && (
          <div className="space-y-4">
            <p className="text-slate-300 text-sm mb-4">
              To operate COPPER offline with zero cloud telemetry, please choose how you would like to
              authorize this installation:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Option A: Local GPU */}
              <button
                type="button"
                onClick={() => setMode("local")}
                className="group p-6 text-left rounded-2xl border border-slate-800 bg-slate-950/60 hover:border-amber-500/50 hover:bg-amber-950/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="p-3 w-fit bg-amber-500/10 text-amber-400 rounded-xl mb-4 group-hover:scale-105 transition-transform">
                    <Cpu size={24} />
                  </div>
                  <h3 className="font-semibold text-base text-slate-100 mb-1">Use My System GPU</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Automatically generate a hardware fingerprint and run locally on your host graphics card.
                  </p>
                </div>
                <div className="mt-6 flex items-center gap-2 text-xs font-medium text-amber-400">
                  <span>Authorize Hardware</span> &rarr;
                </div>
              </button>

              {/* Option B: Owner Shared Code */}
              <button
                type="button"
                onClick={() => setMode("owner")}
                className="group p-6 text-left rounded-2xl border border-slate-800 bg-slate-950/60 hover:border-cyan-500/50 hover:bg-cyan-950/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="p-3 w-fit bg-cyan-500/10 text-cyan-400 rounded-xl mb-4 group-hover:scale-105 transition-transform">
                    <Key size={24} />
                  </div>
                  <h3 className="font-semibold text-base text-slate-100 mb-1">Enter Master Access Code</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Enter the access code provided by the repository owner (Akash) to unlock runtime execution.
                  </p>
                </div>
                <div className="mt-6 flex items-center gap-2 text-xs font-medium text-cyan-400">
                  <span>Enter Code</span> &rarr;
                </div>
              </button>
            </div>
          </div>
        )}

        {mode === "local" && (
          <div className="space-y-6">
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Detected Hardware Profile
              </h4>
              <div className="flex justify-between items-center text-sm py-1 border-b border-slate-800/60">
                <span className="text-slate-400">GPU Device</span>
                <span className="font-medium text-slate-200">
                  {fingerprint?.gpu_name || "Detecting..."}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Total VRAM</span>
                <span className="font-medium text-slate-200">
                  {fingerprint?.gpu_vram_mb ? `${fingerprint.gpu_vram_mb} MB` : "Shared / System"}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm py-1">
                <span className="text-slate-400">Hardware Code</span>
                <span className="font-mono text-xs text-amber-400 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-800/50">
                  {fingerprint?.activation_code || "COPPER-..."}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setMode("choose")}
                className="px-5 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-sm font-medium"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleActivateLocal}
                disabled={loading}
                className="flex-1 px-5 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm transition-colors flex items-center justify-center gap-2"
              >
                {loading ? <Zap className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}
                Confirm & Activate Local Hardware
              </button>
            </div>
          </div>
        )}

        {mode === "owner" && (
          <form onSubmit={handleActivateOwner} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Owner Access Code
              </label>
              <input
                type="text"
                placeholder="COPPER-XXXX-XXXX-XXXX"
                value={ownerCode}
                onChange={(e) => setOwnerCode(e.target.value.toUpperCase())}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-cyan-400 font-mono text-center tracking-widest text-lg focus:outline-none focus:border-cyan-500 transition-colors uppercase placeholder:text-slate-700"
                required
              />
              <p className="text-xs text-slate-500">
                Contact Akash Kundu to receive your authorized access code.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setMode("choose")}
                className="px-5 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-sm font-medium"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading || !ownerCode.trim()}
                className="flex-1 px-5 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? <Zap className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}
                Validate Code & Unlock
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  );
}
