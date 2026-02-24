import { fetchJson, postJson } from './client';
import {
  experimentsSchema,
  recordsSchema,
  publicsSchema,
  documentationSchema,
  aiAnalysisSchema,
  aiHistorySchema,
} from './schemas';

export type EntityType = 'experiment' | 'record';
export type AiAnalysisType = 'metrics' | 'notes' | 'combined';

export async function fetchExperiments(limit = 5000) {
  return fetchJson(`/experiments/?limit=${limit}`, experimentsSchema);
}

export async function fetchRecords(experimentId: number, limit = 50000) {
  return fetchJson(`/records/?experiment_id=${experimentId}&limit=${limit}`, recordsSchema);
}

export async function fetchAllRecords(limit = 50000) {
  return fetchJson(`/records/?limit=${limit}`, recordsSchema);
}

export async function fetchPublics() {
  return fetchJson('/publics', publicsSchema);
}

export async function fetchDocumentation(entityType: EntityType, entityId: number) {
  return fetchJson(`/documentation/${entityType}/${entityId}`, documentationSchema);
}

export async function addDocumentationNote(entityType: EntityType, entityId: number, body: string) {
  return postJson(`/documentation/${entityType}/${entityId}/notes`, { body });
}

export async function runAiAnalysis(entityType: EntityType, entityId: number, type: AiAnalysisType) {
  return postJson(`/ai/analyze/${type}/${entityType}/${entityId}`, {}, aiAnalysisSchema);
}

export async function fetchAiHistory(entityType: EntityType, entityId: number, type: AiAnalysisType) {
  return fetchJson(`/ai/analysis/${entityType}/${entityId}?analysis_type=${type}`, aiHistorySchema);
}
