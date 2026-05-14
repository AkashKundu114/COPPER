import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, Plus, Check, Trash2, Sparkles } from "lucide-react";
import { remindersAPI } from "@/services/api";
import { Modal } from "@/components/common/Modal";
import { formatDateTime } from "@/utils/constants";

export default function Reminders() {
  const [reminders, setReminders] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [nlText, setNlText] = useState("");
  const [parsed, setParsed] = useState<any>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", due_at: "", is_recurring: false, recurrence_rule: "" });

  const load = async () => {
    const { data } = await remindersAPI.list(false);
    setReminders(data);
  };

  useEffect(() => { load(); }, []);

  const parseNL = async () => {
    if (!nlText.trim()) return;
    setIsParsing(true);
    try {
      const { data } = await remindersAPI.parseFromText(nlText);
      setParsed(data);
      setForm({
        title: data.title || "",
        description: data.description || "",
        due_at: data.due_at || "",
        is_recurring: data.is_recurring || false,
        recurrence_rule: data.recurrence_rule || "",
      });
    } catch { alert("Could not parse reminder text"); }
    finally { setIsParsing(false); }
  };

  const submit = async () => {
    if (!form.title || !form.due_at) return;
    await remindersAPI.create(form);
    setShowAdd(false);
    setNlText(""); setParsed(null);
    setForm({ title: "", description: "", due_at: "", is_recurring: false, recurrence_rule: "" });
    load();
  };

  const complete = async (id: number) => {
    await remindersAPI.complete(id);
    setReminders((r) => r.filter((x) => x.id !== id));
  };

  const remove = async (id: number) => {
    await remindersAPI.delete(id);
    setReminders((r) => r.filter((x) => x.id !== id));
  };

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell size={20} className="text-yellow-400" />
          <h2 className="font-semibold text-white">Reminders</h2>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-copper text-sm flex items-center gap-1.5">
          <Plus size={16} /> New Reminder
        </button>
      </div>

      <AnimatePresence>
        {reminders.length === 0 && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="text-center text-gray-600 text-sm py-12">
            No pending reminders — you're all caught up! 🎉
          </motion.p>
        )}
        {reminders.map((r) => (
          <motion.div key={r.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: 20 }}
            className="glass rounded-xl p-4 flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-white text-sm">{r.title}</p>
              {r.description && <p className="text-xs text-gray-400 mt-0.5">{r.description}</p>}
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-copper-400">{formatDateTime(r.due_at)}</span>
                {r.is_recurring && (
                  <span className="text-xs bg-purple-600/20 text-purple-400 px-2 py-0.5 rounded-full">
                    Recurring
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-1 flex-shrink-0">
              <button onClick={() => complete(r.id)}
                className="p-1.5 rounded-lg text-gray-600 hover:text-green-400 hover:bg-green-400/10 transition-colors">
                <Check size={16} />
              </button>
              <button onClick={() => remove(r.id)}
                className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition-colors">
                <Trash2 size={16} />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title="New Reminder">
        <div className="space-y-4">
          {/* Natural language input */}
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Describe it naturally</label>
            <div className="flex gap-2">
              <input value={nlText} onChange={(e) => setNlText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && parseNL()}
                placeholder="Remind me to review PR tomorrow at 10am"
                className="flex-1 input-copper text-sm" />
              <button onClick={parseNL} disabled={isParsing}
                className="px-3 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 transition-colors text-sm flex items-center gap-1">
                <Sparkles size={14} /> {isParsing ? "..." : "Parse"}
              </button>
            </div>
          </div>

          <div className="border-t border-white/5 pt-4 space-y-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Title *</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full input-copper text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Description</label>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full input-copper text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Due at *</label>
              <input type="datetime-local" value={form.due_at}
                onChange={(e) => setForm({ ...form, due_at: e.target.value })}
                className="w-full input-copper text-sm" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="recurring" checked={form.is_recurring}
                onChange={(e) => setForm({ ...form, is_recurring: e.target.checked })}
                className="accent-copper-500" />
              <label htmlFor="recurring" className="text-sm text-gray-400">Recurring</label>
            </div>
            {form.is_recurring && (
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Cron expression</label>
                <input value={form.recurrence_rule}
                  onChange={(e) => setForm({ ...form, recurrence_rule: e.target.value })}
                  placeholder="0 9 * * 1-5  (Mon-Fri at 9am)"
                  className="w-full input-copper text-sm font-mono" />
              </div>
            )}
          </div>
          <button onClick={submit} className="w-full btn-copper">Save Reminder</button>
        </div>
      </Modal>
    </div>
  );
}
