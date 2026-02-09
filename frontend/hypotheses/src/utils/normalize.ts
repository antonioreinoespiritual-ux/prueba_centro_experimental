import type { HypothesisCardData } from './filters';
import { z } from 'zod';
import { experimentSchema, recordSchema, publicSchema } from '../api/schemas';

export type ExperimentApi = z.infer<typeof experimentSchema>;
export type RecordApi = z.infer<typeof recordSchema>;
export type PublicApi = z.infer<typeof publicSchema>;

export function normalizeExperiment(exp: ExperimentApi): HypothesisCardData {
  return {
    id: exp.id,
    project_name: exp.project_name ?? 'Proyecto sin nombre',
    hypothesis: exp.hypothesis ?? null,
    hypothesis_type: exp.hypothesis_type ?? null,
    experiment_status: exp.experiment_status ?? 'draft',
    traffic_type: exp.traffic_type ?? 'mixed',
    primary_metric: exp.primary_metric ?? null,
    independent_variable: exp.independent_variable ?? null,
    metric_x: exp.metric_x ?? exp.independent_variable ?? null,
    threshold_operator: exp.threshold_operator ?? null,
    threshold_value: exp.threshold_value ?? null,
    threshold_type: exp.threshold_type ?? null,
    created_at: exp.created_at ?? null,
    updated_at: exp.updated_at ?? exp.created_at ?? null,
  };
}

export function normalizeExperiments(experiments: ExperimentApi[]): HypothesisCardData[] {
  return experiments.map(normalizeExperiment);
}

export function resolvePublic(record: RecordApi, publics: PublicApi[]) {
  const embedded = (record as RecordApi & { public?: PublicApi }).public;
  const resolved = embedded ?? (record.public_id ? publics.find((p) => p.id === record.public_id) : undefined);
  return {
    id: record.public_id ?? resolved?.id ?? null,
    name: record.publico ?? resolved?.name ?? 'Sin público',
    description: resolved?.description ?? null,
  };
}
