import React from 'react';
import { Source } from '../types';
import './SourceDisplay.css';

interface SourceDisplayProps {
  sources: Source[];
}

const SourceDisplay: React.FC<SourceDisplayProps> = ({ sources }) => {
  const truncateText = (text: string, maxLength: number = 150) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + '...';
  };

  return (
    <div className="source-display">
      {sources.map((source, index) => (
        <div key={index} className="source-card">
          <div className="source-header">
            <span className="source-number">#{index + 1}</span>
            <span className="source-score" title="Relevance score">
              {(source.similarity_score * 100).toFixed(0)}% match
            </span>
          </div>
          
          <div className="source-content">
            <p className="source-text">{truncateText(source.content)}</p>
          </div>

          {source.metadata && (
            <div className="source-metadata">
              {source.metadata.episode_title && (
                <span className="metadata-item" title="Episode">
                  🎙️ {source.metadata.episode_title}
                </span>
              )}
              {source.metadata.episode_number && (
                <span className="metadata-item" title="Episode number">
                  Episode {source.metadata.episode_number}
                </span>
              )}
              {source.metadata.guest_name && (
                <span className="metadata-item" title="Guest">
                  👤 {source.metadata.guest_name}
                </span>
              )}
              {source.metadata.timestamp && (
                <span className="metadata-item" title="Timestamp">
                  ⏱️ {source.metadata.timestamp}
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default SourceDisplay;
