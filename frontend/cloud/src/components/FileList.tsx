import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

function formatBytes(bytes?: number | null) {
  if (!bytes) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

export function FileList() {
  const { selectedIds, toggleSelection, items, loading, error, openFolder } = useCloudStore();
  const folders = items.filter((item) => item.item_type === 'folder');
  const files = items.filter((item) => item.item_type === 'file');

  return (
    <div className="cloud-table">
      <div className="cloud-table__header">
        <span>Nombre</span>
        <span>Propietario</span>
        <span>Tamaño</span>
        <span>Fecha</span>
      </div>
      <div className="cloud-table__body">
        {loading && <div className="cloud-table__row">Cargando archivos...</div>}
        {error && <div className="cloud-table__row">Error: {error}</div>}
        {!loading && !items.length && <div className="cloud-table__row">Sin archivos aún.</div>}
        {folders.map((folder) => (
          <button
            key={`folder-${folder.id}`}
            className={`cloud-table__row ${selectedIds.includes(folder.id) ? 'is-selected' : ''}`}
            onClick={() => toggleSelection(folder.id)}
            onDoubleClick={() => openFolder(folder)}
          >
            <span>📁 {folder.name}</span>
            <span>{folder.owner_id ?? '—'}</span>
            <span>—</span>
            <span>—</span>
          </button>
        ))}
        {files.map((file) => (
          <button
            key={`file-${file.id}`}
            className={`cloud-table__row ${selectedIds.includes(file.id) ? 'is-selected' : ''}`}
            onClick={() => toggleSelection(file.id)}
          >
            <span>{file.name}</span>
            <span>{file.owner_id ?? '—'}</span>
            <span>{formatBytes(file.size)}</span>
            <span>—</span>
          </button>
        ))}
      </div>
    </div>
  );
}
