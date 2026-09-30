import React, { useMemo, useState } from "react";
import * as d3 from "d3";
import { TrendingUp, DollarSign, MousePointerClick, Percent } from "lucide-react";

export const CampaignChart = ({ campaign, metrics = [], anomalies = [] }) => {
  const [selectedMetric, setSelectedMetric] = useState("ctr");

  const metricConfigs = {
    ctr: {
      label: "Click-Through Rate (CTR)",
      format: (v) => `${(v * 100).toFixed(2)}%`,
      color: "#38bdf8", // Sky blue
      icon: Percent,
    },
    roas: {
      label: "Return on Ad Spend (ROAS)",
      format: (v) => `${v.toFixed(2)}x`,
      color: "#34d399", // Emerald
      icon: TrendingUp,
    },
    spend: {
      label: "Hourly Spend ($)",
      format: (v) => `$${v.toFixed(2)}`,
      color: "#f59e0b", // Amber
      icon: DollarSign,
    },
    conversions: {
      label: "Conversions",
      format: (v) => `${Math.round(v)}`,
      color: "#a855f7", // Purple
      icon: MousePointerClick,
    },
  };

  const chartData = useMemo(() => {
    if (!metrics || metrics.length === 0) return [];
    return metrics.map((m) => ({
      date: new Date(m.timestamp || Date.now()),
      value: Number(m[selectedMetric] || 0),
      raw: m,
    }));
  }, [metrics, selectedMetric]);

  const { svgContent, hasData } = useMemo(() => {
    if (!chartData || chartData.length === 0) {
      return { svgContent: null, hasData: false };
    }

    const width = 760;
    const height = 280;
    const margin = { top: 20, right: 30, bottom: 35, left: 55 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const xExtent = d3.extent(chartData, (d) => d.date);
    const yMax = d3.max(chartData, (d) => d.value) || 1;
    const yMin = Math.min(0, d3.min(chartData, (d) => d.value) || 0);

    const xScale = d3.scaleTime().domain(xExtent).range([0, innerWidth]);
    const yScale = d3.scaleLinear().domain([yMin, yMax * 1.15]).range([innerHeight, 0]).nice();

    const lineGenerator = d3
      .line()
      .x((d) => xScale(d.date))
      .y((d) => yScale(d.value))
      .curve(d3.curveMonotoneX);

    const areaGenerator = d3
      .area()
      .x((d) => xScale(d.date))
      .y0(innerHeight)
      .y1((d) => yScale(d.value))
      .curve(d3.curveMonotoneX);

    const pathData = lineGenerator(chartData) || "";
    const areaData = areaGenerator(chartData) || "";

    const xTicks = xScale.ticks(6).map((d) => ({
      x: xScale(d),
      label: d3.timeFormat("%b %d, %H:%M")(d),
    }));

    const yTicks = yScale.ticks(5).map((v) => ({
      y: yScale(v),
      label: metricConfigs[selectedMetric].format(v),
    }));

    // Find anomalies related to this campaign to render shaded warning zones
    const relevantAnomalies = anomalies.filter(
      (a) => a.campaign_id === campaign?.campaign_id
    );

    return {
      svgContent: {
        width,
        height,
        margin,
        innerWidth,
        innerHeight,
        pathData,
        areaData,
        xTicks,
        yTicks,
        xScale,
        yScale,
        relevantAnomalies,
      },
      hasData: true,
    };
  }, [chartData, selectedMetric, anomalies, campaign]);

  const activeConfig = metricConfigs[selectedMetric];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur-md shadow-lg flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            Performance Trajectory: {campaign?.campaign_name || "All Campaigns"}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Hourly telemetry with DeltaX anomaly detection thresholds
          </p>
        </div>

        {/* Metric Selector Buttons */}
        <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-lg border border-slate-800">
          {Object.entries(metricConfigs).map(([key, cfg]) => {
            const Icon = cfg.icon;
            const isSelected = selectedMetric === key;
            return (
              <button
                key={key}
                onClick={() => setSelectedMetric(key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-slate-800 text-white shadow-sm border border-slate-700"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                <Icon className="w-3.5 h-3.5" style={{ color: cfg.color }} />
                <span>{key.toUpperCase()}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Chart Area */}
      {!hasData ? (
        <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
          No metrics available for {campaign?.campaign_name || "selected campaign"}.
        </div>
      ) : (
        <div className="relative w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${svgContent.width} ${svgContent.height}`}
            className="w-full h-auto min-w-[600px] select-none"
          >
            <defs>
              <linearGradient id={`gradient-${selectedMetric}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={activeConfig.color} stopOpacity="0.35" />
                <stop offset="100%" stopColor={activeConfig.color} stopOpacity="0.0" />
              </linearGradient>
            </defs>

            <g transform={`translate(${svgContent.margin.left}, ${svgContent.margin.top})`}>
              {/* Horizontal Grid lines */}
              {svgContent.yTicks.map((tick, i) => (
                <g key={`y-grid-${i}`} transform={`translate(0, ${tick.y})`}>
                  <line
                    x1={0}
                    x2={svgContent.innerWidth}
                    stroke="#1e293b"
                    strokeDasharray="3 3"
                    strokeWidth="1"
                  />
                  <text
                    x={-10}
                    y={3}
                    textAnchor="end"
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    {tick.label}
                  </text>
                </g>
              ))}

              {/* Shaded Red Zone for Detected Anomalies */}
              {svgContent.relevantAnomalies.map((anom, idx) => {
                const anomTime = new Date(anom.detected_at);
                const xPos = svgContent.xScale(anomTime);
                if (xPos >= 0 && xPos <= svgContent.innerWidth) {
                  return (
                    <g key={`anom-zone-${idx}`}>
                      <rect
                        x={Math.max(0, xPos - 25)}
                        y={0}
                        width={50}
                        height={svgContent.innerHeight}
                        fill="#ef4444"
                        fillOpacity="0.18"
                        rx="4"
                      />
                      <line
                        x1={xPos}
                        y1={0}
                        x2={xPos}
                        y2={svgContent.innerHeight}
                        stroke="#ef4444"
                        strokeWidth="1.5"
                        strokeDasharray="4 2"
                      />
                      <circle cx={xPos} cy={14} r="4" fill="#ef4444" />
                      <text
                        x={xPos}
                        y={32}
                        textAnchor="middle"
                        fill="#fca5a5"
                        fontSize="9"
                        fontWeight="600"
                      >
                        ANOMALY
                      </text>
                    </g>
                  );
                }
                return null;
              })}

              {/* Area fill */}
              <path d={svgContent.areaData} fill={`url(#gradient-${selectedMetric})`} />

              {/* Data curve line */}
              <path
                d={svgContent.pathData}
                fill="none"
                stroke={activeConfig.color}
                strokeWidth="2.5"
                strokeLinecap="round"
              />

              {/* X Axis Ticks */}
              {svgContent.xTicks.map((tick, i) => (
                <g key={`x-tick-${i}`} transform={`translate(${tick.x}, ${svgContent.innerHeight})`}>
                  <line y1={0} y2={6} stroke="#334155" />
                  <text
                    y={18}
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    {tick.label}
                  </text>
                </g>
              ))}
            </g>
          </svg>
        </div>
      )}

      {/* Legend & Anomaly Notice */}
      <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-1">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span
              className="w-3 h-0.5 rounded-full"
              style={{ backgroundColor: activeConfig.color }}
            ></span>
            {activeConfig.label}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-red-500/20 border border-red-500/40"></span>
            Anomaly Region (|Z| &gt; 2.0 or Burn Alert)
          </span>
        </div>
        <span className="text-slate-500">Trailing 7 days • 168 hourly snapshots</span>
      </div>
    </div>
  );
};
