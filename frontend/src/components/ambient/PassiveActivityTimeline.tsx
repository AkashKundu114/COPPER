import React, { useState, useEffect } from 'react';
import { ambientAPI } from '../../services/api';
import { Activity, Clock, Layers, Maximize2, Terminal, AlertCircle } from 'lucide-react';

export const PassiveActivityTimeline: React.FC = () => {
  const [hours, setHours] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Data states
  const [timeline, setTimeline] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [currentContext, setCurrentContext] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, [hours]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [
        timelineRes,
        sessionsRes,
        statsRes,
        contextRes,
        summaryRes
      ] = await Promise.all([
        ambientAPI.getTimeline(hours),
        ambientAPI.getSessions(hours),
        ambientAPI.getStats(hours),
        ambientAPI.getCurrentContext(),
        ambientAPI.getSummary()
      ]);

      setTimeline(timelineRes.data?.timeline || []);
      setSessions(sessionsRes.data?.sessions || []);
      setStats(statsRes.data || {});
      setCurrentContext(contextRes.data || null);
      setSummary(summaryRes.data || null);
    } catch (error) {
      console.error('Error fetching ambient data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (mins: number) => {
    if (!mins) return '0m';
    if (mins < 60) return `${Math.floor(mins)}m`;
    const h = Math.floor(mins / 60);
    const m = Math.floor(mins % 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="flex flex-col gap-4 p-4 bg-slate-900/80 border border-slate-800 rounded-lg text-slate-300 font-mono text-xs w-full max-w-4xl">
      {/* Header & Controls */}
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <h2 className="text-purple-400 text-sm font-semibold flex items-center gap-2">
          <Activity size={16} />
          Passive Activity Monitor
        </h2>
        
        <div className="flex gap-2">
          {[2, 8, 24].map((h) => (
            <button
              key={h}
              onClick={() => setHours(h)}
              className={`px-3 py-1 border rounded transition-colors ${
                hours === h 
                  ? 'bg-purple-900/40 border-purple-500/50 text-purple-300' 
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {h}h
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-40 text-purple-400/70">
          Initializing telemetry...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* Main Column */}
          <div className="md:col-span-2 flex flex-col gap-4">
            
            {/* Current Context */}
            <div className="bg-slate-800/30 border border-slate-700/50 p-3 rounded">
              <h3 className="text-accent-400 mb-2 flex items-center gap-2">
                <Maximize2 size={14} />
                Current Foreground Context
              </h3>
              {currentContext ? (
                <div className="flex flex-col gap-1">
                  <div className="text-purple-300 truncate font-semibold">
                    {currentContext.app_name || currentContext.app || 'Unknown App'}
                  </div>
                  <div className="text-slate-400 truncate text-[10px]">
                    {currentContext.window_title || currentContext.title || 'No active window'}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500 italic">No context detected</div>
              )}
            </div>

            {/* Daily Summary */}
            {summary && (
              <div className="bg-slate-800/30 border border-slate-700/50 p-3 rounded">
                <h3 className="text-accent-400 mb-2 flex items-center gap-2">
                  <Terminal size={14} />
                  Activity Synthesis
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  {summary.summary || summary.text || 'Insufficient data for synthesis.'}
                </p>
              </div>
            )}

            {/* Timeline View */}
            <div className="bg-slate-800/30 border border-slate-700/50 p-3 rounded flex-1">
              <h3 className="text-accent-400 mb-3 flex items-center gap-2">
                <Clock size={14} />
                Activity Timeline ({hours}h)
              </h3>
              <div className="relative border-l border-slate-700 ml-2 pl-4 flex flex-col gap-4 max-h-64 overflow-y-auto">
                {timeline.length > 0 || sessions.length > 0 ? (
                  (timeline.length > 0 ? timeline : sessions).map((item, idx) => (
                    <div key={idx} className="relative">
                      <div className="absolute -left-[21px] top-1 w-2 h-2 bg-purple-500 rounded-full border border-slate-900" />
                      <div className="text-[10px] text-slate-500 mb-1">
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'Unknown Time'}
                      </div>
                      <div className="text-slate-300">
                        {item.activity || item.name || item.app || 'Unknown Activity'}
                      </div>
                      {item.duration && (
                        <div className="text-purple-400/80 text-[10px]">
                          {formatDuration(item.duration)}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-slate-500 flex items-center gap-2">
                    <AlertCircle size={12} />
                    No timeline data recorded in this period.
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Side Column - Stats */}
          <div className="flex flex-col gap-4">
            
            <div className="bg-slate-800/30 border border-slate-700/50 p-3 rounded">
              <h3 className="text-accent-400 mb-3 flex items-center gap-2">
                <Layers size={14} />
                Productivity Metrics
              </h3>
              
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Focus Time</span>
                  <span className="text-purple-300">{formatDuration(stats?.focus_time_mins || stats?.focus_time || 0)}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Context Switches</span>
                  <span className="text-purple-300">{stats?.context_switches || 0}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Longest Streak</span>
                  <span className="text-purple-300">{formatDuration(stats?.longest_streak_mins || stats?.longest_streak || 0)}</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/30 border border-slate-700/50 p-3 rounded flex-1">
              <h3 className="text-accent-400 mb-3">App Distribution</h3>
              <div className="flex flex-col gap-2">
                {['coding', 'browsing', 'communication', 'documents', 'media'].map(category => {
                  const dist = stats?.categories || stats?.category_distribution || {};
                  const val = dist[category] || 0;
                  // assuming val is percentage 0-100 or absolute mins. Let's treat it as percentage for visual.
                  // If it's absolute, we can just show it. We'll show the value and a bar.
                  return (
                    <div key={category} className="flex flex-col gap-1">
                      <div className="flex justify-between text-[10px]">
                        <span className="text-slate-400 capitalize">{category}</span>
                        <span className="text-slate-300">{typeof val === 'number' ? Math.round(val) : val}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div 
                          className="bg-purple-500 h-1.5 rounded-full" 
                          style={{ width: `${typeof val === 'number' ? Math.min(100, Math.max(0, val)) : 0}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

        </div>
      )}
    </div>
  );
};
