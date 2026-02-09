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
  const { selectedIds, toggleSelection, items, loading, error } = useCloudStore();
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
        {!loading && !files.length && <div className="cloud-table__row">Sin archivos aún.</div>}
        {files.map((file) => (
          <button
            key={file.id}
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
