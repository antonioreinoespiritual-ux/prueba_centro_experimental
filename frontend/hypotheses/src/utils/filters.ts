export interface HypothesisFilters {
  project: string;
  status: string;
  channel: string;
  type: string;
  metric_x: string;
  q: string;
  order: string;
}

export const defaultFilters: HypothesisFilters = {
  project: '',
  status: '',
  channel: '',
  type: '',
  metric_x: '',
  q: '',
  order: 'updated_desc',
};

export function normalizeFilters(params: URLSearchParams): HypothesisFilters {
  return {
    project: params.get('project') ?? '',
    status: params.get('status') ?? '',
    channel: params.get('channel') ?? '',
    type: params.get('type') ?? '',
    metric_x: params.get('metric_x') ?? '',
    q: params.get('q') ?? '',
    order: params.get('order') ?? defaultFilters.order,
  };
}

export function filtersToSearchParams(filters: HypothesisFilters): URLSearchParams {
  const params = new URLSearchParams();
  (Object.keys(filters) as Array<keyof HypothesisFilters>).forEach((key) => {
    const value = filters[key];
    if (value) {
      params.set(key, value);
    }
  });
  return params;
}

export interface HypothesisCardData {
  id: number;
  project_name: string;
  hypothesis: string | null;
  hypothesis_type: string | null;
  experiment_status: string;
  traffic_type: string;
  primary_metric: string | null;
  independent_variable: string | null;
  metric_x: string | null;
  threshold_operator: string | null;
  threshold_value: number | null;
  threshold_type: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export function applyFilters(list: HypothesisCardData[], filters: HypothesisFilters): HypothesisCardData[] {
  const search = filters.q.trim().toLowerCase();
  let result = list.slice();
  if (filters.type) {
    result = result.filter((item) => item.hypothesis_type === filters.type);
  }
  if (filters.status) {
    result = result.filter((item) => item.experiment_status === filters.status);
  }
  if (filters.channel) {
    result = result.filter((item) => item.traffic_type === filters.channel);
  }
  if (filters.project) {
    result = result.filter((item) => item.project_name === filters.project);
  }
  if (filters.metric_x) {
    result = result.filter((item) => item.independent_variable === filters.metric_x);
  }
  if (search) {
    result = result.filter((item) => {
      const haystack = [
        item.project_name,
        item.hypothesis ?? '',
        item.independent_variable ?? '',
        item.primary_metric ?? '',
        item.hypothesis_type ?? '',
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(search);
    });
  }

  if (filters.order === 'updated_desc') {
    result.sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? ''));
  } else if (filters.order === 'created_desc') {
    result.sort((a, b) => (b.created_at ?? '').localeCompare(a.created_at ?? ''));
  } else if (filters.order === 'project_asc') {
    result.sort((a, b) => a.project_name.localeCompare(b.project_name, 'es'));
  }

  return result;
}
