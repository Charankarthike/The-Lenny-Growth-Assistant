import { useChatStore } from '../store';
import { createSession, getMessages } from '../api';
import './SessionList.css';

const SessionList = () => {
  const {
    sessions,
    currentSession,
    setCurrentSession,
    addSession,
    setMessages,
    setLoading,
    setError,
  } = useChatStore();

  const handleCreateSession = async () => {
    try {
      setLoading(true);
      const session = await createSession('New Conversation');
      addSession(session);
      setCurrentSession(session);
      setMessages([]);
      setLoading(false);
    } catch (error) {
      console.error('Failed to create session:', error);
      setError('Failed to create session');
      setLoading(false);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    try {
      setLoading(true);
      const session = sessions.find((s) => s.session_id === sessionId);
      if (session) {
        setCurrentSession(session);
        const messages = await getMessages(sessionId);
        setMessages(messages);
      }
      setLoading(false);
    } catch (error) {
      console.error('Failed to load session:', error);
      setError('Failed to load session');
      setLoading(false);
    }
  };

  return (
    <div className="session-list">
      <div className="session-list-header">
        <h2>Conversations</h2>
        <button className="new-session-btn" onClick={handleCreateSession}>
          + New
        </button>
      </div>

      <div className="session-items">
        {sessions.length === 0 ? (
          <div className="empty-state">
            <p>No conversations yet</p>
            <p className="hint">Click "+ New" to start</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${
                currentSession?.session_id === session.session_id ? 'active' : ''
              }`}
              onClick={() => handleSelectSession(session.session_id)}
            >
              <div className="session-title">{session.title}</div>
              <div className="session-meta">
                {session.message_count} messages
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default SessionList;
