export function fmtNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return Math.abs(num) >= 1000 ? num.toLocaleString('es-ES') : String(num);
}

export function fmtFloat(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return num.toFixed(digits);
}

export function fmtPercent(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return `${num.toFixed(digits)}%`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('es-ES');
}

export function formatAiOutput(text: string) {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br />');
}
