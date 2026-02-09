import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function Sidebar() {
  const { libraries, currentLibraryId, setCurrentLibrary, openProjectsRoot, openSystemFolder } = useCloudStore();
  const systemLibrary = libraries.find((library) => library.is_system || library.name === '_System');
  const personalLibrary = libraries.find((library) => !library.is_system && library.name !== '_System');
  return (
    <aside className="cloud-sidebar">
      <button className="cloud-btn cloud-btn--primary">+ Nuevo</button>
      <nav className="cloud-nav">
        <button
          className="cloud-nav__item"
          onClick={() => personalLibrary && setCurrentLibrary(personalLibrary.id, personalLibrary.name)}
        >
          Mi unidad
        </button>
        <button className="cloud-nav__item" onClick={() => openProjectsRoot()}>
          Proyectos
        </button>
        <button
          className="cloud-nav__item"
          onClick={() => systemLibrary && setCurrentLibrary(systemLibrary.id, systemLibrary.name)}
        >
          Sistema
        </button>
      </nav>
      <div className="cloud-sidebar__libraries">
        <div className="cloud-sidebar__card-title">Bibliotecas</div>
        {libraries.map((library) => (
          <button
            key={library.id}
            className={`cloud-nav__item ${currentLibraryId === library.id ? 'active' : ''}`}
            onClick={() => setCurrentLibrary(library.id)}
          >
            {library.name === '_System' ? 'Sistema' : library.name}
          </button>
        ))}
      </div>
      <div className="cloud-sidebar__card">
        <div className="cloud-sidebar__card-title">Stack de integración</div>
        <p>Seafile Server · Nextcloud · tusd · Casbin · Meilisearch · ONLYOFFICE</p>
      </div>
    </aside>
  );
}
