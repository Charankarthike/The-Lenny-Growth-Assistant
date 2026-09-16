import { useState, ReactNode } from 'react';
import { useChatStore } from '../store';
import SessionList from './SessionList';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { error, config } = useChatStore();

  return (
    <div className="layout">
      <header className="header">
        <h1>🚀 Lenny Growth Assistant</h1>
        {config && (
          <div className="model-indicator">
            Using: {config.model_name} ({config.model_provider})
          </div>
        )}
      </header>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      <div className="main-container">
        {sidebarOpen && (
          <aside className="sidebar">
            <SessionList />
          </aside>
        )}
        
        <main className="chat-container">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
