import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useVirtualizer } from '@tanstack/react-virtual';
import { fetchAllRecords, fetchExperiments, fetchPublics, fetchRecords } from './api/hypotheses';
import { FiltersBar } from './components/FiltersBar';
import { HypothesisCard } from './components/HypothesisCard';
import { Topbar } from './components/Topbar';
import { useDebouncedValue } from './hooks/useDebouncedValue';
import { useUrlFilters } from './hooks/useUrlFilters';
import { applyFilters, HypothesisFilters } from './utils/filters';
import { normalizeExperiments } from './utils/normalize';
import { ToastProvider, useToast } from './components/Toast';
import { RecordsModal } from './components/RecordsModal';
import { RecordDetailModal } from './components/RecordDetailModal';
import { DocumentationModal } from './components/DocumentationModal';
import { AiAnalysisModal } from './components/AiAnalysisModal';
import type { RecordApi } from './utils/normalize';

function HypothesesApp() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [filters, setFilters] = useUrlFilters();
  const [recordsOpen, setRecordsOpen] = useState(false);
  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<RecordApi | null>(null);
  const [docState, setDocState] = useState<{ type: 'experiment' | 'record'; id: number; title: string } | null>(null);
  const [aiState, setAiState] = useState<{
    type: 'experiment' | 'record';
    id: number;
    analysisType: 'metrics' | 'notes' | 'combined';
    title: string;
  } | null>(null);

  const debouncedSearch = useDebouncedValue(filters.q, 300);

  const experimentsQuery = useQuery({
    queryKey: ['experiments'],
    queryFn: () => fetchExperiments(),
  });

  const publicsQuery = useQuery({
    queryKey: ['publics'],
    queryFn: () => fetchPublics(),
  });

  const allRecordsQuery = useQuery({
    queryKey: ['records', 'all'],
    queryFn: () => fetchAllRecords(),
  });

  useEffect(() => {
    if (experimentsQuery.error instanceof Error) {
      showToast(`Error cargando hipótesis: ${experimentsQuery.error.message}`, 'error');
    }
  }, [experimentsQuery.error, showToast]);

  const normalized = useMemo(() => normalizeExperiments(experimentsQuery.data ?? []), [experimentsQuery.data]);
  const mergedFilters = useMemo(() => ({ ...filters, q: debouncedSearch }), [filters, debouncedSearch]);
  const filtered = useMemo(() => applyFilters(normalized, mergedFilters), [normalized, mergedFilters]);

  const availableProjects = useMemo(() => {
    return Array.from(new Set(normalized.map((item) => item.project_name).filter(Boolean))).sort((a, b) =>
      a.localeCompare(b, 'es'),
    );
  }, [normalized]);

  const availableMetrics = useMemo(() => {
    const project = filters.project;
    const list = project ? normalized.filter((item) => item.project_name === project) : normalized;
    return Array.from(new Set(list.map((item) => item.independent_variable).filter(Boolean))).sort((a, b) =>
      a.localeCompare(b, 'es'),
    );
  }, [filters.project, normalized]);

  const recordCountMap = useMemo(() => {
    const map = new Map<number, number>();
    (allRecordsQuery.data ?? []).forEach((record) => {
      map.set(record.experiment_id, (map.get(record.experiment_id) ?? 0) + 1);
    });
    return map;
  }, [allRecordsQuery.data]);

  const selectedExperiment = useMemo(
    () => normalized.find((item) => item.id === selectedExperimentId) ?? null,
    [normalized, selectedExperimentId],
  );

  const recordsQuery = useQuery({
    queryKey: ['records', selectedExperimentId],
    queryFn: () => fetchRecords(selectedExperimentId!),
    enabled: !!selectedExperimentId && recordsOpen,
  });

  const listRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: filtered.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => 220,
    overscan: 6,
  });

  const handleFiltersChange = (next: HypothesisFilters) => {
    setFilters(next);
  };

  const openRecords = (experimentId: number) => {
    setSelectedExperimentId(experimentId);
    setRecordsOpen(true);
  };

  const closeRecords = () => {
    setRecordsOpen(false);
    setSelectedRecord(null);
  };

  const openRecordDetail = (record: RecordApi) => {
    setSelectedRecord(record);
  };

  const closeRecordDetail = () => setSelectedRecord(null);

  const openDoc = (type: 'experiment' | 'record', id: number, title: string) => {
    setDocState({ type, id, title });
  };

  const openAi = (type: 'experiment' | 'record', id: number, analysisType: 'metrics' | 'notes' | 'combined', title: string) => {
    setAiState({ type, id, analysisType, title });
  };

  const openFolders = (type: 'experiment' | 'record', id: number, title: string) => {
    window.open(`/cloud?type=${type}&id=${id}&name=${encodeURIComponent(title)}`, '_blank');
  };

  return (
    <div className="hyp-app">
      <Topbar total={filtered.length} />
      <main className="hyp-main">
        <FiltersBar filters={filters} projects={availableProjects} metrics={availableMetrics} onChange={handleFiltersChange} />
        <div className="hyp-list">
          {experimentsQuery.isLoading && (
            <>
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="hyp-skeleton" />
              ))}
            </>
          )}
          {!experimentsQuery.isLoading && filtered.length === 0 && (
            <div className="hyp-empty">No se encontraron hipótesis con estos filtros.</div>
          )}
          {!experimentsQuery.isLoading && filtered.length > 0 && (
            <div className="hyp-list__viewport" ref={listRef}>
              <div style={{ height: rowVirtualizer.getTotalSize(), position: 'relative' }}>
                {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                  const item = filtered[virtualRow.index];
                  return (
                    <div
                      key={item.id}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        transform: `translateY(${virtualRow.start}px)`,
                        paddingBottom: 12,
                      }}
                    >
                      <HypothesisCard
                        data={item}
                        recordCount={recordCountMap.get(item.id)}
                        onOpenRecords={() => openRecords(item.id)}
                        onOpenDoc={() => openDoc('experiment', item.id, item.project_name)}
                        onOpenAi={() => openAi('experiment', item.id, 'metrics', item.project_name)}
                        onOpenAiFull={() => openAi('experiment', item.id, 'combined', item.project_name)}
                        onHover={() =>
                          queryClient.prefetchQuery({
                            queryKey: ['records', item.id],
                            queryFn: () => fetchRecords(item.id),
                          })
                        }
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </main>

      <RecordsModal
        open={recordsOpen}
        experiment={selectedExperiment}
        records={recordsQuery.data ?? []}
        loading={recordsQuery.isLoading}
        onClose={closeRecords}
        onSelectRecord={openRecordDetail}
        onOpenFolders={() => {
          if (selectedExperiment) {
            openFolders('experiment', selectedExperiment.id, selectedExperiment.project_name);
          }
        }}
      />

      <RecordDetailModal
        open={!!selectedRecord}
        record={selectedRecord}
        experiment={selectedExperiment}
        publics={publicsQuery.data ?? []}
        onClose={closeRecordDetail}
        onOpenDoc={() => selectedRecord && openDoc('record', selectedRecord.id, selectedRecord.record_name ?? selectedRecord.session_id)}
        onOpenAi={() => selectedRecord && openAi('record', selectedRecord.id, 'metrics', selectedRecord.record_name ?? selectedRecord.session_id)}
        onOpenAiFull={() => selectedRecord && openAi('record', selectedRecord.id, 'combined', selectedRecord.record_name ?? selectedRecord.session_id)}
        onOpenFolders={() => selectedRecord && openFolders('record', selectedRecord.id, selectedRecord.record_name ?? selectedRecord.session_id)}
      />

      <DocumentationModal
        open={!!docState}
        entityType={docState?.type ?? null}
        entityId={docState?.id ?? null}
        title={docState?.title ?? ''}
        onClose={() => setDocState(null)}
        onOpenAiNotes={() => {
          if (docState) {
            setDocState(null);
            openAi(docState.type, docState.id, 'notes', docState.title);
          }
        }}
      />

      <AiAnalysisModal
        open={!!aiState}
        entityType={aiState?.type ?? null}
        entityId={aiState?.id ?? null}
        analysisType={aiState?.analysisType ?? null}
        title={aiState?.title ?? ''}
        onClose={() => setAiState(null)}
      />
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <HypothesesApp />
    </ToastProvider>
  );
}
