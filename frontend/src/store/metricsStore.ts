import { create } from "zustand";

interface MetricsStore {
  currentMrr: number;
  setCurrentMrr: (v: number) => void;
}

export const useMetricsStore = create<MetricsStore>((set) => ({
  currentMrr: 0,
  setCurrentMrr: (v) => set({ currentMrr: v }),
}));
