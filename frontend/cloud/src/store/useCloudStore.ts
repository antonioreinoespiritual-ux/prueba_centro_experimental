import { create } from 'zustand';
import {
  CloudItem,
  CloudLibrary,
  createFolder,
  createLibrary,
  deleteItem,
  downloadFile,
  fetchItems,
  fetchLibraries,
  moveItem,
  renameItem,
  uploadFile,
} from '../api/cloud';

type ViewMode = 'list' | 'grid';

interface BreadcrumbEntry {
  id: number | null;
  name: string;
}

interface CloudState {
  viewMode: ViewMode;
  currentPath: BreadcrumbEntry[];
  selectedIds: number[];
  libraries: CloudLibrary[];
  items: CloudItem[];
  currentLibraryId: number | null;
  currentParentId: number | null;
  loading: boolean;
  error: string | null;
  toast: string | null;
  setViewMode: (mode: ViewMode) => void;
  setCurrentPath: (path: BreadcrumbEntry[]) => void;
  toggleSelection: (id: number) => void;
  clearSelection: () => void;
  loadLibraries: () => Promise<void>;
  setCurrentLibrary: (id: number) => Promise<void>;
  loadItems: () => Promise<void>;
  openFolder: (folder: CloudItem) => Promise<void>;
  goToBreadcrumb: (index: number) => Promise<void>;
  createFolder: (name: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  renameSelected: () => Promise<void>;
  moveSelected: () => Promise<void>;
  deleteSelected: () => Promise<void>;
  downloadSelected: () => void;
  clearToast: () => void;
}

export const useCloudStore = create<CloudState>((set, get) => ({
  viewMode: 'list',
  currentPath: [{ id: null, name: 'Mi unidad' }],
  selectedIds: [],
  libraries: [],
  items: [],
  currentLibraryId: null,
  currentParentId: null,
  loading: false,
  error: null,
  toast: null,
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
      let libraries = await fetchLibraries();
      if (!libraries.length) {
        const created = await createLibrary({ name: 'Mi unidad', owner_id: 'local' });
        libraries = [created];
      }
      set({ libraries, loading: false });
      if (libraries.length) {
        await get().setCurrentLibrary(libraries[0].id);
      }
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Error' });
    }
  },
  setCurrentLibrary: async (id) => {
    set({ currentLibraryId: id, currentParentId: null, currentPath: [{ id: null, name: 'Mi unidad' }] });
    await get().loadItems();
  },
  loadItems: async () => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    set({ loading: true, error: null });
    try {
      const items = await fetchItems({ library_id: currentLibraryId, parent_id: currentParentId });
      set({ items, loading: false });
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Error' });
    }
  },
  openFolder: async (folder) => {
    const { currentPath } = get();
    set({ currentParentId: folder.id, currentPath: [...currentPath, { id: folder.id, name: folder.name }] });
    await get().loadItems();
  },
  goToBreadcrumb: async (index) => {
    const path = get().currentPath.slice(0, index + 1);
    const parentEntry = path[path.length - 1];
    set({ currentPath: path, currentParentId: parentEntry.id });
    await get().loadItems();
  },
  createFolder: async (name) => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    await createFolder({ name, library_id: currentLibraryId, parent_id: currentParentId });
    await get().loadItems();
    set({ toast: 'Carpeta creada.' });
  },
  uploadFile: async (file) => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    await uploadFile({ file, library_id: currentLibraryId, parent_id: currentParentId });
    await get().loadItems();
    set({ toast: 'Archivo subido.' });
  },
  renameSelected: async () => {
    const { selectedIds } = get();
    if (!selectedIds.length) return;
    const name = window.prompt('Nuevo nombre');
    if (!name) return;
    await renameItem(selectedIds[0], name);
    await get().loadItems();
    set({ toast: 'Elemento renombrado.' });
  },
  moveSelected: async () => {
    const { selectedIds } = get();
    if (!selectedIds.length) return;
    const parentInput = window.prompt('ID de la carpeta destino (vacío para raíz)');
    const parentId = parentInput ? Number(parentInput) : null;
    await moveItem(selectedIds[0], Number.isNaN(parentId) ? null : parentId);
    await get().loadItems();
    set({ toast: 'Elemento movido.' });
  },
  deleteSelected: async () => {
    const { selectedIds } = get();
    if (!selectedIds.length) return;
    const ok = window.confirm('¿Eliminar elemento seleccionado?');
    if (!ok) return;
    await deleteItem(selectedIds[0]);
    await get().loadItems();
    set({ toast: 'Elemento eliminado.' });
  },
  downloadSelected: () => {
    const { selectedIds } = get();
    if (!selectedIds.length) return;
    downloadFile(selectedIds[0]);
  },
  clearToast: () => set({ toast: null }),
}));
