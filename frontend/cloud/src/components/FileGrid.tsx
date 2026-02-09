import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function FileGrid() {
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
          <div className="cloud-card__name">
            {getDisplayNameForItem(folder)}
            {getBadgeForItem(folder) && <span className="cloud-item__badge">{getBadgeForItem(folder)}</span>}
          </div>
          <div className="cloud-card__meta">Carpeta</div>
        </button>
      ))}
    </div>
  );
}
