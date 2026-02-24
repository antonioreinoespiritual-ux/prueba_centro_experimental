import React from 'react';
import type { HypothesisFilters } from '../utils/filters';

interface FiltersBarProps {
  filters: HypothesisFilters;
  projects: string[];
  metrics: string[];
  onChange: (next: HypothesisFilters) => void;
}

const orderOptions = [
  { value: 'updated_desc', label: 'Actualizado (desc)' },
  { value: 'created_desc', label: 'Creado (desc)' },
  { value: 'project_asc', label: 'Proyecto (A-Z)' },
];

export function FiltersBar({ filters, projects, metrics, onChange }: FiltersBarProps) {
  const update = (patch: Partial<HypothesisFilters>) => onChange({ ...filters, ...patch });

  return (
    <div className="hyp-filters" role="search" aria-label="Filtros de hipótesis">
      <div className="hyp-filters__row">
        <label className="hyp-field">
          Tipo de hipótesis
          <select value={filters.type} onChange={(event) => update({ type: event.target.value })}>
            <option value="">Todos</option>
            <option value="PROBLEM">Problema</option>
            <option value="CUSTOMER_SEGMENT">Cliente / Segmento</option>
            <option value="SOLUTION">Solución</option>
            <option value="VALUE">Valor</option>
            <option value="acquisition">Acquisition</option>
            <option value="activation">Activation</option>
            <option value="retention">Retention</option>
            <option value="monetization">Monetization</option>
            <option value="trust_credibility">Trust / Credibility</option>
            <option value="message_market_fit">Message-Market Fit</option>
            <option value="channel_fit">Channel Fit</option>
            <option value="pricing">Pricing</option>
            <option value="funnel_friction">Funnel Friction</option>
          </select>
        </label>
        <label className="hyp-field">
          Estado
          <select value={filters.status} onChange={(event) => update({ status: event.target.value })}>
            <option value="">Todos</option>
            <option value="draft">Draft</option>
            <option value="running">Running</option>
            <option value="validated">Validated</option>
            <option value="invalidated">Invalidated</option>
            <option value="pivot_candidate">Pivot Candidate</option>
            <option value="archived">Archived</option>
          </select>
        </label>
        <label className="hyp-field">
          Canal
          <select value={filters.channel} onChange={(event) => update({ channel: event.target.value })}>
            <option value="">Todos</option>
            <option value="paid">Paid</option>
            <option value="organic">Organic</option>
            <option value="live">Live</option>
            <option value="mixed">Mixed</option>
          </select>
        </label>
        <label className="hyp-field">
          Buscar
          <input
            placeholder="proyecto, hipótesis, variable..."
            value={filters.q}
            onChange={(event) => update({ q: event.target.value })}
          />
        </label>
      </div>
      <div className="hyp-filters__row">
        <label className="hyp-field">
          Proyecto
          <select value={filters.project} onChange={(event) => update({ project: event.target.value })}>
            <option value="">Todos</option>
            {projects.map((project) => (
              <option key={project} value={project}>
                {project}
              </option>
            ))}
          </select>
        </label>
        <label className="hyp-field">
          Métrica X
          <select value={filters.metric_x} onChange={(event) => update({ metric_x: event.target.value })}>
            <option value="">Todas</option>
            {metrics.map((metric) => (
              <option key={metric} value={metric}>
                {metric}
              </option>
            ))}
          </select>
        </label>
        <label className="hyp-field">
          Ordenar
          <select value={filters.order} onChange={(event) => update({ order: event.target.value })}>
            {orderOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
