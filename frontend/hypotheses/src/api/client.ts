import { z } from 'zod';

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

export async function fetchJson<T>(input: string, schema?: z.ZodSchema<T>, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${input}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  const data = (await response.json()) as T;
  if (schema) {
    return schema.parse(data);
  }
  return data;
}

export async function postJson<T>(input: string, body: unknown, schema?: z.ZodSchema<T>): Promise<T> {
  return fetchJson(input, schema, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
