export const AGENT_COLORS: Record<string, string> = {
  chat: "text-blue-400",
  coding: "text-green-400",
  automation: "text-yellow-400",
  reminder: "text-purple-400",
  research: "text-cyan-400",
  vision: "text-pink-400",
};

export const AGENT_ICONS: Record<string, string> = {
  chat: "💬",
  coding: "💻",
  automation: "⚙️",
  reminder: "🔔",
  research: "🔍",
  vision: "👁️",
};

export const AGENT_LABELS: Record<string, string> = {
  chat: "Chat",
  coding: "Coding",
  automation: "Automation",
  reminder: "Reminder",
  research: "Research",
  vision: "Vision",
};

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

export function formatRelativeTime(date: Date): string {
  const diff = Date.now() - date.getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
