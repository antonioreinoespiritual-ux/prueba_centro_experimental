import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

const MOCK_FILES = [
  { id: '1', name: 'Hipotesis_A.pdf', owner: 'Luna', size: '1.2 MB', date: '2024-02-09' },
  { id: '2', name: 'Record_23.csv', owner: 'Luna', size: '480 KB', date: '2024-02-08' },
];

export function FileList() {
  const { selectedIds, toggleSelection } = useCloudStore();

  return (
    <div className="cloud-table">
      <div className="cloud-table__header">
        <span>Nombre</span>
        <span>Propietario</span>
        <span>Tamaño</span>
        <span>Fecha</span>
      </div>
      <div className="cloud-table__body">
        {MOCK_FILES.map((file) => (
          <button
            key={file.id}
            className={`cloud-table__row ${selectedIds.includes(file.id) ? 'is-selected' : ''}`}
            onClick={() => toggleSelection(file.id)}
          >
            <span>{file.name}</span>
            <span>{file.owner}</span>
            <span>{file.size}</span>
            <span>{file.date}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
