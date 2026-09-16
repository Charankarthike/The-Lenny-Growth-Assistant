import { create } from 'zustand';
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

export const useStore = create<AppState>((set) => ({
  // Config
  config: null,
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
