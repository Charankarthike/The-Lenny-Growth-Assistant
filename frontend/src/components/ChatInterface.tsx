import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../store';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import './ChatInterface.css';

const ChatInterface: React.FC = () => {
  const { currentSession, messages, isLoading } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (!currentSession) {
    return (
      <div className="chat-interface-empty">
        <div className="empty-state">
          <h2>Welcome to The Lenny Growth Assistant</h2>
          <p>Create a new session or select an existing one to start chatting</p>
          <div className="features">
            <div className="feature">
              <span className="feature-icon">💬</span>
              <h3>Conversational Q&A</h3>
              <p>Ask questions about Lenny's podcast content</p>
            </div>
            <div className="feature">
              <span className="feature-icon">✍️</span>
              <h3>Ship 30 for 30</h3>
              <p>Generate atomic essays from episode insights</p>
            </div>
            <div className="feature">
              <span className="feature-icon">🔍</span>
              <h3>RAG-Powered</h3>
              <p>Answers grounded in transcript data</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>{currentSession.title}</h2>
        <span className="session-metadata">
          Created {new Date(currentSession.created_at).toLocaleDateString()}
        </span>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="no-messages">
            <p>Start a conversation by typing a message below</p>
            <div className="suggestions">
              <button className="suggestion">What are the key growth strategies discussed?</button>
              <button className="suggestion">Generate a Ship 30 for 30 essay about product-market fit</button>
              <button className="suggestion">Tell me about retention tactics</button>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        {isLoading && (
          <div className="loading-indicator">
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>Assistant is thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <MessageInput />
    </div>
  );
};

export default ChatInterface;
