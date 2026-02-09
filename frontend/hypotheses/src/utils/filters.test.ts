import { describe, expect, it } from 'vitest';
import { applyFilters, defaultFilters, HypothesisCardData } from './filters';

describe('applyFilters', () => {
  const items: HypothesisCardData[] = [
    {
      id: 1,
      project_name: 'Alpha',
      hypothesis: 'Test A',
      hypothesis_type: 'acquisition',
      experiment_status: 'running',
      traffic_type: 'paid',
      primary_metric: 'ctr',
      independent_variable: 'cta',
      metric_x: 'cta',
      threshold_operator: null,
      threshold_value: null,
      threshold_type: null,
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    },
    {
      id: 2,
      project_name: 'Beta',
      hypothesis: 'Test B',
      hypothesis_type: 'retention',
      experiment_status: 'validated',
      traffic_type: 'organic',
      primary_metric: 'purchase_rate',
      independent_variable: 'hook',
      metric_x: 'hook',
      threshold_operator: null,
      threshold_value: null,
      threshold_type: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
  ];

  it('filters by type and search', () => {
    const result = applyFilters(items, { ...defaultFilters, type: 'retention', q: 'beta' });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(2);
  });

  it('sorts by updated desc by default', () => {
    const result = applyFilters(items, { ...defaultFilters, q: '' });
    expect(result[0].id).toBe(1);
  });
});
