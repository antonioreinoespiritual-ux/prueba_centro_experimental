import { create } from 'zustand';
import { CloudItem, CloudLibrary, createFolder, fetchItems, fetchLibraries, uploadFile } from '../api';

type ViewMode = 'list' | 'grid';

interface CloudState {
  viewMode: ViewMode;
  currentPath: string[];
  selectedIds: number[];
  libraries: CloudLibrary[];
  items: CloudItem[];
  currentLibraryId: number | null;
  currentParentId: number | null;
  loading: boolean;
  error: string | null;
  setViewMode: (mode: ViewMode) => void;
  setCurrentPath: (path: string[]) => void;
  toggleSelection: (id: number) => void;
  clearSelection: () => void;
  loadLibraries: () => Promise<void>;
  setCurrentLibrary: (id: number) => Promise<void>;
  loadItems: () => Promise<void>;
  createFolder: (name: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
}

export const useCloudStore = create<CloudState>((set, get) => ({
  viewMode: 'list',
  currentPath: ['Mi unidad'],
  selectedIds: [],
  libraries: [],
  items: [],
  currentLibraryId: null,
  currentParentId: null,
  loading: false,
  error: null,
  setViewMode: (mode) => set({ viewMode: mode }),
  setCurrentPath: (path) => set({ currentPath: path }),
  toggleSelection: (id) =>
    set((state) => ({
      selectedIds: state.selectedIds.includes(id)
        ? state.selectedIds.filter((item) => item !== id)
        : [...state.selectedIds, id],
    })),
  clearSelection: () => set({ selectedIds: [] }),
  loadLibraries: async () => {
    set({ loading: true, error: null });
    try {
      const libraries = await fetchLibraries();
      set({ libraries, loading: false });
      if (libraries.length && get().currentLibraryId === null) {
        await get().setCurrentLibrary(libraries[0].id);
      }
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Error' });
    }
  },
  setCurrentLibrary: async (id) => {
    set({ currentLibraryId: id, currentParentId: null, currentPath: ['Mi unidad'] });
    await get().loadItems();
  },
  loadItems: async () => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    set({ loading: true, error: null });
    try {
      const items = await fetchItems(currentLibraryId, currentParentId);
      set({ items, loading: false });
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Error' });
    }
  },
  createFolder: async (name) => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    await createFolder({ name, library_id: currentLibraryId, parent_id: currentParentId });
    await get().loadItems();
  },
  uploadFile: async (file) => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    await uploadFile({ file, library_id: currentLibraryId, parent_id: currentParentId });
    await get().loadItems();
  },
}));
