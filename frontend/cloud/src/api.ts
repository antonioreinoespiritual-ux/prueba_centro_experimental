export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

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
  const response = await fetch(`${API_BASE}/api/cloud/libraries`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function createLibrary(name: string): Promise<CloudLibrary> {
  const response = await fetch(`${API_BASE}/api/cloud/libraries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function fetchItems(libraryId: number, parentId?: number | null): Promise<CloudItem[]> {
  const params = new URLSearchParams();
  params.set('library_id', String(libraryId));
  if (parentId !== undefined && parentId !== null) params.set('parent_id', String(parentId));
  const response = await fetch(`${API_BASE}/api/cloud/items?${params.toString()}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function createFolder(payload: {
  name: string;
  library_id: number;
  parent_id?: number | null;
}): Promise<CloudItem> {
  const response = await fetch(`${API_BASE}/api/cloud/folders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
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
  if (payload.parent_id) formData.append('parent_id', String(payload.parent_id));
  const response = await fetch(`${API_BASE}/api/cloud/files/complete-upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
