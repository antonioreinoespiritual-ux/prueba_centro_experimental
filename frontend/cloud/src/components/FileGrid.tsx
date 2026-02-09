import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

const MOCK_FOLDERS = [
  { id: 'lib-1', name: 'Hipótesis', meta: 'Biblioteca' },
  { id: 'lib-2', name: 'Records', meta: 'Biblioteca' },
];

export function FileGrid() {
  const { selectedIds, toggleSelection } = useCloudStore();

  return (
    <div className="cloud-grid">
      {MOCK_FOLDERS.map((folder) => (
        <button
          key={folder.id}
          className={`cloud-card ${selectedIds.includes(folder.id) ? 'is-selected' : ''}`}
          onClick={() => toggleSelection(folder.id)}
        >
          <div className="cloud-card__icon">📁</div>
          <div className="cloud-card__name">{folder.name}</div>
          <div className="cloud-card__meta">{folder.meta}</div>
        </button>
      ))}
    </div>
  );
}
