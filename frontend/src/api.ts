import axios from 'axios';
import type { Session, Message, Config } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Config
export const getConfig = async (): Promise<Config> => {
  const { data } = await api.get('/config');
  return data;
};

// Sessions
export const createSession = async (title?: string): Promise<Session> => {
  const { data } = await api.post('/sessions', { title });
  return data;
};

export const listSessions = async (): Promise<Session[]> => {
  const { data } = await api.get('/sessions');
  return data.sessions;
};

export const getSession = async (sessionId: string): Promise<Session> => {
  const { data } = await api.get(`/sessions/${sessionId}`);
  return data;
};

export const deleteSession = async (sessionId: string): Promise<void> => {
  await api.delete(`/sessions/${sessionId}`);
};

// Messages
export const sendMessage = async (
  sessionId: string,
  content: string
): Promise<Message> => {
  const { data } = await api.post(`/chat`, {
    messages: [{ role: 'user', content }],
    stream: false,
  });
  return {
    id: Date.now().toString(),
    role: 'assistant',
    content: data.response,
    timestamp: new Date().toISOString(),
    sources: data.sources || [],
  };
};

export const getMessages = async (sessionId: string): Promise<Message[]> => {
  const { data } = await api.get(`/sessions/${sessionId}/messages`);
  return data.messages || [];
};

export default api;
