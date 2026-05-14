import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Bell } from "lucide-react";
import { wsService } from "@/services/websocket";

interface Notification {
  id: string;
  title: string;
  body: string;
  type: string;
  timestamp: Date;
}

export function NotificationPanel() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    const unsub = wsService.onMessage((msg) => {
      if (msg.type === "notification" || msg.type === "reminder") {
        const notif: Notification = {
          id: crypto.randomUUID(),
          title: msg.title || "COPPER",
          body: msg.body || msg.content || "",
          type: msg.type,
          timestamp: new Date(),
        };
        setNotifications((n) => [notif, ...n].slice(0, 10));
        setTimeout(() => dismiss(notif.id), 6000);
      }
    });
    return unsub;
  }, []);

  const dismiss = (id: string) =>
    setNotifications((n) => n.filter((x) => x.id !== id));

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
      <AnimatePresence>
        {notifications.map((n) => (
          <motion.div
            key={n.id}
            initial={{ x: 60, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 60, opacity: 0 }}
            className="glass rounded-xl p-4 border border-copper-600/30"
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 p-1.5 rounded-lg bg-copper-600/20">
                <Bell size={14} className="text-copper-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{n.title}</p>
                {n.body && <p className="text-xs text-gray-400 mt-0.5 truncate">{n.body}</p>}
              </div>
              <button onClick={() => dismiss(n.id)}
                className="text-gray-600 hover:text-white transition-colors flex-shrink-0">
                <X size={14} />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
