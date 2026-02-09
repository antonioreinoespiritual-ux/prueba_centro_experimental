export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${input}`, init);
  if (!response.ok) {
    const text = await response.text();
    console.error('API error', { input, status: response.status, body: text });
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface CloudLibrary {
  id: number;
  name: string;
  owner_id?: string | null;
}

export interface CloudItem {
  id: number;
  name: string;
  parent_id?: number | null;
  library_id: number;
  item_type: 'folder' | 'file';
  size?: number | null;
  path?: string | null;
  owner_id?: string | null;
}

export async function fetchLibraries(): Promise<CloudLibrary[]> {
  return fetchJson('/api/cloud/libraries');
}

export async function createLibrary(payload: { name: string; owner_id?: string | null }): Promise<CloudLibrary> {
  return fetchJson('/api/cloud/libraries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function fetchItems(params: { library_id: number; parent_id?: number | null }): Promise<CloudItem[]> {
  const query = new URLSearchParams();
  query.set('library_id', String(params.library_id));
  if (params.parent_id !== undefined && params.parent_id !== null) {
    query.set('parent_id', String(params.parent_id));
  }
  return fetchJson(`/api/cloud/items?${query.toString()}`);
}

export async function createFolder(payload: {
  name: string;
  library_id: number;
  parent_id?: number | null;
}): Promise<CloudItem> {
  return fetchJson('/api/cloud/folders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function uploadFile(payload: {
  file: File;
  library_id: number;
  parent_id?: number | null;
}): Promise<CloudItem> {
  const formData = new FormData();
  formData.append('file', payload.file);
  formData.append('filename', payload.file.name);
  formData.append('library_id', String(payload.library_id));
  if (payload.parent_id !== undefined && payload.parent_id !== null) {
    formData.append('parent_id', String(payload.parent_id));
  }
  return fetchJson('/api/cloud/files/complete-upload', {
    method: 'POST',
    body: formData,
  });
}

export async function renameItem(itemId: number, name: string): Promise<CloudItem> {
  return fetchJson(`/api/cloud/items/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}

export async function moveItem(itemId: number, parent_id: number | null): Promise<CloudItem> {
  return fetchJson(`/api/cloud/items/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parent_id }),
  });
}

export async function deleteItem(itemId: number): Promise<{ deleted: boolean; item_id: number }> {
  return fetchJson(`/api/cloud/items/${itemId}`, { method: 'DELETE' });
}

export function downloadFile(itemId: number) {
  window.open(`${API_BASE}/api/cloud/files/${itemId}/download`, '_blank');
}
