import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

const NAV_ITEMS = ['Mi unidad', 'Hipótesis', 'Records', 'Compartidos', 'Bibliotecas'];

export function Sidebar() {
  const { libraries, currentLibraryId, setCurrentLibrary } = useCloudStore();
  return (
    <aside className="cloud-sidebar">
      <button className="cloud-btn cloud-btn--primary">+ Nuevo</button>
      <nav className="cloud-nav">
        {NAV_ITEMS.map((item) => (
          <button key={item} className="cloud-nav__item">
            {item}
          </button>
        ))}
      </nav>
      <div className="cloud-sidebar__libraries">
        <div className="cloud-sidebar__card-title">Bibliotecas</div>
        {libraries.map((library) => (
          <button
            key={library.id}
            className={`cloud-nav__item ${currentLibraryId === library.id ? 'active' : ''}`}
            onClick={() => setCurrentLibrary(library.id)}
          >
            {library.name}
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
