import { useEffect } from "react";
import { useSystemStore } from "@/store/systemStore";

export function useSystemStats(intervalMs = 5000) {
  const { fetchStats, stats, isLoading } = useSystemStore();

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, intervalMs);
    return () => clearInterval(interval);
  }, [intervalMs]);

  return { stats, isLoading };
}
