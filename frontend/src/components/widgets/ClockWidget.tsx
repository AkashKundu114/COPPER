import { useEffect, useState } from "react";

export function ClockWidget() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const time = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const seconds = now.toLocaleTimeString([], { second: "2-digit" });

  return (
    <div className="rounded-none border border-zinc-800 bg-void-panel px-4 py-3 min-w-[150px]">
      <div className="flex items-baseline gap-1">
        <span className="font-display font-semibold text-2xl text-white tabular-nums">{time}</span>
        <span className="font-mono text-xs text-zinc-400 tabular-nums">:{seconds}</span>
      </div>
      <p className="font-mono text-[10px] text-ink-faint mt-0.5 uppercase tracking-wider">
        {Intl.DateTimeFormat().resolvedOptions().timeZone.split("/").pop()?.replace("_", " ")}
      </p>
    </div>
  );
}
