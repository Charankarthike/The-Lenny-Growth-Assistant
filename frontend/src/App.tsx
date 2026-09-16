import { useEffect } from 'react';
import { useChatStore } from './store';
import { getConfig, listSessions } from './api';
import Layout from './components/Layout';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const { setConfig, setSessions, setError, setLoading } = useChatStore();

  useEffect(() => {
    const initialize = async () => {
      try {
        setLoading(true);
        
        // Load config
        const config = await getConfig();
        setConfig(config);
        
        // Load sessions
        const sessions = await listSessions();
        setSessions(sessions);
        
        setLoading(false);
      } catch (error) {
        console.error('Failed to initialize:', error);
        setError('Failed to connect to backend. Please ensure the server is running.');
        setLoading(false);
      }
    };

    initialize();
  }, [setConfig, setSessions, setError, setLoading]);

  return (
    <Layout>
      <ChatInterface />
    </Layout>
  );
}

export default App;
