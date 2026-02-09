import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Modal } from './Modal';
import type { HypothesisCardData } from '../utils/filters';
import type { RecordApi, PublicApi } from '../utils/normalize';
import { fmtNumber, fmtFloat, fmtPercent, formatDate } from '../utils/format';
import { resolvePublic } from '../utils/normalize';
import { fetchDocumentation } from '../api/hypotheses';
import { computeCac, computeCpr, computeEngagement } from '../utils/metrics';

interface RecordDetailModalProps {
  open: boolean;
  record: RecordApi | null;
  experiment: HypothesisCardData | null;
  publics: PublicApi[];
  onClose: () => void;
  onOpenDoc: () => void;
  onOpenAi: () => void;
  onOpenAiFull: () => void;
  onOpenFolders: () => void;
}

type TabKey = 'context' | 'creative' | 'metrics' | 'notes';

export function RecordDetailModal({
  open,
  record,
  experiment,
  publics,
  onClose,
  onOpenDoc,
  onOpenAi,
  onOpenAiFull,
  onOpenFolders,
}: RecordDetailModalProps) {
  const [tab, setTab] = useState<TabKey>('context');
  const publicInfo = useMemo(() => (record ? resolvePublic(record, publics) : null), [record, publics]);
  const documentationQuery = useQuery({
    queryKey: ['documentation', 'record', record?.id],
    queryFn: () => fetchDocumentation('record', record!.id),
    enabled: open && !!record,
  });
  const engagement = record ? computeEngagement(record) : null;
  const cac = record ? computeCac(record) : null;
  const cpr = record ? computeCpr(record) : null;

  if (!record) return null;

  return (
    <Modal open={open} onClose={onClose} ariaLabelledBy="record-detail-title">
      <div className="hyp-modal__header">
        <div>
          <div id="record-detail-title" style={{ fontWeight: 600, fontSize: 18 }}>
            Record detalle — {record.record_name ?? record.session_id}
          </div>
          <div className="hyp-topbar__subtitle">Analiza el record sin salir de la hipótesis.</div>
        </div>
        <div className="hyp-actions">
          <button className="hyp-button" onClick={onOpenDoc} aria-label="Documentación">
            Documentación
          </button>
          <button className="hyp-button hyp-button--primary" onClick={onOpenAi} aria-label="Análisis IA">
            Análisis IA
          </button>
          <button className="hyp-button hyp-button--primary" onClick={onOpenAiFull} aria-label="Análisis IA Completo">
            Análisis IA Completo
          </button>
          <button className="hyp-button" onClick={onOpenFolders} aria-label="Abrir carpetas">
            CARPETAS
          </button>
          <button className="hyp-button hyp-button--ghost" onClick={onClose} aria-label="Cerrar">
            Cerrar
          </button>
        </div>
      </div>
      <div className="hyp-modal__body">
        <div className="hyp-tabs" role="tablist" aria-label="Secciones del record">
          <button className={`hyp-tab ${tab === 'context' ? 'active' : ''}`} onClick={() => setTab('context')}>
            Contexto
          </button>
          <button className={`hyp-tab ${tab === 'creative' ? 'active' : ''}`} onClick={() => setTab('creative')}>
            Creative
          </button>
          <button className={`hyp-tab ${tab === 'metrics' ? 'active' : ''}`} onClick={() => setTab('metrics')}>
            Métricas
          </button>
          <button className={`hyp-tab ${tab === 'notes' ? 'active' : ''}`} onClick={() => setTab('notes')}>
            Notas
          </button>
        </div>

        {tab === 'context' && (
          <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
            <div className="hyp-card">
              <div className="hyp-card__title">Contexto</div>
              <div className="hyp-meta">
                <span className="hyp-tag">Proyecto: {experiment?.project_name ?? '—'}</span>
                <span className="hyp-tag">Hipótesis: {experiment?.hypothesis ?? '—'}</span>
                <span className="hyp-tag">Tipo: {experiment?.hypothesis_type ?? '—'}</span>
                <span className="hyp-tag">Estado: {experiment?.experiment_status ?? '—'}</span>
                <span className="hyp-tag">Canal: {experiment?.traffic_type ?? '—'}</span>
                <span className="hyp-tag">Record creado: {formatDate(record.created_at)}</span>
              </div>
            </div>
            <div className="hyp-card">
              <div className="hyp-card__title">Público</div>
              <div className="hyp-meta">
                <span className="hyp-tag">Nombre: {publicInfo?.name ?? 'Sin público'}</span>
                <span className="hyp-tag">ID: {publicInfo?.id ?? '—'}</span>
              </div>
              <div style={{ color: 'var(--hyp-text-muted)', marginTop: 8 }}>
                {publicInfo?.description ?? '—'}
              </div>
            </div>
          </div>
        )}

        {tab === 'creative' && (
          <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
            <div className="hyp-card">
              <div className="hyp-card__title">Hook</div>
              <div className="hyp-meta">
                <span className="hyp-tag">{record.hook_text ?? '—'}</span>
                <span className="hyp-tag">{record.hook_type ?? '—'}</span>
              </div>
            </div>
            <div className="hyp-card">
              <div className="hyp-card__title">CTA</div>
              <div className="hyp-meta">
                <span className="hyp-tag">{record.cta_text ?? '—'}</span>
                <span className="hyp-tag">{record.cta_type ?? '—'}</span>
              </div>
            </div>
            <div className="hyp-card">
              <div className="hyp-card__title">Ejecución</div>
              <div className="hyp-meta">
                <span className="hyp-tag">{record.execution_type ?? '—'}</span>
                <span className="hyp-tag">{record.record_name ?? '—'}</span>
              </div>
            </div>
          </div>
        )}

        {tab === 'metrics' && (
          <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
            <div className="hyp-card">
              <div className="hyp-card__title">Métricas principales</div>
              <div className="hyp-meta">
                <span className="hyp-tag">Clicks: {fmtNumber(record.clicks)}</span>
                <span className="hyp-tag">Views: {fmtNumber(record.views)}</span>
                <span className="hyp-tag">CTR: {fmtPercent(record.ctr)}</span>
                <span className="hyp-tag">Purchase: {fmtNumber(record.purchase)}</span>
                <span className="hyp-tag">Initiate Checkout: {fmtNumber(record.initiate_checkouts)}</span>
                <span className="hyp-tag">Lead Form: {fmtNumber(record.lead_form)}</span>
                <span className="hyp-tag">Inicia Test: {fmtNumber(record.inicia_test)}</span>
                <span className="hyp-tag">Nuevos seguidores: {fmtNumber(record.live_new_followers)}</span>
              </div>
            </div>
            <div className="hyp-card">
              <div className="hyp-card__title">Engagement</div>
              <div className="hyp-meta">
                <span className="hyp-tag">Retención %: {fmtPercent(record.retention_pct)}</span>
                <span className="hyp-tag">Engagement %: {engagement ? fmtPercent(engagement) : '—'}</span>
                <span className="hyp-tag">Avg Watch Time: {fmtFloat(record.avg_watch_time)}</span>
                <span className="hyp-tag">Likes: {fmtNumber(record.likes)}</span>
                <span className="hyp-tag">Comentarios: {fmtNumber(record.comments)}</span>
                <span className="hyp-tag">Shares: {fmtNumber(record.shares)}</span>
                <span className="hyp-tag">Guardados: {fmtNumber(record.saves)}</span>
                <span className="hyp-tag">CPC: {fmtFloat(record.cpc)}</span>
                <span className="hyp-tag">CAC: {cac ? fmtFloat(cac, 2) : '—'}</span>
                <span className="hyp-tag">CPR: {cpr ? fmtFloat(cpr, 2) : '—'}</span>
              </div>
            </div>
          </div>
        )}

        {tab === 'notes' && (
          <div className="hyp-card" style={{ marginTop: 16 }}>
            <div className="hyp-card__title">Notas cualitativas</div>
            {documentationQuery.isLoading && <div style={{ color: 'var(--hyp-text-muted)' }}>Cargando notas...</div>}
            {!documentationQuery.isLoading && documentationQuery.data?.notes?.length ? (
              <div style={{ display: 'grid', gap: 8 }}>
                {documentationQuery.data.notes.map((note) => (
                  <div key={note.id} className="hyp-note">
                    <div>{note.body}</div>
                    <div className="hyp-note__meta">{formatDate(note.created_at)}</div>
                  </div>
                ))}
              </div>
            ) : (
              !documentationQuery.isLoading && <div style={{ color: 'var(--hyp-text-muted)' }}>Sin notas.</div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
