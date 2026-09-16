"""
Transcript loader for various formats (JSON, Markdown, HTML, plain text).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from bs4 import BeautifulSoup
import markdown

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TranscriptData:
    """Data structure for a loaded transcript."""
    title: str
    full_text: str
    episode_number: Optional[int] = None
    guest_name: Optional[str] = None
    publish_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    url: Optional[str] = None


class TranscriptLoader:
    """Loader for transcript files in various formats."""
    
    def __init__(self, data_path: str):
        """
        Initialize the loader.
        
        Args:
            data_path: Path to the directory containing transcript files
        """
        self.data_path = Path(data_path)
        logger.info("transcript_loader_initialized", data_path=str(self.data_path))
    
    def load_json(self, file_path: Path) -> TranscriptData:
        """
        Load a transcript from a JSON file.
        
        Expected JSON structure:
        {
            "title": "Episode Title",
            "episode_number": 42,
            "guest_name": "Guest Name",
            "publish_date": "2023-01-15",
            "duration_minutes": 60,
            "transcript": "Full transcript text...",
            "summary": "Optional summary",
            "topics": ["topic1", "topic2"],
            "url": "https://..."
        }
        
        Args:
            file_path: Path to the JSON file
        
        Returns:
            TranscriptData object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse publish date if present
        publish_date = None
        if 'publish_date' in data and data['publish_date']:
            try:
                publish_date = datetime.fromisoformat(data['publish_date'])
            except (ValueError, TypeError):
                logger.warning("invalid_publish_date", file=str(file_path))
        
        return TranscriptData(
            title=data.get('title', 'Untitled'),
            full_text=data.get('transcript', data.get('full_text', '')),
            episode_number=data.get('episode_number'),
            guest_name=data.get('guest_name'),
            publish_date=publish_date,
            duration_minutes=data.get('duration_minutes'),
            summary=data.get('summary'),
            topics=data.get('topics'),
            url=data.get('url')
        )
    
    def load_markdown(self, file_path: Path) -> TranscriptData:
        """
        Load a transcript from a Markdown file.
        
        Expects front matter or headers for metadata:
        ---
        title: Episode Title
        episode: 42
        guest: Guest Name
        date: 2023-01-15
        ---
        
        Or extracts from H1/H2 headers.
        
        Args:
            file_path: Path to the Markdown file
        
        Returns:
            TranscriptData object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse front matter (YAML-like)
        metadata = self._extract_front_matter(content)
        
        # Remove front matter from content
        if metadata:
            content = self._remove_front_matter(content)
        
        # Convert markdown to plain text for full_text
        full_text = self._markdown_to_text(content)
        
        # Extract title from H1 if not in metadata
        title = metadata.get('title', self._extract_first_heading(content) or file_path.stem)
        
        # Parse date
        publish_date = None
        if 'date' in metadata:
            try:
                publish_date = datetime.fromisoformat(metadata['date'])
            except (ValueError, TypeError):
                pass
        
        return TranscriptData(
            title=title,
            full_text=full_text,
            episode_number=metadata.get('episode'),
            guest_name=metadata.get('guest'),
            publish_date=publish_date,
            duration_minutes=metadata.get('duration'),
            summary=metadata.get('summary'),
            topics=metadata.get('topics', '').split(',') if metadata.get('topics') else None,
            url=metadata.get('url')
        )
    
    def load_html(self, file_path: Path) -> TranscriptData:
        """
        Load a transcript from an HTML file.
        
        Args:
            file_path: Path to the HTML file
        
        Returns:
            TranscriptData object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title from <title> or <h1>
        title = None
        if soup.title:
            title = soup.title.string
        elif soup.h1:
            title = soup.h1.get_text()
        else:
            title = file_path.stem
        
        # Extract metadata from meta tags
        metadata = self._extract_html_metadata(soup)
        
        # Get main text content (remove scripts, styles)
        for script in soup(["script", "style"]):
            script.decompose()
        
        full_text = soup.get_text(separator='\n', strip=True)
        
        # Parse date from metadata
        publish_date = None
        if 'date' in metadata:
            try:
                publish_date = datetime.fromisoformat(metadata['date'])
            except (ValueError, TypeError):
                pass
        
        return TranscriptData(
            title=title,
            full_text=full_text,
            episode_number=metadata.get('episode'),
            guest_name=metadata.get('guest'),
            publish_date=publish_date,
            duration_minutes=metadata.get('duration'),
            summary=metadata.get('summary'),
            topics=metadata.get('topics', '').split(',') if metadata.get('topics') else None,
            url=metadata.get('url')
        )
    
    def load_text(self, file_path: Path) -> TranscriptData:
        """
        Load a transcript from a plain text file.
        
        Args:
            file_path: Path to the text file
        
        Returns:
            TranscriptData object with minimal metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to extract title from first line
        lines = content.split('\n')
        title = lines[0].strip() if lines else file_path.stem
        
        # If first line looks like a title (short, no punctuation), use rest as content
        if len(title) < 100 and not title.endswith('.'):
            full_text = '\n'.join(lines[1:]).strip()
        else:
            full_text = content
            title = file_path.stem
        
        return TranscriptData(
            title=title,
            full_text=full_text
        )
    
    def load_file(self, file_path: Path) -> Optional[TranscriptData]:
        """
        Load a transcript file, automatically detecting format.
        
        Args:
            file_path: Path to the transcript file
        
        Returns:
            TranscriptData object or None if format not supported
        """
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.json':
                return self.load_json(file_path)
            elif suffix in ['.md', '.markdown']:
                return self.load_markdown(file_path)
            elif suffix in ['.html', '.htm']:
                return self.load_html(file_path)
            elif suffix in ['.txt', '.text']:
                return self.load_text(file_path)
            else:
                logger.warning("unsupported_file_format", file=str(file_path), suffix=suffix)
                return None
        except Exception as e:
            logger.error("file_load_error", file=str(file_path), error=str(e))
            return None
    
    def load_all(self, pattern: str = "*") -> List[TranscriptData]:
        """
        Load all transcript files from the data directory.
        
        Args:
            pattern: Glob pattern for file matching (default: all files)
        
        Returns:
            List of TranscriptData objects
        """
        if not self.data_path.exists():
            logger.warning("data_path_not_found", path=str(self.data_path))
            return []
        
        transcripts = []
        supported_extensions = ['.json', '.md', '.markdown', '.html', '.htm', '.txt', '.text']
        
        for file_path in self.data_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                logger.info("loading_transcript_file", file=str(file_path))
                transcript = self.load_file(file_path)
                if transcript:
                    transcripts.append(transcript)
        
        logger.info("transcripts_loaded", count=len(transcripts))
        return transcripts
    
    # Helper methods
    
    @staticmethod
    def _extract_front_matter(content: str) -> Dict[str, Any]:
        """Extract YAML-like front matter from markdown."""
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter = parts[1].strip()
                for line in front_matter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
        return metadata
    
    @staticmethod
    def _remove_front_matter(content: str) -> str:
        """Remove front matter from markdown content."""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content
    
    @staticmethod
    def _markdown_to_text(content: str) -> str:
        """Convert markdown to plain text."""
        # Convert markdown to HTML
        html = markdown.markdown(content)
        # Remove HTML tags
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    
    @staticmethod
    def _extract_first_heading(content: str) -> Optional[str]:
        """Extract the first H1 heading from markdown."""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None
    
    @staticmethod
    def _extract_html_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML meta tags."""
        metadata = {}
        
        # Look for common meta tags
        meta_mappings = {
            'episode': ['episode', 'episode-number'],
            'guest': ['author', 'guest', 'guest-name'],
            'date': ['date', 'published', 'publish-date'],
            'summary': ['description', 'summary'],
            'url': ['url', 'canonical']
        }
        
        for key, names in meta_mappings.items():
            for name in names:
                meta = soup.find('meta', attrs={'name': name})
                if not meta:
                    meta = soup.find('meta', attrs={'property': f'og:{name}'})
                if meta and meta.get('content'):
                    metadata[key] = meta['content']
                    break
        
        return metadata
