import { useState, useCallback } from "react";
import { memoryAPI } from "@/services/api";

export function useMemory() {
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [stats, setStats] = useState<any>(null);

  const search = useCallback(async (query: string) => {
    setIsSearching(true);
    try {
      const { data } = await memoryAPI.search(query);
      setResults(data);
      return data;
    } catch (e) {
      console.error("Memory search error:", e);
      return null;
    } finally {
      setIsSearching(false);
    }
  }, []);

  const addMemory = useCallback(async (key: string, content: string, source = "manual") => {
    await memoryAPI.add(key, content, source);
  }, []);

  const fetchStats = useCallback(async () => {
    const { data } = await memoryAPI.getStats();
    setStats(data);
    return data;
  }, []);

  return { results, isSearching, stats, search, addMemory, fetchStats };
}
