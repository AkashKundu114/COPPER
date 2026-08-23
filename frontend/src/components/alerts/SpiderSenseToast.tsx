import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Info, ShieldAlert, X } from "lucide-react";
import { playAlertSound } from "../../utils/alertSound";

export interface ProactiveAlert {
  alert_id: string;
  severity: "info" | "warning" | "critical";
  category: string;
  title: string;
  message: string;
  mode: string;
  suggested_actions: string[];
}

interface SpiderSenseToastProps {
  alerts: ProactiveAlert[];
  onDismiss: (alertId: string) => void;
  onAction: (alertId: string, action: string) => void;
}

const SEVERITY_CONFIG = {
  info: {
    icon: Info,
    border: "border-blue-500/40",
    bg: "bg-blue-950/30",
    iconColor: "text-blue-400",
    titleColor: "text-blue-300",
    autoDismissMs: 15000,
  },
  warning: {
    icon: AlertTriangle,
    border: "border-amber-500/40",
    bg: "bg-amber-950/30",
    iconColor: "text-amber-400",
    titleColor: "text-amber-300",
    autoDismissMs: 0,
  },
  critical: {
    icon: ShieldAlert,
    border: "border-red-500/40",
    bg: "bg-red-950/30",
    iconColor: "text-red-400",
    titleColor: "text-red-300",
    autoDismissMs: 0,
  },
};

function AlertToast({
  alert,
  onDismiss,
  onAction,
}: {
  alert: ProactiveAlert;
  onDismiss: () => void;
  onAction: (action: string) => void;
}) {
  const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
  const Icon = config.icon;

  useEffect(() => {
    playAlertSound(alert.severity);
  }, [alert.severity]);

  useEffect(() => {
    if (config.autoDismissMs > 0) {
      const timer = setTimeout(onDismiss, config.autoDismissMs);
      return () => clearTimeout(timer);
    }
  }, [config.autoDismissMs, onDismiss]);

  return (
    <motion.div
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 300 }}
      className={`w-96 rounded-xl border ${config.border} ${config.bg} backdrop-blur-md p-4 shadow-2xl`}
    >
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 mt-0.5 ${config.iconColor}`}>
          <Icon size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className={`text-sm font-semibold ${config.titleColor}`}>
              {alert.title}
            </h4>
            <button
              onClick={onDismiss}
              className="text-gray-500 hover:text-gray-300 transition-colors flex-shrink-0"
            >
              <X size={14} />
            </button>
          </div>
          <p className="text-xs text-gray-300 mt-1 leading-relaxed">
            {alert.message}
          </p>
          {alert.suggested_actions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {alert.suggested_actions.map((action) => (
                <button
                  key={action}
                  onClick={() => onAction(action)}
                  className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-[11px] text-gray-300 font-medium border border-white/10 transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
              Spider-Sense • {alert.category}
            </span>
          </div>
          {config.autoDismissMs > 0 && (
            <div className="mt-2 h-[2px] w-full bg-black/20 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{
                  duration: config.autoDismissMs / 1000,
                  ease: "linear",
                }}
                className={`h-full ${config.bg.replace("/30", "")}`}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function SpiderSenseToast({
  alerts,
  onDismiss,
  onAction,
}: SpiderSenseToastProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 pointer-events-auto">
      <AnimatePresence mode="popLayout">
        {alerts.slice(0, 3).map((alert) => (
          <AlertToast
            key={alert.alert_id}
            alert={alert}
            onDismiss={() => onDismiss(alert.alert_id)}
            onAction={(action) => onAction(alert.alert_id, action)}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
