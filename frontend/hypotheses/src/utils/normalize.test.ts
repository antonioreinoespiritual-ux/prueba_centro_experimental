import { describe, expect, it } from 'vitest';
import { normalizeExperiment } from './normalize';

describe('normalizeExperiment', () => {
  it('fills defaults and derives metric_x', () => {
    const result = normalizeExperiment({
      id: 1,
      project_name: 'Proyecto Uno',
      hypothesis: null,
      traffic_type: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
      hypothesis_type: null,
      independent_variable: 'cta',
      metric_x: null,
      primary_metric: null,
      validation_threshold: null,
      threshold_value: null,
      threshold_type: null,
      threshold_operator: null,
      experiment_status: null,
      min_volume: null,
      volume_min_value: null,
      volume_unit: null,
      drive_folder_path: null,
    });

    expect(result.traffic_type).toBe('mixed');
    expect(result.experiment_status).toBe('draft');
    expect(result.metric_x).toBe('cta');
    expect(result.updated_at).toBe('2024-01-01T00:00:00Z');
  });
});
