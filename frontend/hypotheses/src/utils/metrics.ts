import type { RecordApi } from './normalize';

export function computeEngagement(record: RecordApi) {
  const views = record.views ?? 0;
  const total = (record.likes ?? 0) + (record.comments ?? 0) + (record.shares ?? 0) + (record.saves ?? 0);
  if (!views) return null;
  return (total / views) * 100;
}

export function computeSpend(record: RecordApi) {
  if (record.cpc === null || record.cpc === undefined) return null;
  const clicks = record.clicks ?? 0;
  return record.cpc * clicks;
}

export function computeCac(record: RecordApi) {
  if (!record.purchase) return null;
  const spend = computeSpend(record);
  if (!spend) return null;
  return spend / record.purchase;
}

export function computeCpr(record: RecordApi) {
  if (!record.clicks) return null;
  const spend = computeSpend(record);
  if (!spend) return null;
  return spend / record.clicks;
}
