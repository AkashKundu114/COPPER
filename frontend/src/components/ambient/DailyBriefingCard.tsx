import React, { useState, useEffect } from 'react';
import { briefingAPI, predictionsAPI, contextSwitchAPI } from '../../services/api';
import { Sun, Moon, Sparkles, Activity, CheckCircle, Clock, Calendar, Zap, RefreshCw } from 'lucide-react';

export const DailyBriefingCard: React.FC = () => {
  const [mode, setMode] = useState<'morning' | 'eod'>('morning');
  const [briefing, setBriefing] = useState<any>(null);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [activeProject, setActiveProject] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);

  useEffect(() => {
    fetchData();
  }, [mode]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [briefingRes, predictionsRes, contextRes] = await Promise.all([
        mode === 'morning' ? briefingAPI.getMorning() : briefingAPI.getEod(),
        predictionsAPI.getToday(),
        contextSwitchAPI.getCurrent()
      ]);
      setBriefing(briefingRes.data);
      setPredictions(predictionsRes.data?.predictions || []);
      setActiveProject(contextRes.data);
    } catch (error) {
      console.error('Error fetching briefing data', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      if (mode === 'morning') {
        await briefingAPI.generateMorning();
      } else {
        await briefingAPI.generateEod();
      }
      await fetchData();
    } catch (error) {
      console.error('Error generating briefing', error);
    } finally {
      setGenerating(false);
    }
  };

  const note = briefing?.synthesis || briefing?.note || "Awaiting AI synthesis. Generate to initialize your briefing.";
  const metrics = briefing?.metrics || {
    scheduleEvents: 0,
    overdueTasks: 0,
    completedToday: 0,
    activeProjects: 0
  };

  return (
    <div className="flex flex-col bg-slate-900/90 border border-slate-800 rounded-lg p-4 font-mono text-xs w-full max-w-2xl gap-4">
      {/* Header & Toggles */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-accent-400" />
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">
            Daily Briefing
          </h2>
          {activeProject?.project_name && (
            <span className="ml-2 px-2 py-0.5 bg-slate-800 border border-slate-700 text-cyber-cyan rounded-full text-[10px] uppercase">
              ACTV: {activeProject.project_name}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode('morning')}
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              mode === 'morning' ? 'bg-slate-800 text-accent-400' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Sun className="w-3 h-3" />
            <span>MRNG</span>
          </button>
          <button
            onClick={() => setMode('eod')}
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              mode === 'eod' ? 'bg-slate-800 text-verdigris' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Moon className="w-3 h-3" />
            <span>EOD</span>
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="ml-2 p-1 text-slate-500 hover:text-cyber-cyan transition-colors disabled:opacity-50"
            title="Generate Briefing"
          >
            <RefreshCw className={`w-3 h-3 ${generating ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Synthesis Card */}
      <div className="bg-slate-950/50 border border-slate-800/50 p-3 rounded-md">
        <h3 className="text-slate-500 mb-1 flex items-center gap-1 uppercase tracking-wider text-[10px]">
          <Activity className="w-3 h-3" />
          Executive Synthesis
        </h3>
        {loading && !generating ? (
          <div className="text-slate-600 animate-pulse">Decrypting neural pathways...</div>
        ) : (
          <p className="text-slate-300 leading-relaxed">
            {note}
          </p>
        )}
      </div>

      {/* Metrics Pills */}
      <div className="grid grid-cols-4 gap-2">
        <div className="bg-slate-900 border border-slate-800 p-2 rounded flex flex-col items-center justify-center">
          <Calendar className="w-4 h-4 text-cyber-cyan mb-1" />
          <span className="text-slate-200 text-lg">{metrics.scheduleEvents}</span>
          <span className="text-slate-500 text-[10px] uppercase text-center mt-1">Events</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2 rounded flex flex-col items-center justify-center">
          <Clock className="w-4 h-4 text-red-400 mb-1" />
          <span className="text-slate-200 text-lg">{metrics.overdueTasks}</span>
          <span className="text-slate-500 text-[10px] uppercase text-center mt-1">Due/Overdue</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2 rounded flex flex-col items-center justify-center">
          <CheckCircle className="w-4 h-4 text-verdigris mb-1" />
          <span className="text-slate-200 text-lg">{metrics.completedToday}</span>
          <span className="text-slate-500 text-[10px] uppercase text-center mt-1">Completed</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2 rounded flex flex-col items-center justify-center">
          <Zap className="w-4 h-4 text-accent-400 mb-1" />
          <span className="text-slate-200 text-lg">{metrics.activeProjects}</span>
          <span className="text-slate-500 text-[10px] uppercase text-center mt-1">Active Proj</span>
        </div>
      </div>

      {/* Anticipation Strip */}
      {predictions.length > 0 && (
        <div className="mt-2 border-t border-slate-800 pt-3">
          <h3 className="text-slate-500 mb-2 uppercase tracking-wider text-[10px] flex items-center gap-1">
            <Zap className="w-3 h-3 text-accent-400" />
            Anticipated Vectors
          </h3>
          <div className="flex flex-col gap-1.5">
            {predictions.map((pred, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-800/30 px-2 py-1.5 rounded">
                <span className="text-slate-300 truncate pr-2">{pred.task_description || pred.description || 'Unknown task'}</span>
                <span className="text-cyber-cyan text-[10px] flex-shrink-0">
                  {pred.confidence ? (pred.confidence * 100).toFixed(0) : '85'}% CONF
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
