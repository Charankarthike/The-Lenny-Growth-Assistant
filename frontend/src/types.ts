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
  id: string;
  message_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  created_at: string;
  sources?: Source[];
  artifact?: Artifact;
  metadata?: MessageMetadata;
}

export interface Source {
  content: string;
  similarity_score: number;
  metadata?: {
    episode_title?: string;
    episode_number?: number;
    guest_name?: string;
    timestamp?: string;
  };
}

export interface Artifact {
  artifact_id: string;
  artifact_type: string;
  title?: string;
  content: string;
  metadata?: {
    word_count?: number;
    topics?: string[];
  };
}

export interface MessageMetadata {
  skill?: string;
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
