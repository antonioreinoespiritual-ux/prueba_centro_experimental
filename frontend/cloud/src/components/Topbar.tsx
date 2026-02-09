import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

interface TopbarProps {
  onCreateFolder: () => void;
  onUploadFile: (file: File) => void;
}

export function Topbar({ onCreateFolder, onUploadFile }: TopbarProps) {
  const { selectedIds, viewMode, setViewMode } = useCloudStore();
  const hasSelection = selectedIds.length > 0;
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  return (
    <header className="cloud-topbar">
      <div className="cloud-topbar__brand">
        <div className="cloud-logo">
          <span className="cloud-logo__mark" />
          <span className="cloud-logo__text">Cloud Drive</span>
        </div>
        <div className="cloud-search">
          <span>🔍</span>
          <input placeholder="Buscar en Cloud Drive" aria-label="Buscar" />
        </div>
      </div>
      <div className="cloud-topbar__actions">
        <div className="cloud-topbar__group">
          <button className="cloud-btn cloud-btn--primary" onClick={onCreateFolder}>Nuevo</button>
          <button
            className="cloud-btn"
            onClick={() => fileInputRef.current?.click()}
          >
            Subir archivo
          </button>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) onUploadFile(file);
              event.currentTarget.value = '';
            }}
          />
          {hasSelection && (
            <>
              <button className="cloud-btn">Compartir</button>
              <button className="cloud-btn">Mover</button>
              <button className="cloud-btn">Renombrar</button>
              <button className="cloud-btn cloud-btn--danger">Borrar</button>
              <button className="cloud-btn">Descargar</button>
            </>
          )}
        </div>
        <div className="cloud-view-toggle" role="tablist">
          <button
            className={viewMode === 'list' ? 'active' : ''}
            onClick={() => setViewMode('list')}
            role="tab"
            aria-selected={viewMode === 'list'}
          >
            Lista
          </button>
          <button
            className={viewMode === 'grid' ? 'active' : ''}
            onClick={() => setViewMode('grid')}
            role="tab"
            aria-selected={viewMode === 'grid'}
          >
            Cuadrícula
          </button>
        </div>
      </div>
    </header>
  );
}
