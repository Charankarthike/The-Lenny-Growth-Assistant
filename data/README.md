# Transcript Data Directory

This directory contains transcript data for Lenny's Podcast episodes.

## Structure

```
data/
├── transcripts/          # Raw transcript files
│   ├── sample_episode_001.json
│   └── sample_episode_002.json
├── embeddings/          # Generated embeddings (gitignored)
└── vector_store/        # Vector index files (gitignored)
```

## Supported Formats

The ingestion system supports multiple transcript formats:

### JSON Format (Recommended)

```json
{
  "title": "Episode Title",
  "episode_number": 42,
  "guest_name": "Guest Name",
  "publish_date": "2023-01-15",
  "duration_minutes": 60,
  "transcript": "Full transcript text...",
  "summary": "Optional episode summary",
  "topics": ["topic1", "topic2"],
  "url": "https://source-url.com"
}
```

### Markdown Format

```markdown
---
title: Episode Title
episode: 42
guest: Guest Name
date: 2023-01-15
---

# Episode Title

Full transcript content...
```

### HTML Format

HTML files with metadata in `<meta>` tags:

```html
<meta name="episode" content="42">
<meta name="guest" content="Guest Name">
<meta name="date" content="2023-01-15">
```

### Plain Text

Simple `.txt` files with title on first line (minimal metadata).

## Adding Transcripts

1. **Place transcript files in the `transcripts/` directory**
   - Supported extensions: `.json`, `.md`, `.markdown`, `.html`, `.htm`, `.txt`

2. **Run the ingestion script:**
   ```bash
   cd backend
   python scripts/ingest_transcripts.py
   ```

3. **Generate embeddings:**
   ```bash
   python scripts/generate_embeddings.py
   ```

## Sample Data

Two sample episodes are included for testing:

- **Episode 1**: Building Products That Users Love (Elena Verna)
  - Topics: product-market fit, retention, growth loops
  
- **Episode 2**: Pricing Strategy for B2B SaaS (Patrick Campbell)
  - Topics: pricing, value metrics, monetization

## Getting Real Transcripts

To populate with actual Lenny's Podcast transcripts:

1. **Official Sources**: Check if Lenny Rachitsky provides transcripts on his website or newsletter
2. **YouTube**: Many podcast episodes are on YouTube with auto-generated or manual transcripts
3. **Podcast Apps**: Some podcast apps (like Apple Podcasts) provide transcripts
4. **Transcription Services**: Use services like Otter.ai, Rev.com, or Descript to generate transcripts from audio

## Data Privacy

- Do not commit large transcript files to Git (use `.gitignore`)
- Respect copyright and usage rights for podcast content
- For production use, ensure you have permission to use the transcript data

## Database Storage

Once ingested, transcripts are stored in PostgreSQL:
- `transcripts` table: Full episodes with metadata
- `transcript_chunks` table: Chunked segments with embeddings for retrieval

Query the database to see ingested content:
```sql
SELECT COUNT(*) FROM transcripts;
SELECT COUNT(*) FROM transcript_chunks;
```
