import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, CheckCircle } from "lucide-react";
import { remindersAPI } from "@/services/api";
import { formatDateTime } from "@/utils/constants";

export function ReminderWidget() {
  const [reminders, setReminders] = useState<any[]>([]);

  useEffect(() => {
    remindersAPI.list(false).then(({ data }) => setReminders(data.slice(0, 4)));
  }, []);

  const complete = async (id: number) => {
    await remindersAPI.complete(id);
    setReminders((r) => r.filter((x) => x.id !== id));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Bell size={16} className="text-yellow-400" />
        <span className="text-sm font-medium text-gray-400">Upcoming Reminders</span>
      </div>
      <div className="space-y-2">
        {reminders.length === 0 && (
          <p className="text-xs text-gray-600 text-center py-3">No upcoming reminders</p>
        )}
        {reminders.map((r) => (
          <div key={r.id} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-dark-700">
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-200 truncate">{r.title}</p>
              <p className="text-xs text-gray-500">{formatDateTime(r.due_at)}</p>
            </div>
            <button onClick={() => complete(r.id)}
              className="flex-shrink-0 text-gray-600 hover:text-green-400 transition-colors">
              <CheckCircle size={16} />
            </button>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
