import { create } from 'zustand';
import { sendMessage as apiSendMessage } from './api';
import type { Session, Message, Config } from './types';

interface AppState {
  // Config
  config: Config | null;
  setConfig: (config: Config) => void;
  
  // Sessions
  sessions: Session[];
  currentSession: Session | null;
  setSessions: (sessions: Session[]) => void;
  setCurrentSession: (session: Session | null) => void;
  addSession: (session: Session) => void;
  removeSession: (sessionId: string) => void;
  
  // Messages
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  sendMessage: (content: string) => Promise<void>;
  
  // UI State
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Artifact viewer
  showArtifactViewer: boolean;
  currentArtifact: { content: string; type: 'markdown' | 'html' } | null;
  setShowArtifactViewer: (show: boolean) => void;
  setCurrentArtifact: (artifact: { content: string; type: 'markdown' | 'html' } | null) => void;
}

export const useChatStore = create<AppState>((set, get) => ({
  // Config
  config: null;
  setConfig: (config) => set({ config }),
  
  // Sessions
  sessions: [],
  currentSession: null,
  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (session) => set({ currentSession: session, messages: [] }),
  addSession: (session) => set((state) => ({ 
    sessions: [session, ...state.sessions] 
  })),
  removeSession: (sessionId) => set((state) => ({
    sessions: state.sessions.filter((s) => s.session_id !== sessionId),
    currentSession: state.currentSession?.session_id === sessionId ? null : state.currentSession,
  })),
  
  // Messages
  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  sendMessage: async (content: string) => {
    const { currentSession, addMessage, setLoading, setError } = get();
    if (!currentSession) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        message_id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
      };
      addMessage(userMessage);
      
      // Send to API
      const response = await apiSendMessage(currentSession.session_id, content);
      
      // Add assistant message
      const assistantMessage: Message = {
        id: response.message_id || Date.now().toString(),
        message_id: response.message_id,
        role: 'assistant',
        content: response.content,
        timestamp: response.created_at,
        created_at: response.created_at,
        sources: response.metadata?.sources,
        artifact: response.metadata?.artifacts?.[0],
        metadata: response.metadata,
      };
      addMessage(assistantMessage);
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message');
    } finally {
      setLoading(false);
    }
  },
  
  // UI State
  isLoading: false,
  error: null,
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  // Artifact viewer
  showArtifactViewer: false,
  currentArtifact: null,
  setShowArtifactViewer: (show) => set({ showArtifactViewer: show }),
  setCurrentArtifact: (artifact) => set({ currentArtifact: artifact }),
}));

// Also export as useStore for backwards compatibility
export const useStore = useChatStore;
