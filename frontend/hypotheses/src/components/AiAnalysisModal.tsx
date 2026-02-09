import React, { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Modal } from './Modal';
import { fetchAiHistory, runAiAnalysis } from '../api/hypotheses';
import { formatAiOutput, formatDate } from '../utils/format';

interface AiAnalysisModalProps {
  open: boolean;
  entityType: 'experiment' | 'record' | null;
  entityId: number | null;
  analysisType: 'metrics' | 'notes' | 'combined' | null;
  title: string;
  onClose: () => void;
}

export function AiAnalysisModal({ open, entityType, entityId, analysisType, title, onClose }: AiAnalysisModalProps) {
  const [selectedOutput, setSelectedOutput] = useState<string | null>(null);
  const analysisMutation = useMutation({
    mutationFn: () => runAiAnalysis(entityType!, entityId!, analysisType!),
  });

  const historyQuery = useQuery({
    queryKey: ['ai-history', entityType, entityId, analysisType],
    queryFn: () => fetchAiHistory(entityType!, entityId!, analysisType!),
    enabled: open && !!entityType && !!entityId && !!analysisType,
  });

  useEffect(() => {
    if (open && entityType && entityId && analysisType) {
      setSelectedOutput(null);
      analysisMutation.mutate();
    }
  }, [open, entityType, entityId, analysisType]);

  const output = selectedOutput ?? analysisMutation.data?.output ?? '';

  return (
    <Modal open={open} onClose={onClose} ariaLabelledBy="ai-modal-title">
      <div className="hyp-modal__header">
        <div>
          <div id="ai-modal-title" style={{ fontWeight: 600, fontSize: 18 }}>
            Análisis IA — {title}
          </div>
          <div className="hyp-topbar__subtitle">Fuente: {analysisType}</div>
        </div>
        <div className="hyp-actions">
          <button
            className="hyp-button hyp-button--primary"
            onClick={() => analysisMutation.mutate()}
            disabled={analysisMutation.isPending}
            aria-label="Re-analizar"
          >
            {analysisMutation.isPending ? 'Analizando...' : 'Re-analizar'}
          </button>
          <button className="hyp-button hyp-button--ghost" onClick={onClose} aria-label="Cerrar">
            Cerrar
          </button>
        </div>
      </div>
      <div className="hyp-modal__body">
        {analysisMutation.isPending && <div className="hyp-skeleton" style={{ height: 140 }} />}
        {!analysisMutation.isPending && output && (
          <div className="hyp-ai-output" dangerouslySetInnerHTML={{ __html: formatAiOutput(output) }} />
        )}
        {!analysisMutation.isPending && !output && <div className="hyp-empty">Sin análisis disponible.</div>}
        {historyQuery.data?.length ? (
          <div style={{ marginTop: 20 }}>
            <div className="hyp-card__title">Historial de análisis</div>
            <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
                {historyQuery.data.map((item) => (
                  <button
                    key={item.id}
                    className="hyp-button"
                    style={{ textAlign: 'left' }}
                    onClick={() => setSelectedOutput(item.output)}
                    type="button"
                  >
                    {formatDate(item.created_at)} · {item.analysis_type} · ID: {item.id}
                  </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
