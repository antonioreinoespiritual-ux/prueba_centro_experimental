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
  const {
    selectedIds,
    toggleSelection,
    items,
    loading,
    error,
    openFolder,
    searchQuery,
    getDisplayNameForItem,
    getBadgeForItem,
  } = useCloudStore();
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const visibleItems = normalizedQuery
    ? items.filter((item) => {
        const displayName = getDisplayNameForItem(item).toLowerCase();
        return item.name.toLowerCase().includes(normalizedQuery) || displayName.includes(normalizedQuery);
      })
    : items;
  const folders = visibleItems.filter((item) => item.item_type === 'folder');
  const files = visibleItems.filter((item) => item.item_type === 'file');

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
            <span className="cloud-item__name">
              <span>📁 {getDisplayNameForItem(folder)}</span>
              {getBadgeForItem(folder) && <span className="cloud-item__badge">{getBadgeForItem(folder)}</span>}
            </span>
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
            <span className="cloud-item__name">
              <span>{getDisplayNameForItem(file)}</span>
              {getBadgeForItem(file) && <span className="cloud-item__badge">{getBadgeForItem(file)}</span>}
            </span>
            <span>{file.owner_id ?? '—'}</span>
            <span>{formatBytes(file.size)}</span>
            <span>—</span>
          </button>
        ))}
      </div>
    </div>
  );
}
