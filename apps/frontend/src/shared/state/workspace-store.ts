"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface WorkspaceState {
  workspaceId: string | null;
  preferredAgentProfileId: string | null;
  useRetrieval: boolean;
  topK: number;
  setWorkspaceId: (id: string | null) => void;
  setPreferredAgentProfileId: (id: string | null) => void;
  setUseRetrieval: (value: boolean) => void;
  setTopK: (value: number) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      workspaceId: null,
      preferredAgentProfileId: null,
      useRetrieval: false,
      topK: 3,
      setWorkspaceId: (id) => set({ workspaceId: id }),
      setPreferredAgentProfileId: (id) => set({ preferredAgentProfileId: id }),
      setUseRetrieval: (value) => set({ useRetrieval: value }),
      setTopK: (value) => set({ topK: value }),
    }),
    { name: "semantic-reasoning-workspace" },
  ),
);
