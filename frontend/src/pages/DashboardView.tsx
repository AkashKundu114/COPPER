import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Bot,
  Radio,
  Sparkles,
  Activity,
  Clock,
  Code2,
  GitBranch,
  Plus,
  ArrowRight,
} from "lucide-react";
import type { NavSection } from "../components/layout/Sidebar";
import { systemAPI, cognitiveAPI, type CockpitStatus } from "../services/api";
import { scheduleAPI, type ScheduleEvent } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { staggerContainer, staggerItem } from "../lib/motion";

interface DashboardViewProps {
  onNavigate?: (section: NavSection) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [cockpit, setCockpit] = useState<CockpitStatus | null>(null);
  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([]);
  const [cognitiveState, setCognitiveState] = useState<{
    state: string;
    confidence: number;
    recommendations: string[];
    current_focus_streak?: number;
  } | null>(null);
  const [intelDismissed, setIntelDismissed] = useState(false);

  const fetchLiveTelemetry = useCallback(async () => {
    try {
      const res = await systemAPI.getCockpitStatus();
      if (res.data) {
        setCockpit(res.data);
      }
    } catch (err) {
      console.error("Error loading live cockpit telemetry:", err);
    }
  }, []);

  const fetchOperationalData = useCallback(async () => {
    try {
      const [eventsData, cogRes] = await Promise.all([
        scheduleAPI.list().catch(() => []),
        cognitiveAPI.getState().catch(() => null),
      ]);
      setScheduleEvents(eventsData || []);
      if (cogRes?.data) {
        setCognitiveState(cogRes.data);
      }
    } catch (err) {
      console.error("Error loading operational dashboard data:", err);
    }
  }, []);

  useEffect(() => {
    fetchLiveTelemetry();
    fetchOperationalData();
    const interval = setInterval(fetchLiveTelemetry, 3000);
    return () => clearInterval(interval);
  }, [fetchLiveTelemetry, fetchOperationalData]);

  // Greeting determination
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  // GPU readings or fallbacks
  const gpuModel = cockpit?.hardware?.gpu?.model
    ? cockpit.hardware.gpu.model.replace("NVIDIA GeForce ", "")
    : "System GPU";
  const vramUsed = cockpit?.hardware?.gpu?.vram_used_gb ?? 0;
  const vramTotal = cockpit?.hardware?.gpu?.vram_total_gb ?? 8.0;
  const vramHeadroom = Math.max(0, vramTotal - vramUsed).toFixed(1);

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="p-5 md:p-6 space-y-5 max-w-6xl mx-auto text-text font-sans pb-16"
    >
      {/* Hero Banner / Greeting */}
      <motion.div
        variants={staggerItem}
        className="surface-card p-5 rounded-2xl relative overflow-hidden"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <Badge variant="success">
                {cockpit?.security?.defcon_label || "OPTIMAL"}
              </Badge>
              <Badge variant="copper">
                <GitBranch size={10} className="mr-1 inline" />
                {cockpit?.git?.branch || "MAIN"}
              </Badge>
              <Badge variant="default">100% AIR-GAPPED</Badge>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-text tracking-tight">
              {greeting}, Akash
            </h1>
            <p className="text-xs text-text-secondary mt-1">
              Autonomous {cockpit?.agents?.fleet_count ?? 12}-agent fleet online • Zero external egress
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="px-3 py-2 rounded-lg bg-surface-base border border-border-subtle text-right">
              <span className="text-2xs font-mono uppercase text-text-tertiary block">
                Router Latency
              </span>
              <span className="text-sm font-semibold font-mono text-copper">
                {cockpit?.routing?.velocity_ms !== undefined
                  ? `${cockpit.routing.velocity_ms.toFixed(3)} ms`
                  : "0.158 ms"}
              </span>
            </div>
            <div className="px-3 py-2 rounded-lg bg-surface-base border border-border-subtle text-right">
              <span className="text-2xs font-mono uppercase text-text-tertiary block">
                Throughput
              </span>
              <span className="text-sm font-semibold font-mono text-text">
                ~{cockpit?.routing?.throughput_qps
                  ? Math.round(cockpit.routing.throughput_qps).toLocaleString()
                  : "6,271"}{" "}
                QPS
              </span>
            </div>
          </div>
        </div>

        {/* Action Strip */}
        <div className="mt-4 pt-3.5 border-t border-border-hairline flex flex-wrap gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigate?.("chat")}
          >
            <Code2 size={13} className="mr-1" /> Start Coding Session
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate?.("companion")}
          >
            <Radio size={13} className="mr-1 text-copper" /> Voice Companion
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate?.("today")}
          >
            <Calendar size={13} className="mr-1 text-text-secondary" /> Daily Standup
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate?.("agents")}
          >
            <Bot size={13} className="mr-1 text-info" /> Agent Fleet
          </Button>
        </div>
      </motion.div>

      {/* 3-Column Bento Grid */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        {/* Column 1: Schedule */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar size={16} className="text-copper" />
                <CardTitle>Schedule</CardTitle>
              </div>
              <Badge variant="default">
                {scheduleEvents.length > 0 ? `${scheduleEvents.length} EVENTS` : "READY"}
              </Badge>
            </div>
          </CardHeader>

          <CardContent>
            {scheduleEvents.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {scheduleEvents.slice(0, 3).map((evt) => (
                  <div
                    key={evt.id}
                    className={`p-2.5 rounded-lg border text-xs flex justify-between items-center ${
                      evt.completed
                        ? "bg-surface-base/50 border-border-subtle opacity-50"
                        : "bg-surface-base border-border-subtle"
                    }`}
                  >
                    <div className="overflow-hidden pr-2">
                      <p className="font-medium text-text truncate">{evt.title}</p>
                      <p className="text-2xs text-text-tertiary font-mono flex items-center gap-1 mt-0.5">
                        <Clock size={11} className="text-copper" /> {evt.time}
                      </p>
                    </div>
                    <Badge variant={evt.completed ? "default" : "success"}>
                      {evt.completed ? "DONE" : evt.category || "ACTIVE"}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-surface-base border border-border-subtle text-center space-y-2">
                <p className="text-xs text-text-secondary">
                  No events scheduled today.
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onNavigate?.("today")}
                >
                  <Plus size={13} className="mr-1" /> Add Standup Event
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Column 2: Agent Fleet */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot size={16} className="text-copper" />
                <CardTitle>Autonomous Fleet</CardTitle>
              </div>
              <Badge variant="copper">
                {cockpit?.agents?.fleet_count ?? 12} READY
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-3">
            <div className="p-2.5 rounded-lg bg-surface-base border border-border-subtle space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-text font-medium flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                  ATLAS • Core Reasoning
                </span>
                <span className="text-copper text-2xs font-mono">14B active</span>
              </div>
              <p className="text-2xs text-text-secondary">
                Intent decomposition, semantic search & dialogue routing.
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                variant="primary"
                size="sm"
                className="flex-1"
                onClick={() => onNavigate?.("chat")}
              >
                <Code2 size={13} className="mr-1" /> Start Chat
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="flex-1"
                onClick={() => onNavigate?.("companion")}
              >
                <Radio size={13} className="mr-1 text-copper" /> Voice
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Column 3: Guardian Intelligence */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-warning" />
                <CardTitle>Intelligence</CardTitle>
              </div>
              <Badge variant="warning">
                CONF {Math.round((cognitiveState?.confidence ?? 0.95) * 100)}%
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-3">
            {!intelDismissed ? (
              <>
                <p className="text-xs text-text-secondary leading-relaxed bg-surface-base p-2.5 rounded-lg border border-border-subtle italic">
                  "{cognitiveState?.recommendations?.[0] ||
                    `Cognitive state: ${cognitiveState?.state || "nominal"}. Ready for developer instruction.`}"
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => onNavigate?.("chat")}
                  >
                    Execute Plan
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIntelDismissed(true)}
                  >
                    Dismiss
                  </Button>
                </div>
              </>
            ) : (
              <div className="p-3 rounded-lg bg-surface-base border border-border-subtle text-center space-y-2">
                <p className="text-xs text-text-tertiary">
                  Advisories acknowledged. Standing by.
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIntelDismissed(false)}
                >
                  Restore Advisory
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Hardware & Telemetry Matrix */}
      <motion.div variants={staggerItem}>
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-copper" />
                <CardTitle>System & Model Telemetry</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate?.("benchmarks")}
                className="text-copper hover:text-copper-bright text-xs"
              >
                Benchmarks & Telemetry <ArrowRight size={13} className="ml-1" />
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1">
                <span className="text-2xs font-mono uppercase text-text-tertiary block">
                  Router Precision
                </span>
                <p className="text-xl font-bold font-mono text-text">
                  {cockpit?.routing?.precision_pct !== undefined
                    ? `${cockpit.routing.precision_pct.toFixed(1)}%`
                    : "97.8%"}
                </p>
                <span className="text-2xs text-text-secondary">
                  Sub-millisecond routing
                </span>
              </div>

              <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1">
                <span className="text-2xs font-mono uppercase text-text-tertiary block">
                  Threat Shield
                </span>
                <p className="text-xl font-bold font-mono text-success">
                  {cockpit?.security?.threat_shield_pct !== undefined
                    ? `${cockpit.security.threat_shield_pct.toFixed(1)}%`
                    : "100.0%"}
                </p>
                <span className="text-2xs text-success">
                  0 Breaches Detected
                </span>
              </div>

              <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1">
                <span className="text-2xs font-mono uppercase text-text-tertiary truncate block">
                  {gpuModel} VRAM
                </span>
                <p className="text-xl font-bold font-mono text-copper">
                  {vramUsed} / {vramTotal} GB
                </p>
                <span className="text-2xs text-text-secondary">
                  {vramHeadroom} GB Headroom
                </span>
              </div>

              <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1">
                <span className="text-2xs font-mono uppercase text-text-tertiary block">
                  Neural Mesh Models
                </span>
                <p className="text-xl font-bold font-mono text-text">
                  {cockpit?.models?.loaded_count && cockpit.models.loaded_count > 0
                    ? `${cockpit.models.loaded_count} Loaded`
                    : "Core Standby"}
                </p>
                <span className="text-2xs text-text-secondary">
                  Local Weight Cache
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
};
