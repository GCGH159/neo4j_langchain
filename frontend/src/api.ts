import type { Session, Message, SSEChunk, DbStats, HealthStatus } from './types';

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API Error ${res.status}: ${err}`);
  }
  return res.json();
}

async function createSession(name?: string): Promise<Session> {
  return request<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

async function listSessions(): Promise<Session[]> {
  return request<Session[]>('/sessions');
}

async function renameSession(id: string, name: string): Promise<Session> {
  return request<Session>(`/sessions/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ name }),
  });
}

async function deleteSession(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/sessions/${id}`, { method: 'DELETE' });
}

async function getSessionMessages(id: string): Promise<Message[]> {
  return request<Message[]>(`/sessions/${id}/messages`);
}

async function chatStream(
  sessionId: string,
  message: string,
  onChunk: (chunk: SSEChunk) => void,
  onError: (error: Error) => void,
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!res.ok) {
      throw new Error(`Chat API Error: ${res.status}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6)) as SSEChunk;
            onChunk(data);
          } catch {
            // skip malformed SSE data
          }
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

async function getDbStats(): Promise<DbStats> {
  return request<DbStats>('/db/stats');
}

async function getDbSchema(): Promise<{ schema: string }> {
  return request<{ schema: string }>('/db/schema');
}

async function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health');
}

export const api = {
  createSession,
  listSessions,
  renameSession,
  deleteSession,
  getSessionMessages,
  chatStream,
  getDbStats,
  getDbSchema,
  getHealth,
};
