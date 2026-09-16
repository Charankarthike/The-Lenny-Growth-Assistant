import axios from 'axios';
import type { Session, Message, Config } from './types';

const API_BASE_URL = '/api/v1';

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
  const { data } = await api.post(`/sessions/${sessionId}/messages`, {
    content,
    stream: false,
  });
  return data;
};

export const getMessages = async (sessionId: string): Promise<Message[]> => {
  const { data } = await api.get(`/sessions/${sessionId}/messages`);
  return data.messages || [];
};

export default api;
