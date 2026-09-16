// API Types
export interface Session {
  session_id: string;
  created_at: string;
  updated_at: string;
  title: string;
  model_provider: string;
  model_name: string;
  message_count: number;
  is_active: boolean;
}

export interface Message {
  message_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  sources?: SourceReference[];
  artifacts?: ArtifactMetadata[];
  token_count?: number;
  processing_time_ms?: number;
}

export interface SourceReference {
  transcript_id: string;
  episode_number?: number;
  guest_name?: string;
  title: string;
  excerpt: string;
  relevance_score: number;
}

export interface ArtifactMetadata {
  artifact_id: string;
  artifact_type: 'markdown' | 'html' | 'json';
  title: string;
  word_count?: number;
}

export interface Config {
  model_provider: string;
  model_name: string;
  available_providers: string[];
  embedding_model: string;
  embedding_dimension: number;
  features: {
    streaming: boolean;
    artifact_generation: boolean;
    ship_30_for_30: boolean;
  };
}
