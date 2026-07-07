export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const STORAGE_KEYS = {
  token: 'token',
  chats: 'ai-business-os-chats',
  activeChatId: 'ai-business-os-active-chat',
  sidebarCollapsed: 'ai-business-os-sidebar-collapsed',
  alertsEnabled: 'ai-business-os-alerts-enabled',
} as const;

export const SUGGESTION_CHIPS = [
  'Check inventory',
  'Create a products table',
  'Draft an invoice',
  'Add a new customer',
] as const;
