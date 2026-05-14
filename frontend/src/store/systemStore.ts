import { create } from "zustand";
import { automationAPI } from "@/services/api";

interface SystemStats {
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  os: string;
}

interface SystemStore {
  stats: SystemStats | null;
  processes: any[];
  isLoading: boolean;
  lastUpdated: Date | null;

  fetchStats: () => Promise<void>;
  fetchProcesses: () => Promise<void>;
}

export const useSystemStore = create<SystemStore>((set) => ({
  stats: null,
  processes: [],
  isLoading: false,
  lastUpdated: null,

  fetchStats: async () => {
    set({ isLoading: true });
    try {
      const { data } = await automationAPI.getStats();
      set({ stats: data, lastUpdated: new Date() });
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    } finally {
      set({ isLoading: false });
    }
  },

  fetchProcesses: async () => {
    try {
      const { data } = await automationAPI.getProcesses();
      set({ processes: data });
    } catch (e) {
      console.error("Failed to fetch processes:", e);
    }
  },
}));
