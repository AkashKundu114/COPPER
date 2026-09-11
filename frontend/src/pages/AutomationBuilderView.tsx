import React, { useState } from 'react';
import { Play, Plus, Settings, Trash2, GitPullRequest, Clock, Brain, FileText, ArrowRight } from 'lucide-react';

interface AutomationRule {
  id: string;
  name: string;
  triggerType: string;
  condition: string;
  action: string;
  isActive: boolean;
}

const PREMADE_TEMPLATES = [
  { id: 'tpl1', name: 'Deep Work Protocol', triggerType: 'Time of Day', condition: '9:00 AM - 11:00 AM', action: 'Mute Notifications & Context Switch', icon: Brain },
  { id: 'tpl2', name: 'Daily Wrap-Up', triggerType: 'Time of Day', condition: '5:00 PM', action: 'Draft Summary', icon: Clock },
  { id: 'tpl3', name: 'Git Code Review on Push', triggerType: 'Commit Created', condition: 'Any branch', action: 'Run Script', icon: GitPullRequest },
  { id: 'tpl4', name: 'Meeting Note Transcriber', triggerType: 'Audio Ended', condition: 'Duration > 5m', action: 'Draft Summary', icon: FileText },
];

export const AutomationBuilderView: React.FC = () => {
  const [automations, setAutomations] = useState<AutomationRule[]>([
    {
      id: 'rule1',
      name: 'Focus Mode Trigger',
      triggerType: 'Cognitive State = Deep Focus',
      condition: 'Focus duration > 30m',
      action: 'Mute Notifications',
      isActive: true,
    },
    {
      id: 'rule2',
      name: 'Automated Scripts',
      triggerType: 'Window Focused',
      condition: 'App = VS Code',
      action: 'Switch Project Context',
      isActive: false,
    }
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRule, setNewRule] = useState<Partial<AutomationRule>>({});

  const toggleAutomation = (id: string) => {
    setAutomations(prev => prev.map(rule => rule.id === id ? { ...rule, isActive: !rule.isActive } : rule));
  };

  const deleteAutomation = (id: string) => {
    setAutomations(prev => prev.filter(rule => rule.id !== id));
  };

  const handleAddCustom = () => {
    if (newRule.name && newRule.triggerType && newRule.action) {
      setAutomations([...automations, {
        id: `rule_${Date.now()}`,
        name: newRule.name,
        triggerType: newRule.triggerType,
        condition: newRule.condition || 'Always',
        action: newRule.action,
        isActive: true,
      }]);
      setIsModalOpen(false);
      setNewRule({});
    }
  };

  const addTemplate = (tpl: typeof PREMADE_TEMPLATES[0]) => {
    setAutomations([...automations, {
      id: `rule_${Date.now()}`,
      name: tpl.name,
      triggerType: tpl.triggerType,
      condition: tpl.condition,
      action: tpl.action,
      isActive: true,
    }]);
  };

  return (
    <div className="p-6 h-full flex flex-col font-mono text-zinc-300">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-display font-bold text-white mb-1 flex items-center gap-2">
            <Settings className="w-6 h-6 text-cyber-cyan" />
            Visual Automation & Trigger Canvas
          </h2>
          <p className="text-xs text-zinc-500">Configure reactive behaviors and triggers for C.O.P.P.E.R.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-cyber-cyan/10 hover:bg-cyber-cyan/20 border border-cyber-cyan/30 text-cyber-cyan rounded-lg text-sm transition-all shadow-[0_0_15px_rgba(0,240,255,0.15)]"
        >
          <Plus className="w-4 h-4" />
          Add Custom Trigger
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        <div className="lg:col-span-2 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2 pb-4">
          <h3 className="text-sm font-semibold text-white mb-2">Active Automations Canvas</h3>
          {automations.map(rule => (
            <div key={rule.id} className="relative group bg-[#0a0f19] border border-white/10 rounded-xl p-4 flex flex-col gap-3 transition-all hover:border-cyber-cyan/40">
              <div className="flex items-center justify-between">
                <h4 className="text-white font-medium flex items-center gap-2">
                  <Play className={`w-4 h-4 ${rule.isActive ? 'text-verdigris' : 'text-zinc-600'}`} />
                  {rule.name}
                </h4>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => toggleAutomation(rule.id)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${rule.isActive ? 'bg-verdigris' : 'bg-zinc-700'}`}
                  >
                    <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${rule.isActive ? 'translate-x-5' : 'translate-x-1'}`} />
                  </button>
                  <button onClick={() => deleteAutomation(rule.id)} className="text-zinc-500 hover:text-red-400 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <div className="flex items-center gap-4 text-xs mt-2 bg-white/5 p-3 rounded-lg overflow-x-auto">
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-zinc-500 uppercase tracking-wider text-[10px]">Trigger</span>
                  <span className="text-cyber-cyan truncate">{rule.triggerType}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-zinc-500 uppercase tracking-wider text-[10px]">Condition</span>
                  <span className="text-amber-400 truncate">{rule.condition}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-zinc-500 uppercase tracking-wider text-[10px]">Action</span>
                  <span className="text-verdigris truncate">{rule.action}</span>
                </div>
              </div>
            </div>
          ))}
          {automations.length === 0 && (
            <div className="text-center p-8 border border-dashed border-white/10 rounded-xl text-zinc-500 text-sm">
              No automations active. Add a custom rule or choose a template.
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4">
          <h3 className="text-sm font-semibold text-white mb-2">Pre-Made Templates</h3>
          <div className="grid gap-3">
            {PREMADE_TEMPLATES.map(tpl => (
              <button
                key={tpl.id}
                onClick={() => addTemplate(tpl)}
                className="flex items-start gap-3 p-3 bg-white/[0.03] hover:bg-white/[0.08] border border-white/5 rounded-lg text-left transition-colors group"
              >
                <div className="p-2 bg-black/40 rounded-md text-cyber-cyan group-hover:text-white transition-colors">
                  <tpl.icon className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-white mb-1">{tpl.name}</h4>
                  <p className="text-[10px] text-zinc-500">{tpl.triggerType} → {tpl.action}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#0a0f19] border border-cyber-cyan/30 rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Create Custom Automation</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Rule Name</label>
                <input
                  type="text"
                  value={newRule.name || ''}
                  onChange={e => setNewRule({ ...newRule, name: e.target.value })}
                  placeholder="e.g. Build Notifier"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Trigger Type</label>
                <input
                  type="text"
                  value={newRule.triggerType || ''}
                  onChange={e => setNewRule({ ...newRule, triggerType: e.target.value })}
                  placeholder="e.g. Window Focused, Time of Day"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Condition</label>
                <input
                  type="text"
                  value={newRule.condition || ''}
                  onChange={e => setNewRule({ ...newRule, condition: e.target.value })}
                  placeholder="e.g. App = Terminal"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Target Action</label>
                <input
                  type="text"
                  value={newRule.action || ''}
                  onChange={e => setNewRule({ ...newRule, action: e.target.value })}
                  placeholder="e.g. Run Script"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan transition-colors"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 text-xs text-zinc-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddCustom}
                disabled={!newRule.name || !newRule.triggerType || !newRule.action}
                className="px-4 py-2 bg-cyber-cyan text-black text-xs font-bold rounded-lg hover:bg-[#53c9e5] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Deploy Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
