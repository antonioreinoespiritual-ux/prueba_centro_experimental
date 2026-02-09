import { create } from 'zustand';
import {
  CloudItem,
  CloudLibrary,
  createFolder,
  createLibrary,
  deleteItem,
  downloadFile,
  fetchDisplayMap,
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
  displayMap: Record<number, { display_name: string; badge?: string | null }>;
  currentLibraryId: number | null;
  currentParentId: number | null;
  loading: boolean;
  error: string | null;
  toast: string | null;
  searchQuery: string;
  setViewMode: (mode: ViewMode) => void;
  setCurrentPath: (path: BreadcrumbEntry[]) => void;
  toggleSelection: (id: number) => void;
  clearSelection: () => void;
  loadLibraries: () => Promise<void>;
  setCurrentLibrary: (id: number, name?: string) => Promise<void>;
  loadItems: () => Promise<void>;
  openFolder: (folder: CloudItem) => Promise<void>;
  goToBreadcrumb: (index: number) => Promise<void>;
  openSystemFolder: (name: string) => Promise<void>;
  openSystemRelPath: (relPath: string) => Promise<void>;
  openProjectsRoot: () => Promise<void>;
  createFolder: (name: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  renameSelected: () => Promise<void>;
  moveSelected: () => Promise<void>;
  deleteSelected: () => Promise<void>;
  downloadSelected: () => void;
  getDisplayNameForItem: (item: CloudItem) => string;
  getBadgeForItem: (item: CloudItem) => string | null;
  getRenameDisabledReason: () => string | null;
  setSearchQuery: (query: string) => void;
  clearToast: () => void;
}

export const useCloudStore = create<CloudState>((set, get) => ({
  viewMode: 'list',
  currentPath: [{ id: null, name: 'Mi unidad' }],
  selectedIds: [],
  libraries: [],
  items: [],
  displayMap: {},
  currentLibraryId: null,
  currentParentId: null,
  loading: false,
  error: null,
  toast: null,
  searchQuery: '',
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
        const systemLibrary = libraries.find((library) => library.is_system || library.name === '_System');
        const defaultLibrary = systemLibrary ?? libraries[0];
        await get().setCurrentLibrary(defaultLibrary.id, defaultLibrary.name);
        if (systemLibrary) {
          await get().openProjectsRoot();
        }
      }
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Error' });
    }
  },
  setCurrentLibrary: async (id, name) => {
    const resolvedName = name ?? get().libraries.find((library) => library.id === id)?.name ?? 'Mi unidad';
    const displayName = resolvedName === '_System' ? 'Sistema' : resolvedName;
    set({ currentLibraryId: id, currentParentId: null, currentPath: [{ id: null, name: displayName }] });
    await get().loadItems();
  },
  loadItems: async () => {
    const { currentLibraryId, currentParentId } = get();
    if (!currentLibraryId) return;
    set({ loading: true, error: null });
    try {
      const items = await fetchItems({ library_id: currentLibraryId, parent_id: currentParentId });
      set({ items, loading: false });
      try {
        const displayEntries = await fetchDisplayMap({ library_id: currentLibraryId, parent_id: currentParentId });
        const displayMap = displayEntries.reduce<Record<number, { display_name: string; badge?: string | null }>>(
          (acc, entry) => {
            acc[entry.item_id] = { display_name: entry.display_name, badge: entry.badge };
            return acc;
          },
          {},
        );
        set({ displayMap });
      } catch (displayError) {
        console.warn('Display map error', displayError);
        set({ displayMap: {} });
      }
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Error' });
    }
  },
  openFolder: async (folder) => {
    const { currentPath } = get();
    const displayName = get().getDisplayNameForItem(folder);
    set({ currentParentId: folder.id, currentPath: [...currentPath, { id: folder.id, name: displayName }] });
    await get().loadItems();
  },
  goToBreadcrumb: async (index) => {
    const path = get().currentPath.slice(0, index + 1);
    const parentEntry = path[path.length - 1];
    set({ currentPath: path, currentParentId: parentEntry.id });
    await get().loadItems();
  },
  openSystemFolder: async (name) => {
    const { libraries } = get();
    const systemLibrary = libraries.find((library) => library.is_system || library.name === '_System');
    if (!systemLibrary) {
      set({ toast: 'No se encontró la biblioteca del sistema.' });
      return;
    }
    if (get().currentLibraryId !== systemLibrary.id) {
      await get().setCurrentLibrary(systemLibrary.id, systemLibrary.name);
    } else {
      await get().loadItems();
    }
    const target = get().items.find(
      (item) => item.item_type === 'folder' && item.name.toLowerCase() === name.toLowerCase(),
    );
    if (!target) {
      set({ toast: `No se encontró la carpeta ${name}.` });
      return;
    }
    await get().openFolder(target);
  },
  openSystemRelPath: async (relPath) => {
    const cleanPath = relPath.replace(/^\/+/, '').replace(/\/+$/, '');
    if (!cleanPath) return;
    let segments = cleanPath.split('/').filter(Boolean);
    const { libraries } = get();
    const systemLibrary = libraries.find((library) => library.is_system || library.name === '_System');
    if (!systemLibrary) {
      set({ toast: 'No se encontró la biblioteca del sistema.' });
      return;
    }
    if (get().currentLibraryId !== systemLibrary.id) {
      await get().setCurrentLibrary(systemLibrary.id, systemLibrary.name);
    } else {
      await get().loadItems();
    }
    if (segments[0]?.toLowerCase() === 'projects') {
      await get().openProjectsRoot();
      segments = segments.slice(1);
    }
    for (const segment of segments) {
      const target = get().items.find(
        (item) => item.item_type === 'folder' && item.name.toLowerCase() === segment.toLowerCase(),
      );
      if (!target) {
        set({ toast: `No se encontró la ruta ${segment}.` });
        return;
      }
      await get().openFolder(target);
    }
  },
  openProjectsRoot: async () => {
    const { libraries } = get();
    const systemLibrary = libraries.find((library) => library.is_system || library.name === '_System');
    if (!systemLibrary) {
      set({ toast: 'No se encontró la biblioteca del sistema.' });
      return;
    }
    if (get().currentLibraryId !== systemLibrary.id) {
      await get().setCurrentLibrary(systemLibrary.id, systemLibrary.name);
    } else {
      await get().loadItems();
    }
    const target = get().items.find((item) => item.item_type === 'folder' && item.name === 'Projects');
    if (!target) {
      set({ toast: 'No se encontró la carpeta Projects.' });
      return;
    }
    set({ currentParentId: target.id, currentPath: [{ id: target.id, name: 'Projects' }] });
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
    const reason = get().getRenameDisabledReason();
    if (reason) {
      set({ toast: reason });
      return;
    }
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
  getDisplayNameForItem: (item) => {
    const mapped = get().displayMap[item.id];
    if (mapped?.display_name) return mapped.display_name;
    if (item.name === '_System') return 'Sistema';
    if (item.name === '_Archived') return 'Archivados';
    return item.name;
  },
  getBadgeForItem: (item) => get().displayMap[item.id]?.badge ?? null,
  getRenameDisabledReason: () => {
    const { selectedIds, items } = get();
    if (!selectedIds.length) return null;
    const selected = items.find((item) => item.id === selectedIds[0]);
    if (!selected || selected.item_type !== 'folder') return null;
    const badge = get().getBadgeForItem(selected);
    if (badge && (badge.startsWith('H') || badge.startsWith('R'))) {
      return 'Se renombra desde el nombre del experimento/record.';
    }
    return null;
  },
  setSearchQuery: (query) => set({ searchQuery: query }),
  clearToast: () => set({ toast: null }),
}));
