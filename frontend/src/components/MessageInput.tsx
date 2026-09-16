import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../store';
import './MessageInput.css';

const MessageInput: React.FC = () => {
  const [input, setInput] = useState('');
  const [rows, setRows] = useState(1);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { currentSession, sendMessage, isLoading } = useChatStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const newRows = Math.min(Math.ceil(scrollHeight / 24), 6);
      setRows(newRows);
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !currentSession || isLoading) return;

    const message = input.trim();
    setInput('');
    setRows(1);

    try {
      await sendMessage(message);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Optionally show error to user
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="message-input-container">
      <form onSubmit={handleSubmit} className="message-input-form">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            currentSession 
              ? "Type your message... (Shift+Enter for new line)" 
              : "Select or create a session to start chatting"
          }
          disabled={!currentSession || isLoading}
          rows={rows}
          className="message-textarea"
        />
        <button
          type="submit"
          disabled={!input.trim() || !currentSession || isLoading}
          className="send-button"
          aria-label="Send message"
        >
          {isLoading ? (
            <span className="loading-spinner">⏳</span>
          ) : (
            <span className="send-icon">➤</span>
          )}
        </button>
      </form>
      <div className="input-footer">
        <span className="input-hint">
          💡 Try: "What are key growth strategies?" or "Generate Ship 30 essay about retention"
        </span>
      </div>
    </div>
  );
};

export default MessageInput;
