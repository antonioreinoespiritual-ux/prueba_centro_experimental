import { useEffect, useMemo, useState } from 'react';
import { defaultFilters, filtersToSearchParams, normalizeFilters, HypothesisFilters } from '../utils/filters';

export function useUrlFilters(): [HypothesisFilters, (next: HypothesisFilters) => void] {
  const initial = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return { ...defaultFilters, ...normalizeFilters(params) };
  }, []);
  const [filters, setFilters] = useState<HypothesisFilters>(initial);

  useEffect(() => {
    const params = filtersToSearchParams(filters);
    const search = params.toString();
    const nextUrl = `${window.location.pathname}${search ? `?${search}` : ''}`;
    window.history.replaceState({}, '', nextUrl);
  }, [filters]);

  return [filters, setFilters];
}
