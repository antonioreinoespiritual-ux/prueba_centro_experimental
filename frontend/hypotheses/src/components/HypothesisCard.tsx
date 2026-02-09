import React from 'react';
import type { HypothesisCardData } from '../utils/filters';
import { formatDate } from '../utils/format';

interface HypothesisCardProps {
  data: HypothesisCardData;
  recordCount?: number;
  onOpenRecords: () => void;
  onOpenDoc: () => void;
  onOpenAi: () => void;
  onOpenAiFull: () => void;
  onHover?: () => void;
}

export function HypothesisCard({
  data,
  recordCount,
  onOpenRecords,
  onOpenDoc,
  onOpenAi,
  onOpenAiFull,
  onHover,
}: HypothesisCardProps) {
  return (
    <article className="hyp-card" onMouseEnter={onHover}>
      <div className="hyp-card__header">
        <div>
          <div className="hyp-card__title">{data.project_name}</div>
          <div className="hyp-meta" style={{ marginTop: 6 }}>
            <span className={`hyp-badge hyp-badge--${data.experiment_status}`}>{data.experiment_status}</span>
            <span className={`hyp-badge hyp-badge--${data.traffic_type}`}>{data.traffic_type}</span>
            <span className="hyp-pill">Hipótesis #{data.id}</span>
          </div>
        </div>
        <button className="hyp-button hyp-button--ghost" onClick={onOpenRecords} aria-label="Abrir records">
          Records {recordCount !== undefined ? `(${recordCount})` : ''}
        </button>
      </div>
      <div className="hyp-meta">
        {data.metric_x ? <span className="hyp-tag">Metric X: {data.metric_x}</span> : <span className="hyp-tag">Metric X: —</span>}
        {data.hypothesis_type && <span className="hyp-tag">{data.hypothesis_type}</span>}
        {data.primary_metric && <span className="hyp-tag">Y: {data.primary_metric}</span>}
        {data.independent_variable && <span className="hyp-tag">Variable: {data.independent_variable}</span>}
        {data.threshold_operator && data.threshold_value !== null && (
          <span className="hyp-tag">
            Umbral: {data.threshold_operator} {data.threshold_value}
            {data.threshold_type === 'percentage' ? '%' : ''}
          </span>
        )}
        {data.created_at && <span className="hyp-tag">Creado: {formatDate(data.created_at)}</span>}
        {data.updated_at && <span className="hyp-tag">Actualizado: {formatDate(data.updated_at)}</span>}
      </div>
      <div style={{ color: 'var(--hyp-text-muted)', fontSize: 13, lineHeight: 1.6 }}>
        {data.hypothesis || 'Sin hipótesis definida'}
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
      </div>
    </article>
  );
}
