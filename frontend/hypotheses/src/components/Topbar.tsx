import React from 'react';

interface TopbarProps {
  total: number;
}

export function Topbar({ total }: TopbarProps) {
  return (
    <header className="hyp-topbar">
      <div>
        <div className="hyp-topbar__title">Lista de Hipótesis</div>
        <div className="hyp-topbar__subtitle">Todas las hipótesis del centro experimental · {total} hipótesis</div>
      </div>
      <nav className="hyp-nav" aria-label="Navegación principal">
        <a className="hyp-link" href="/" aria-label="Formularios">
          Formularios
        </a>
        <a className="hyp-link" href="/static/dashboard.html" aria-label="Dashboard">
          Dashboard
        </a>
        <a className="hyp-link" href="/static/records.html" aria-label="Records">
          Records
        </a>
        <a className="hyp-link" href="/static/publics.html" aria-label="Públicos">
          Públicos
        </a>
      </nav>
    </header>
  );
}
