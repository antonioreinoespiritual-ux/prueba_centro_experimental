import React from 'react';

const NAV_ITEMS = ['Mi unidad', 'Hipótesis', 'Records', 'Compartidos', 'Bibliotecas'];

export function Sidebar() {
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
      <div className="cloud-sidebar__card">
        <div className="cloud-sidebar__card-title">Stack de integración</div>
        <p>Seafile Server · Nextcloud · tusd · Casbin · Meilisearch · ONLYOFFICE</p>
      </div>
    </aside>
  );
}
