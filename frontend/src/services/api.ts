import { API_BASE_URL } from '../lib/constants';
import type { ChatResponse, TableDetail, Alert, AlertRule } from '../types';
import { supabase } from '../lib/supabase';

export function isAuthenticated(): boolean {
  return true;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
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
  getMe: () => request<{id: string, email: string, full_name: string, business_name: string}>('/auth/me'),
  
  updateProfile: (phone_number: string) => 
    request<{id: string, phone_number: string}>('/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number })
    }),

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
