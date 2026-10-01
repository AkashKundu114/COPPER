import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  DollarSign,
  TrendingUp,
  Percent,
  MousePointerClick,
  Activity,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  RefreshCw,
  BarChart3,
  Sliders,
  Radio,
  Zap,
} from "lucide-react";
import { campaignAPI } from "../services/api";
import { CampaignChart } from "./CampaignChart";
import { AnomalyAlerts } from "./AnomalyAlerts";
import { BudgetOptimizer } from "./BudgetOptimizer";

export const CampaignDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [campaignMetrics, setCampaignMetrics] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [optimization, setOptimization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview"); // "overview" | "chart" | "alerts" | "optimizer"
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const res = await campaignAPI.getDashboard();
      if (res.data) {
        setDashboardData(res.data);
        const cmps = res.data.campaigns || [];
        setCampaigns(cmps);
        setAnomalies(res.data.active_anomalies || []);
        setOptimization(res.data.budget_optimization || null);

        if (!selectedCampaign && cmps.length > 0) {
          setSelectedCampaign(cmps[0]);
        }
      }
    } catch (err) {
      console.error("Failed to load campaign dashboard:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCampaign]);

  const fetchMetricsForSelected = useCallback(async (campaignId) => {
    try {
      const res = await campaignAPI.getMetrics(campaignId, 168);
      if (res.data) {
        setCampaignMetrics(res.data);
      }
    } catch (err) {
      console.error(`Failed to fetch metrics for ${campaignId}:`, err);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  useEffect(() => {
    if (selectedCampaign?.campaign_id) {
      fetchMetricsForSelected(selectedCampaign.campaign_id);
    }
  }, [selectedCampaign, fetchMetricsForSelected]);

  // Connect to live WebSocket for ad-tech anomaly alerts
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname || "localhost";
    const port = window.location.port === "5173" ? "8000" : window.location.port || "8000";
    const wsUrl = `${protocol}//${host}:${port}/ws/campaign-alerts`;

    let ws;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          if (payload.type === "campaign_alerts_snapshot" && Array.isArray(payload.anomalies)) {
            setAnomalies(payload.anomalies);
          }
        } catch (e) {
          console.debug("WS parse error:", e);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
      };

      ws.onerror = () => {
        setWsConnected(false);
      };
    } catch (err) {
      console.debug("WS connect error:", err);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const handleRecalculateBudget = async (budgetAmount) => {
    try {
      const res = await campaignAPI.optimizeBudget(budgetAmount);
      if (res.data) {
        setOptimization(res.data);
      }
    } catch (e) {
      console.error("Budget recalibration failed:", e);
    }
  };

  const summary = dashboardData?.summary || {
    total_spend: 0,
    total_conversions: 0,
    overall_roas: 0,
    avg_ctr: 0,
  };

  const getStatusBadge = (status) => {
    if (status === "critical") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
          <ShieldAlert className="w-3 h-3" /> Critical
        </span>
      );
    }
    if (status === "warning") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3 h-3" /> Warning
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
        <CheckCircle2 className="w-3 h-3" /> Healthy
      </span>
    );
  };

  return (
    <div className="w-full h-full flex flex-col p-6 overflow-y-auto bg-canvas text-text gap-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 text-white shadow-md shadow-cyan-950/40">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                Campaign Intelligence Agent
                <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                  DELTA (DeltaX-Grade)
                </span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Simulated real-time advertising telemetry, statistical anomaly detection, and ML budget optimization
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* WebSocket Status Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-elevated border border-border-subtle text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                wsConnected ? "bg-emerald-400 animate-pulse" : "bg-surface-active"
              }`}
            />
            <span className="text-text-secondary font-mono">
              {wsConnected ? "STREAM ONLINE" : "REST SYNC"}
            </span>
          </div>

          <button
            onClick={fetchDashboard}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-active hover:bg-surface-spotlight border border-border-highlight text-xs font-medium text-text transition-all shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 4 Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Spend */}
        <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 shadow-md backdrop-blur-md">
          <div className="flex items-center justify-between text-text-secondary text-xs font-medium">
            <span>Daily Spend Run-Rate</span>
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-1 font-mono">
            <span className="text-2xl font-bold text-text">
              ${summary.total_spend ? Number(summary.total_spend).toLocaleString() : "0"}
            </span>
            <span className="text-xs text-text-tertiary">/day</span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1 block">
            Across 5 active simulated ad campaigns
          </span>
        </div>

        {/* Total Conversions */}
        <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 shadow-md backdrop-blur-md">
          <div className="flex items-center justify-between text-text-secondary text-xs font-medium">
            <span>Projected Conversions</span>
            <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400">
              <MousePointerClick className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-1 font-mono">
            <span className="text-2xl font-bold text-purple-300">
              {summary.total_conversions ? Number(summary.total_conversions).toLocaleString() : "0"}
            </span>
            <span className="text-xs text-text-tertiary">orders</span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1 block">
            Derived from hourly click x CVR telemetry
          </span>
        </div>

        {/* Avg CTR */}
        <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 shadow-md backdrop-blur-md">
          <div className="flex items-center justify-between text-text-secondary text-xs font-medium">
            <span>Blended CTR</span>
            <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
              <Percent className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-1 font-mono">
            <span className="text-2xl font-bold text-sky-300">
              {(Number(summary.avg_ctr || 0) * 100).toFixed(2)}%
            </span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1 block">
            Target benchmark: &gt; 1.5% brand / &gt; 3.5% perf
          </span>
        </div>

        {/* Overall ROAS */}
        <div className="bg-surface-elevated border border-border-subtle rounded-xl p-4 shadow-md backdrop-blur-md">
          <div className="flex items-center justify-between text-text-secondary text-xs font-medium">
            <span>Portfolio ROAS</span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-1 font-mono">
            <span className="text-2xl font-bold text-emerald-400">
              {Number(summary.overall_roas || 0).toFixed(2)}x
            </span>
          </div>
          <span className="text-[11px] text-text-tertiary mt-1 block">
            Blended revenue/spend conversion return
          </span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-border-subtle pb-2">
        {[
          { id: "overview", label: "Overview & Campaigns", icon: BarChart3 },
          { id: "chart", label: "Trajectory & Anomalies", icon: Activity },
          { id: "alerts", label: `Anomaly Alerts (${anomalies.length})`, icon: Zap },
          { id: "optimizer", label: "Budget Optimizer (ML)", icon: Sliders },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? "bg-surface-active text-white border border-border-highlight shadow-sm"
                  : "text-text-secondary hover:text-text hover:bg-surface-elevated/50"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-cyan-400" : ""}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Campaign Table */}
      {activeTab === "overview" && (
        <div className="flex flex-col gap-6">
          {/* Campaign Table */}
          <div className="bg-surface-elevated border border-border-subtle rounded-xl overflow-hidden shadow-lg backdrop-blur-md">
            <div className="p-4 border-b border-border-subtle flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-text">
                  Active Advertising Campaigns ({campaigns.length})
                </h3>
                <p className="text-xs text-text-secondary">
                  Click any row to inspect historical metrics and anomaly timeline
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-base text-text-secondary uppercase font-mono text-[11px] border-b border-border-subtle">
                  <tr>
                    <th className="py-3 px-4">Campaign Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4 text-right">Daily Budget</th>
                    <th className="py-3 px-4 text-right">Hourly Spend</th>
                    <th className="py-3 px-4 text-right">Clicks</th>
                    <th className="py-3 px-4 text-right">CTR</th>
                    <th className="py-3 px-4 text-right">ROAS</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {campaigns.map((c) => {
                    const isSelected = selectedCampaign?.campaign_id === c.campaign_id;
                    return (
                      <tr
                        key={c.campaign_id}
                        onClick={() => setSelectedCampaign(c)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-surface-active text-white"
                            : "hover:bg-surface-elevated/60 text-text-secondary"
                        }`}
                      >
                        <td className="py-3 px-4 font-semibold text-text flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              isSelected ? "bg-cyan-400 animate-ping" : "bg-surface-spotlight"
                            }`}
                          />
                          {c.campaign_name}
                        </td>
                        <td className="py-3 px-4">
                          <span className="capitalize font-mono text-[11px] px-2 py-0.5 rounded bg-surface-active text-text-secondary border border-border-highlight">
                            {c.campaign_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-text-secondary">
                          ${Number(c.daily_budget || 0).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-text-secondary">
                          ${Number(c.spend || 0).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-text-secondary">
                          {Number(c.clicks || 0).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-semibold text-sky-400">
                          {(Number(c.ctr || 0) * 100).toFixed(2)}%
                        </td>
                        <td
                          className={`py-3 px-4 text-right font-mono font-semibold ${
                            Number(c.roas) >= 2.0
                              ? "text-emerald-400"
                              : Number(c.roas) >= 1.0
                              ? "text-amber-400"
                              : "text-red-400"
                          }`}
                        >
                          {Number(c.roas || 0).toFixed(2)}x
                        </td>
                        <td className="py-3 px-4 text-center">
                          {getStatusBadge(c.status || "healthy")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Quick Chart Preview */}
          <CampaignChart
            campaign={selectedCampaign}
            metrics={campaignMetrics}
            anomalies={anomalies}
          />
        </div>
      )}

      {/* Tab 2: Trajectory & Anomaly Chart */}
      {activeTab === "chart" && (
        <CampaignChart
          campaign={selectedCampaign}
          metrics={campaignMetrics}
          anomalies={anomalies}
        />
      )}

      {/* Tab 3: Live Anomaly Alerts Feed */}
      {activeTab === "alerts" && (
        <AnomalyAlerts
          anomalies={anomalies}
          onAutoFixApplied={(anom) => {
            fetchDashboard();
          }}
        />
      )}

      {/* Tab 4: Autonomous Budget Optimizer */}
      {activeTab === "optimizer" && (
        <BudgetOptimizer
          optimizationData={optimization}
          campaigns={campaigns}
          onRecalculate={handleRecalculateBudget}
          onApplyOptimization={() => {
            fetchDashboard();
          }}
        />
      )}
    </div>
  );
};

export default CampaignDashboard;
