export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  data?: any[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  business_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ChatResponse {
  message: string;
  operations_executed: unknown[];
  data_payload?: {
    added_items: any[];
    total_inventory: any[];
    queried_data?: any[];
  };
}

export interface TableSummary {
  name: string;
  created_at: string;
}

export interface ColumnMeta {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  unique: boolean;
}

export interface TableDetail {
  table: string;
  columns: ColumnMeta[];
  rows: Record<string, unknown>[];
  row_count: number;
}

export interface AlertRule {
  id: number;
  name: string;
  type: string;
  condition: string;
  threshold: number;
  is_active: boolean;
  created_at: string;
}

export interface Alert {
  id: number;
  rule_id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

export type ToastType = 'info' | 'success' | 'error';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}
