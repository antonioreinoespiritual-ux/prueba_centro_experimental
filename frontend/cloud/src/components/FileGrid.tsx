import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function FileGrid() {
  const { selectedIds, toggleSelection, items, loading, error, openFolder } = useCloudStore();
  const folders = items.filter((item) => item.item_type === 'folder');

  return (
    <div className="cloud-grid">
      {loading && <div className="cloud-card">Cargando...</div>}
      {error && <div className="cloud-card">Error: {error}</div>}
      {!loading && !folders.length && <div className="cloud-card">Sin carpetas.</div>}
      {folders.map((folder) => (
        <button
          key={folder.id}
          className={`cloud-card ${selectedIds.includes(folder.id) ? 'is-selected' : ''}`}
          onClick={() => toggleSelection(folder.id)}
          onDoubleClick={() => openFolder(folder)}
        >
          <div className="cloud-card__icon">📁</div>
          <div className="cloud-card__name">{folder.name}</div>
          <div className="cloud-card__meta">Carpeta</div>
        </button>
      ))}
    </div>
  );
}
