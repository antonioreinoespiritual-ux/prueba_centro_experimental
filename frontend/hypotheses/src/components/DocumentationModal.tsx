import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Modal } from './Modal';
import { addDocumentationNote, fetchDocumentation } from '../api/hypotheses';
import { formatDate } from '../utils/format';
import { useToast } from './Toast';

interface DocumentationModalProps {
  open: boolean;
  entityType: 'experiment' | 'record' | null;
  entityId: number | null;
  title: string;
  onClose: () => void;
  onOpenAiNotes: () => void;
}

export function DocumentationModal({ open, entityType, entityId, title, onClose, onOpenAiNotes }: DocumentationModalProps) {
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [note, setNote] = useState('');

  const documentationQuery = useQuery({
    queryKey: ['documentation', entityType, entityId],
    queryFn: () => fetchDocumentation(entityType!, entityId!),
    enabled: open && !!entityType && !!entityId,
  });

  const addMutation = useMutation({
    mutationFn: (body: string) => addDocumentationNote(entityType!, entityId!, body),
    onSuccess: () => {
      setNote('');
      queryClient.invalidateQueries({ queryKey: ['documentation', entityType, entityId] });
      showToast('Nota agregada');
    },
    onError: (error: Error) => {
      showToast(`Error al agregar nota: ${error.message}`, 'error');
    },
  });

  const handleAdd = () => {
    if (!note.trim()) {
      showToast('Escribe una nota antes de agregar.', 'error');
      return;
    }
    addMutation.mutate(note.trim());
  };

  return (
    <Modal open={open} onClose={onClose} ariaLabelledBy="doc-modal-title">
      <div className="hyp-modal__header">
        <div id="doc-modal-title" style={{ fontWeight: 600, fontSize: 18 }}>
          Documentación — {title}
        </div>
        <div className="hyp-actions">
          <button className="hyp-button hyp-button--primary" onClick={onOpenAiNotes} aria-label="Análisis IA (Notas)">
            Análisis IA (Notas)
          </button>
          <button className="hyp-button hyp-button--ghost" onClick={onClose} aria-label="Cerrar">
            Cerrar
          </button>
        </div>
      </div>
      <div className="hyp-modal__body">
        <div className="hyp-card" style={{ marginBottom: 16 }}>
          <label className="hyp-field" style={{ width: '100%' }}>
            Nueva nota
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Escribe una nueva nota cualitativa..."
              style={{
                minHeight: 120,
                resize: 'vertical',
                background: 'var(--hyp-surface-2)',
                color: 'var(--hyp-text)',
                border: '1px solid var(--hyp-border)',
                borderRadius: 10,
                padding: 12,
              }}
            />
          </label>
          <button className="hyp-button" onClick={handleAdd} disabled={addMutation.isPending}>
            {addMutation.isPending ? 'Guardando...' : 'Agregar Nota'}
          </button>
        </div>
        {documentationQuery.isLoading && <div className="hyp-skeleton" style={{ height: 120 }} />}
        {!documentationQuery.isLoading && documentationQuery.data?.notes?.length ? (
          documentationQuery.data.notes.map((noteItem) => (
            <div key={noteItem.id} className="hyp-note">
              <div>{noteItem.body}</div>
              <div className="hyp-note__meta">
                {formatDate(noteItem.created_at)}
                {noteItem.updated_at ? ` (editada: ${formatDate(noteItem.updated_at)})` : ''}
              </div>
            </div>
          ))
        ) : (
          !documentationQuery.isLoading && <div className="hyp-empty">No hay notas de documentación aún.</div>
        )}
      </div>
    </Modal>
  );
}
