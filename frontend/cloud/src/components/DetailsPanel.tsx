import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function DetailsPanel() {
  const { selectedIds } = useCloudStore();

  if (!selectedIds.length) {
    return (
      <aside className="cloud-detail">
        <div className="cloud-detail__header">Detalles</div>
        <div className="cloud-detail__body">Selecciona un elemento para ver los detalles.</div>
      </aside>
    );
  }

  return (
    <aside className="cloud-detail">
      <div className="cloud-detail__header">Detalles</div>
      <div className="cloud-detail__body">
        <div>
          <div className="cloud-detail__label">Seleccionados</div>
          <p>{selectedIds.length} elemento(s)</p>
        </div>
        <div>
          <div className="cloud-detail__label">Permisos</div>
          <p>Privado · Solo lectura</p>
        </div>
      </div>
    </aside>
  );
}
