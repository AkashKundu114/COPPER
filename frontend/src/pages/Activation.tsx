import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Key, ShieldCheck, Zap, AlertCircle, CheckCircle2 } from "lucide-react";
import axios from "axios";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

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

  const fetchFingerprint = async () => {
    try {
      const res = await axios.get("/api/activation/fingerprint");
      setFingerprint(res.data);
      setError(null);
    } catch {
      try {
        const fallback = await axios.get("http://127.0.0.1:8000/api/activation/fingerprint");
        setFingerprint(fallback.data);
        setError(null);
      } catch {
        setError("Backend is starting or unreachable on port 8000. Click 'Retry Detection' once online.");
      }
    }
  };

  useEffect(() => {
    fetchFingerprint();
  }, []);

  const handleActivateLocal = async () => {
    setLoading(true);
    setError(null);
    try {
      let res;
      try {
        res = await axios.post("/api/activation/activate/local");
      } catch {
        res = await axios.post("http://127.0.0.1:8000/api/activation/activate/local");
      }
      if (res.data.activated) {
        onActivated();
      } else {
        setError("Failed to verify local hardware requirements.");
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Local activation failed. Ensure backend is running.");
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
      let res;
      try {
        res = await axios.post("/api/activation/activate/owner-code", {
          code: ownerCode.trim(),
        });
      } catch {
        res = await axios.post("http://127.0.0.1:8000/api/activation/activate/owner-code", {
          code: ownerCode.trim(),
        });
      }
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-canvas text-text p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-xl surface-card rounded-2xl p-7 border border-border shadow-elevation-modal relative"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-copper-subtle text-copper rounded-xl border border-copper/20">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-text">C.O.P.P.E.R. Authorization</h1>
            <p className="text-xs text-text-secondary">Offline Sovereign Intelligence Hardware Gate</p>
          </div>
        </div>

        {error && (
          <div className="mb-5 p-3.5 bg-danger-dim border border-danger/30 rounded-xl flex items-center gap-2.5 text-danger text-xs">
            <AlertCircle size={16} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {mode === "choose" && (
          <div className="space-y-4">
            <p className="text-text-secondary text-xs mb-3">
              To operate COPPER offline with zero cloud telemetry, choose how you want to authorize this installation:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {/* Option A: Local GPU */}
              <button
                type="button"
                onClick={() => setMode("local")}
                className="group p-5 text-left rounded-xl border border-border-subtle bg-surface-base hover:border-copper/50 hover:bg-copper-subtle transition-all flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div className="p-2 w-fit bg-copper-subtle text-copper rounded-lg mb-3 group-hover:scale-105 transition-transform">
                    <Cpu size={20} />
                  </div>
                  <h3 className="font-semibold text-sm text-text mb-1">Use Host GPU</h3>
                  <p className="text-2xs text-text-secondary leading-relaxed">
                    Generate an offline hardware fingerprint and run locally on your graphics card.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1.5 text-2xs font-medium text-copper">
                  <span>Authorize Hardware</span> &rarr;
                </div>
              </button>

              {/* Option B: Owner Shared Code */}
              <button
                type="button"
                onClick={() => setMode("owner")}
                className="group p-5 text-left rounded-xl border border-border-subtle bg-surface-base hover:border-info/50 hover:bg-info-dim transition-all flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div className="p-2 w-fit bg-info-dim text-info rounded-lg mb-3 group-hover:scale-105 transition-transform">
                    <Key size={20} />
                  </div>
                  <h3 className="font-semibold text-sm text-text mb-1">Master Access Code</h3>
                  <p className="text-2xs text-text-secondary leading-relaxed">
                    Enter the access code provided by repository author (Akash) to unlock execution.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1.5 text-2xs font-medium text-info">
                  <span>Enter Code</span> &rarr;
                </div>
              </button>
            </div>
          </div>
        )}

        {mode === "local" && (
          <div className="space-y-5">
            <div className="p-4 rounded-xl bg-surface-base border border-border-subtle space-y-2.5">
              <div className="flex justify-between items-center">
                <h4 className="text-2xs font-semibold text-text-tertiary uppercase tracking-wider">
                  Detected Hardware Profile
                </h4>
                <button
                  type="button"
                  onClick={fetchFingerprint}
                  className="text-2xs text-copper hover:underline cursor-pointer font-medium"
                >
                  ↻ Refresh
                </button>
              </div>
              <div className="flex justify-between items-center text-xs py-1 border-b border-border-subtle">
                <span className="text-text-secondary">GPU Device</span>
                <span className="font-medium text-text">
                  {fingerprint?.gpu_name || "Detecting..."}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs py-1 border-b border-border-subtle">
                <span className="text-text-secondary">Total VRAM</span>
                <span className="font-medium text-text">
                  {fingerprint?.gpu_vram_mb ? `${fingerprint.gpu_vram_mb} MB` : "Shared / System"}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs py-1">
                <span className="text-text-secondary">Hardware Code</span>
                <Badge variant="copper">
                  {fingerprint?.activation_code || "COPPER-..."}
                </Badge>
              </div>
            </div>

            <div className="flex gap-2.5">
              <Button
                variant="secondary"
                size="md"
                onClick={() => setMode("choose")}
              >
                Back
              </Button>
              <Button
                variant="primary"
                size="md"
                className="flex-1"
                disabled={loading}
                onClick={handleActivateLocal}
              >
                {loading ? <Zap className="animate-spin mr-1" size={15} /> : <CheckCircle2 className="mr-1" size={15} />}
                Confirm & Activate Local Hardware
              </Button>
            </div>
          </div>
        )}

        {mode === "owner" && (
          <form onSubmit={handleActivateOwner} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-2xs font-semibold text-text-secondary uppercase tracking-wider block">
                Owner Access Code
              </label>
              <input
                type="text"
                placeholder="COPPER-XXXX-XXXX-XXXX"
                value={ownerCode}
                onChange={(e) => setOwnerCode(e.target.value.toUpperCase())}
                className="w-full bg-surface-base border border-border-subtle rounded-lg px-3 py-2.5 text-copper font-mono text-center tracking-widest text-base focus:outline-none focus:border-copper transition-colors uppercase placeholder:text-text-tertiary"
                required
              />
              <p className="text-2xs text-text-tertiary">
                Contact Akash Kundu to receive your authorized access code.
              </p>
            </div>

            <div className="flex gap-2.5">
              <Button
                variant="secondary"
                size="md"
                type="button"
                onClick={() => setMode("choose")}
              >
                Back
              </Button>
              <Button
                variant="primary"
                size="md"
                type="submit"
                className="flex-1"
                disabled={loading || !ownerCode.trim()}
              >
                {loading ? <Zap className="animate-spin mr-1" size={15} /> : <CheckCircle2 className="mr-1" size={15} />}
                Validate Code & Unlock
              </Button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  );
}
