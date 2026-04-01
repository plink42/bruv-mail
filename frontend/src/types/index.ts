export interface IMAPAccount {
  id: number;
  host: string;
  username: string;
  last_uid: number;
  display_name?: string;
  is_active: boolean;
  created_at?: string;
}

export interface EmailMessage {
  id: number;
  account_id: number;
  message_id: string;
  subject?: string;
  from_addr?: string;
  to_addrs?: string;
  date?: string;
  body_text?: string;
  body_html?: string;
  tags: string[];
}

export interface Task {
  id: number;
  email_id: number;
  title: string;
  due_date?: string;
  status: 'open' | 'done' | 'dismissed';
  confidence: number;
  created_at: string;
}

export interface Tag {
  tag: string;
  count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuthToken {
  token: string;
  created_at: string;
  expires_at?: string;
  note?: string;
  is_revoked: boolean;
  source: 'env' | 'runtime';
}
