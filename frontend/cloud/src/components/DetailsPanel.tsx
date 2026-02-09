import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function DetailsPanel() {
  const { selectedIds, items, getDisplayNameForItem, getBadgeForItem } = useCloudStore();

  if (!selectedIds.length) {
    return (
      <aside className="cloud-detail">
        <div className="cloud-detail__header">Detalles</div>
        <div className="cloud-detail__body">Selecciona un elemento para ver los detalles.</div>
      </aside>
    );
  }

  const selected = items.find((item) => item.id === selectedIds[0]);

  return (
    <aside className="cloud-detail">
      <div className="cloud-detail__header">Detalles</div>
      <div className="cloud-detail__body">
        <div>
          <div className="cloud-detail__label">Seleccionados</div>
          <p>{selectedIds.length} elemento(s)</p>
        </div>
        {selected && (
          <>
            <div>
              <div className="cloud-detail__label">Nombre</div>
              <p>
                {getDisplayNameForItem(selected)}{' '}
                {getBadgeForItem(selected) && <span className="cloud-item__badge">{getBadgeForItem(selected)}</span>}
              </p>
            </div>
            <div>
              <div className="cloud-detail__label">Tipo</div>
              <p>{selected.item_type}</p>
            </div>
          </>
        )}
        <div>
          <div className="cloud-detail__label">Permisos</div>
          <p>Privado · Solo lectura</p>
        </div>
      </div>
    </aside>
  );
}
