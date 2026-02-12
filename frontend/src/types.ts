export interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface SSEChunk {
  type: 'content' | 'done' | 'error';
  content: string;
}

export interface DbStats {
  labels: string[];
  relationship_types: string[];
  node_counts: Record<string, number>;
  total_relationships: number;
}

export interface HealthStatus {
  status: string;
  neo4j: boolean;
  llm_model: string;
}
