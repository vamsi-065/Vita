import { API_BASE_URL } from '../lib/constants';
import type { ChatResponse, TableDetail, Alert, AlertRule } from '../types';

export function isAuthenticated(): boolean {
  return true;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(typeof detail === 'string' ? detail : 'Request failed');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  getMe: () => Promise.resolve({ id: '1', email: 'open@business.os', full_name: 'Open User', business_name: 'Vita' }),

  sendChat: (message: string) =>
    request<ChatResponse>('/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    }),

  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<ChatResponse>('/chat/upload', {
      method: 'POST',
      body: formData,
    });
  },

  getTables: () =>
    request<{ tables: { name: string; created_at: string }[] }>('/tables/'),

  getTable: (name: string) => request<TableDetail>(`/tables/${name}`),

  cleanDatabase: () => request<{ status: string; message: string }>('/tables/clean', { method: 'POST' }),

  getAlerts: () => request<Alert[]>('/alerts/'),

  getAlertRules: () => request<AlertRule[]>('/alerts/rules'),

  createAlertRule: (rule: {
    name: string;
    type: string;
    condition: string;
    threshold: number;
    is_active: boolean;
  }) =>
    request<AlertRule>('/alerts/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rule),
    }),
};
