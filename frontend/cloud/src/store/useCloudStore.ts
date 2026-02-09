import { create } from 'zustand';

type ViewMode = 'list' | 'grid';

interface CloudState {
  viewMode: ViewMode;
  currentPath: string[];
  selectedIds: string[];
  setViewMode: (mode: ViewMode) => void;
  setCurrentPath: (path: string[]) => void;
  toggleSelection: (id: string) => void;
  clearSelection: () => void;
}

export const useCloudStore = create<CloudState>((set) => ({
  viewMode: 'list',
  currentPath: ['Mi unidad'],
  selectedIds: [],
  setViewMode: (mode) => set({ viewMode: mode }),
  setCurrentPath: (path) => set({ currentPath: path }),
  toggleSelection: (id) =>
    set((state) => ({
      selectedIds: state.selectedIds.includes(id)
        ? state.selectedIds.filter((item) => item !== id)
        : [...state.selectedIds, id],
    })),
  clearSelection: () => set({ selectedIds: [] }),
}));
