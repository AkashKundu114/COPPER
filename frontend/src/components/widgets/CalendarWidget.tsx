const DAY_LABELS = ["S", "M", "T", "W", "T", "F", "S"];

export function CalendarWidget() {
  const now = new Date();
  const month = now.toLocaleDateString([], { month: "long" });
  const weekday = now.toLocaleDateString([], { weekday: "long" });
  const date = now.getDate();

  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - now.getDay());
  const week = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(startOfWeek);
    d.setDate(startOfWeek.getDate() + i);
    return d;
  });

  return (
    <div className="rounded-none border border-zinc-800 bg-void-panel px-4 py-3 min-w-[190px]">
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <p className="font-mono text-[10px] text-ink-faint uppercase tracking-wider">{month}</p>
          <p className="font-display font-semibold text-xl text-white leading-tight">{weekday}</p>
        </div>
        <span className="font-display font-bold text-2xl text-zinc-100">{date}</span>
      </div>
      <div className="flex justify-between gap-1">
        {week.map((d, i) => {
          const isToday = d.toDateString() === now.toDateString();
          return (
            <div
              key={i}
              className={`flex-1 flex flex-col items-center gap-0.5 rounded-none py-1 ${
                isToday ? "bg-zinc-800" : ""
              }`}
            >
              <span className="font-mono text-[9px] text-ink-faint">{DAY_LABELS[i]}</span>
              <span className={`text-xs ${isToday ? "text-white font-semibold" : "text-ink-secondary"}`}>
                {d.getDate()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
