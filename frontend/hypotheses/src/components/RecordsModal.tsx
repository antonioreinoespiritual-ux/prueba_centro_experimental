import React, { useMemo } from 'react';
import { Modal } from './Modal';
import { formatDate, fmtNumber } from '../utils/format';
import type { RecordApi } from '../utils/normalize';
import type { HypothesisCardData } from '../utils/filters';

interface RecordsModalProps {
  open: boolean;
  experiment: HypothesisCardData | null;
  records: RecordApi[];
  loading: boolean;
  onClose: () => void;
  onSelectRecord: (record: RecordApi) => void;
  onOpenFolders: () => void;
}

export function RecordsModal({
  open,
  experiment,
  records,
  loading,
  onClose,
  onSelectRecord,
  onOpenFolders,
}: RecordsModalProps) {
  const sortedRecords = useMemo(() => {
    return records.slice().sort((a, b) => String(b.created_at ?? '').localeCompare(String(a.created_at ?? '')));
  }, [records]);

  return (
    <Modal open={open} onClose={onClose} ariaLabelledBy="records-title">
      <div className="hyp-modal__header">
        <div>
          <div id="records-title" style={{ fontWeight: 600, fontSize: 18 }}>
            Records — {experiment?.project_name ?? 'Hipótesis'}
          </div>
          <div className="hyp-topbar__subtitle">{records.length} records</div>
        </div>
        <div className="hyp-actions">
          <button className="hyp-button" onClick={onOpenFolders} aria-label="Abrir carpetas de hipótesis">
            CARPETAS
          </button>
          <button className="hyp-button hyp-button--ghost" onClick={onClose} aria-label="Cerrar">
            Cerrar
          </button>
        </div>
      </div>
      <div className="hyp-modal__body">
        {loading && <div className="hyp-skeleton" style={{ height: 120 }} />}
        {!loading && sortedRecords.length === 0 && <div className="hyp-empty">Esta hipótesis no tiene records aún.</div>}
        {!loading && sortedRecords.length > 0 && (
          <div className="hyp-scroll-area">
            <table className="hyp-table">
              <thead>
                <tr>
                  <th>ID (Session)</th>
                  <th>Record</th>
                  <th>Métrica X</th>
                  <th>Proyecto</th>
                  <th>Status</th>
                  <th>Clicks</th>
                  <th>Views</th>
                  <th>Purchase</th>
                  <th>Created</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {sortedRecords.map((record) => (
                  <tr key={record.id} className="hyp-row" onClick={() => onSelectRecord(record)}>
                    <td>{record.session_id}</td>
                    <td>{record.record_name ?? '—'}</td>
                    <td>{experiment?.independent_variable ?? '—'}</td>
                    <td>{experiment?.project_name ?? '—'}</td>
                    <td>{record.record_status ?? 'collecting'}</td>
                    <td>{fmtNumber(record.clicks)}</td>
                    <td>{fmtNumber(record.views)}</td>
                    <td>{fmtNumber(record.purchase)}</td>
                    <td>{formatDate(record.created_at)}</td>
                    <td>{formatDate(record.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Modal>
  );
}
