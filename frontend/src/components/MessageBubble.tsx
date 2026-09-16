import React, { useState } from 'react';
import { Message } from '../types';
import SourceDisplay from './SourceDisplay';
import ArtifactViewer from './ArtifactViewer';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderContent = () => {
    // Simple markdown-like formatting
    const lines = message.content.split('\n');
    return lines.map((line, index) => {
      // Headers
      if (line.startsWith('# ')) {
        return <h1 key={index}>{line.slice(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={index}>{line.slice(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={index}>{line.slice(4)}</h3>;
      }
      
      // Lists
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return <li key={index}>{line.trim().slice(2)}</li>;
      }
      if (/^\d+\.\s/.test(line.trim())) {
        return <li key={index}>{line.trim().replace(/^\d+\.\s/, '')}</li>;
      }
      
      // Code blocks (simple detection)
      if (line.trim().startsWith('```')) {
        return null; // Handle in a more sophisticated way if needed
      }
      
      // Paragraphs
      if (line.trim() === '') {
        return <br key={index} />;
      }
      
      return <p key={index}>{line}</p>;
    });
  };

  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-header">
        <span className="message-role">
          {isUser ? '👤 You' : '🤖 Assistant'}
        </span>
        <span className="message-timestamp">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>

      <div className="message-content">
        {renderContent()}
      </div>

      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          <button 
            className="sources-toggle"
            onClick={() => setShowSources(!showSources)}
          >
            📚 {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            <span className={`toggle-icon ${showSources ? 'open' : ''}`}>▼</span>
          </button>
          {showSources && <SourceDisplay sources={message.sources} />}
        </div>
      )}

      {message.artifact && (
        <div className="message-artifact">
          <ArtifactViewer artifact={message.artifact} />
        </div>
      )}

      {message.metadata?.skill && (
        <div className="message-metadata">
          <span className="skill-badge">
            {message.metadata.skill === 'ship30' ? '✍️ Ship 30 for 30' : '💬 Q&A'}
          </span>
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
