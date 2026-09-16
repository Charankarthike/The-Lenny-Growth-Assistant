import React, { useState } from 'react';
import { Artifact } from '../types';
import './ArtifactViewer.css';

interface ArtifactViewerProps {
  artifact: Artifact;
}

const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getArtifactIcon = (type: string) => {
    switch (type) {
      case 'ship30_essay':
        return '✍️';
      case 'analysis':
        return '📊';
      case 'summary':
        return '📝';
      default:
        return '📄';
    }
  };

  const getArtifactTitle = () => {
    if (artifact.title) return artifact.title;
    
    switch (artifact.artifact_type) {
      case 'ship30_essay':
        return 'Ship 30 for 30 Essay';
      case 'analysis':
        return 'Analysis';
      case 'summary':
        return 'Summary';
      default:
        return 'Artifact';
    }
  };

  const renderContent = () => {
    const content = artifact.content;
    
    // Simple markdown-like rendering
    const lines = content.split('\n');
    return lines.map((line, index) => {
      if (line.startsWith('# ')) {
        return <h1 key={index} className="artifact-h1">{line.slice(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={index} className="artifact-h2">{line.slice(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={index} className="artifact-h3">{line.slice(4)}</h3>;
      }
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return <li key={index} className="artifact-li">{line.trim().slice(2)}</li>;
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index} className="artifact-p">{line}</p>;
    });
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
      // Optionally show success toast
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="artifact-viewer">
      <div className="artifact-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="artifact-title">
          <span className="artifact-icon">{getArtifactIcon(artifact.artifact_type)}</span>
          <span className="artifact-name">{getArtifactTitle()}</span>
          {artifact.metadata?.word_count && (
            <span className="artifact-meta">
              {artifact.metadata.word_count} words
            </span>
          )}
        </div>
        <button className="expand-button" aria-label={isExpanded ? 'Collapse' : 'Expand'}>
          <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
        </button>
      </div>

      {isExpanded && (
        <div className="artifact-body">
          <div className="artifact-content">
            {renderContent()}
          </div>
          
          <div className="artifact-actions">
            <button onClick={copyToClipboard} className="action-button">
              📋 Copy
            </button>
            {artifact.metadata?.topics && artifact.metadata.topics.length > 0 && (
              <div className="artifact-topics">
                {artifact.metadata.topics.map((topic: string, idx: number) => (
                  <span key={idx} className="topic-tag">{topic}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ArtifactViewer;
