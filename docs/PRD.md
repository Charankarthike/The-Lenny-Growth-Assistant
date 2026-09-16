# Product Requirements Document: The Lenny Growth Assistant

## Forward Deployment Brief

### User and Problem

**Primary User:** Product managers, growth leads, and product marketers who need to make evidence-based decisions quickly.

**Job to be Done:** Extract actionable insights from Lenny Rachitsky's extensive podcast library to inform product strategy, growth experiments, and content creation—without manually reviewing hours of transcripts.

**Pain Removed:**
- **Time waste:** Searching through 200+ hours of content manually
- **Knowledge fragmentation:** Valuable insights buried across dozens of episodes
- **Context loss:** Difficulty connecting related concepts across episodes
- **Content creation bottleneck:** Need to produce Ship 30 for 30-style content grounded in expert advice

### Success Metrics

**Primary Product Metric:**
- **Answer Groundedness Rate:** ≥95% of assistant responses must cite specific transcript sources with verifiable claims

**Secondary Operational Metrics:**
- **Session Completion Rate:** ≥80% of sessions result in at least 3 conversational turns (indicates useful engagement)
- **Artifact Generation Success Rate:** ≥90% of requested artifacts render without errors
- **Response Latency (p95):** <5 seconds for conversational answers, <15 seconds for Ship 30 for 30 content
- **Local Model Viability:** Ollama responses must achieve ≥85% quality parity with cloud LLM responses (as measured by evaluator judgment)

### Key Assumptions

Because the client brief was incomplete, the following assumptions have been made:

1. **Transcript Access:** Lenny's Podcast transcripts are publicly available or provided. We'll use a sample dataset or scrape from publicly available sources.

2. **User Authentication:** Not required for MVP. The system is assumed to run in a trusted internal environment. Production deployment would add auth layers.

3. **Single-tenant deployment:** This is an internal tool for one organization, not a multi-tenant SaaS product.

4. **Transcript format:** Transcripts are in plain text or easily parseable format (Markdown, JSON, or HTML).

5. **Episode metadata:** Transcripts include guest name, episode title, and publication date for source attribution.

6. **Update cadence:** Transcript database is refreshed manually, not automatically synced with new episodes.

7. **Concurrent users:** System designed for 5-10 concurrent users maximum (small team usage).

8. **Content generation:** Ship 30 for 30 essays are for internal use and draft iteration, not final publication.

9. **Artifact security:** Generated HTML artifacts won't contain executable scripts or external resource loading for security.

10. **Model selection:** Evaluator has Ollama installed locally and can run models like Llama 3.1 8B or Mistral 7B comfortably.

### Scope Choices

#### ✅ **Included in Scope**

**Core Functionality:**
- RAG-powered conversational assistant with session context
- PostgreSQL persistence for conversations and metadata
- Dual LLM support: Cloud (Anthropic/OpenAI) and Local (Ollama)
- Transcript ingestion, chunking, and vector search
- Source citation and grounding validation
- Ship 30 for 30 content generation skill (1,250 words, formatted)
- In-app Artifact Viewer with secure HTML/Markdown rendering

**Infrastructure & Operations:**
- FastAPI backend with clear API contracts
- Docker Compose one-command startup
- Structured logging and error handling
- Health checks and graceful degradation
- Automated tests for critical paths
- Comprehensive handoff documentation

**User Experience:**
- Chat interface with session management
- Markdown rendering in chat
- Artifact panel with HTML sanitization
- Responsive layout (desktop-first)
- Basic accessibility (semantic HTML, keyboard navigation)

#### ❌ **Intentionally Excluded**

**Authentication & Authorization:**
- No user login, role-based access, or multi-tenancy
- **Rationale:** Internal tool assumption; adds complexity without clear requirement

**Real-time Collaboration:**
- No shared sessions or multi-user editing
- **Rationale:** Single-user sessions sufficient for MVP; costly to implement

**Advanced Agent Features:**
- No multi-agent orchestration, self-reflection loops, or tool use beyond retrieval and generation
- **Rationale:** Requirements specify skills-based routing, not complex agent architectures

**Automated Transcript Sync:**
- No automated scraping, RSS ingestion, or API polling
- **Rationale:** Manual refresh suitable for demo; production would add scheduling

**Mobile Optimization:**
- Desktop-optimized, mobile-responsive but not mobile-first
- **Rationale:** Primary users are knowledge workers at desks

**Advanced Search:**
- No faceted search, filtering by guest/date, or saved searches
- **Rationale:** Conversational interface is primary interaction; can be added later

**Production Infrastructure:**
- No Kubernetes, load balancing, CDN, or edge deployment
- **Rationale:** Local deployment requirement; production would containerize differently

### Risks and Trade-offs

#### 🔴 **High-Impact Risks**

**1. Hallucination and Grounding Failures**
- **Risk:** LLM generates plausible but incorrect answers not supported by transcripts
- **Mitigation:** 
  - Enforce citation requirements in system prompts
  - Retrieval score thresholds to trigger "I don't know" responses
  - Display source snippets alongside answers for user verification
  - Structured output validation
- **Residual Risk:** Medium. Cannot eliminate entirely; requires human judgment.

**2. Local Model Quality Degradation**
- **Risk:** Ollama models (7B-8B parameters) produce lower-quality, less coherent responses than Claude/GPT-4
- **Mitigation:**
  - Optimized prompts specifically for smaller models
  - Lower temperature settings to reduce variance
  - Fallback to simpler task decomposition
  - Clear UI indicator of which model is active
- **Residual Risk:** High. Smaller models will have quality differences; evaluator should test both.

**3. Artifact Rendering Security (XSS, Code Injection)**
- **Risk:** Generated HTML artifacts contain malicious scripts or load external resources
- **Mitigation:**
  - HTML sanitization using DOMPurify library
  - Content Security Policy headers restricting script execution
  - Sandboxed iframe rendering
  - No external resource loading (images, scripts, stylesheets)
- **Residual Risk:** Low. Industry-standard mitigations applied.

#### 🟡 **Medium-Impact Risks**

**4. Retrieval Relevance Failures**
- **Risk:** Vector search returns semantically similar but contextually irrelevant chunks
- **Mitigation:**
  - Hybrid search (vector + keyword BM25)
  - Chunk overlap to preserve context
  - Metadata filtering (guest name, topic tags if available)
  - Reranking step using LLM
- **Trade-off:** Slower retrieval (adds 200-500ms) but higher precision

**5. Response Latency**
- **Risk:** RAG pipeline (retrieve → rerank → generate) exceeds acceptable latency
- **Mitigation:**
  - Streaming responses for better perceived performance
  - Aggressive vector index optimization (HNSW)
  - Cached embeddings and compiled queries
  - Connection pooling for database
- **Trade-off:** Larger memory footprint (embedding model always loaded)

**6. Database Persistence Overhead**
- **Risk:** Saving every message adds latency and complicates error handling
- **Mitigation:**
  - Asynchronous persistence (write-behind pattern)
  - Retry logic with exponential backoff
  - Session creation decoupled from first message
- **Trade-off:** Possible data loss if server crashes before async write completes

#### 🟢 **Low-Impact Risks**

**7. Cost Overruns (Cloud LLM)**
- **Risk:** Extensive testing or long sessions rack up API costs
- **Mitigation:**
  - Usage logging and alerting
  - Rate limiting per session
  - Clear defaults to Ollama for demo
- **Residual Risk:** Low. Evaluator controls model selection.

**8. Transcript Data Quality**
- **Risk:** Transcripts contain errors, poor formatting, or incomplete speaker attribution
- **Mitigation:**
  - Data cleaning pipeline during ingestion
  - Manual review of sample transcripts
  - Fallback to "source unclear" if metadata missing
- **Residual Risk:** Medium. Data quality is upstream dependency.

**9. Browser Compatibility**
- **Risk:** Artifact viewer or UI components break in non-Chrome browsers
- **Mitigation:**
  - Modern browser targets (Chrome, Firefox, Safari latest versions)
  - Progressive enhancement approach
  - Polyfills for critical features
- **Residual Risk:** Low. Testing on latest browsers only.

---

## User Stories and Acceptance Criteria

### Epic 1: Conversational Assistant

**US-1.1: Ask Product/Growth Questions**
- **As a** product manager
- **I want to** ask natural language questions about product strategy and growth tactics
- **So that** I can get evidence-based answers from Lenny's expert interviews

**Acceptance Criteria:**
- [ ] User can type a question and receive a grounded answer within 5 seconds
- [ ] Answer cites specific episode and guest
- [ ] Answer includes relevant excerpt or quote from transcript
- [ ] System handles follow-up questions using session context
- [ ] If no relevant information exists, system responds "I don't have information about that in the available transcripts"

**US-1.2: Multi-turn Conversations**
- **As a** user
- **I want to** have back-and-forth conversations that build on previous context
- **So that** I can refine my questions without repeating background

**Acceptance Criteria:**
- [ ] System maintains conversation history within a session
- [ ] Pronouns and references resolved correctly ("Tell me more about that", "What else did they say?")
- [ ] Session persists in database for future review
- [ ] User can start a new session to clear context

### Epic 2: Ship 30 for 30 Content Generation

**US-2.1: Generate Formatted Essay**
- **As a** content creator
- **I want to** request a Ship 30 for 30-style essay on a specific topic
- **So that** I can produce skimmable, engaging content grounded in expert insights

**Acceptance Criteria:**
- [ ] Essay is ~1,250 words (±10%)
- [ ] Includes a strong hook in the first 2 sentences
- [ ] Uses clear headings and bullet points
- [ ] Employs selective bold emphasis for key concepts
- [ ] Ends with a specific, actionable takeaway
- [ ] All claims are grounded in transcript sources
- [ ] Sources are listed at the end

**US-2.2: Content Skill Routing**
- **As a** user
- **I want to** trigger the Ship 30 for 30 skill with specific phrasing
- **So that** the system understands my intent without complex commands

**Acceptance Criteria:**
- [ ] Phrases like "write a Ship 30 for 30 essay about…" trigger the skill
- [ ] Agent routes to content generation skill automatically
- [ ] Generated content appears as an artifact in the viewer
- [ ] User can regenerate with modifications

### Epic 3: Artifact Rendering

**US-3.1: View Markdown Artifacts**
- **As a** user
- **I want to** view generated Markdown documents in a rendered panel
- **So that** I can read formatted content without copying to another tool

**Acceptance Criteria:**
- [ ] Artifact viewer displays beside chat
- [ ] Markdown renders with proper headings, lists, bold, italics
- [ ] Code blocks are syntax-highlighted
- [ ] User can copy artifact to clipboard
- [ ] Artifact updates when new content is generated

**US-3.2: View HTML/CSS Artifacts**
- **As a** user
- **I want to** request HTML mockups or formatted visualizations
- **So that** I can see styled content directly in the app

**Acceptance Criteria:**
- [ ] HTML artifacts render in sandboxed iframe
- [ ] No JavaScript execution allowed
- [ ] No external resource loading (images, fonts, scripts)
- [ ] CSS styles are scoped to the artifact
- [ ] User warned if HTML is sanitized or blocked

### Epic 4: Model Configuration

**US-4.1: Switch Between Cloud and Local Models**
- **As an** evaluator
- **I want to** easily toggle between Anthropic/OpenAI and Ollama
- **So that** I can compare quality and validate local model performance

**Acceptance Criteria:**
- [ ] Configuration file or environment variable controls model selection
- [ ] UI displays which model is currently active
- [ ] System gracefully handles missing API keys (falls back to available model)
- [ ] Switching models does not lose session context
- [ ] README documents how to configure each option

**US-4.2: Ollama Integration**
- **As an** evaluator running the demo
- **I want to** use Ollama with a locally-running model
- **So that** I can validate the system without cloud dependencies

**Acceptance Criteria:**
- [ ] System connects to Ollama on default port (11434)
- [ ] Clear error message if Ollama is not running
- [ ] Supports models: Llama 3.1, Mistral, Phi-3
- [ ] Embedding model runs locally via Ollama or sentence-transformers
- [ ] Demo defaults to Ollama configuration

### Epic 5: Operational Readiness

**US-5.1: One-Command Startup**
- **As an** evaluator
- **I want to** start the entire system with a single command
- **So that** I can quickly test the application

**Acceptance Criteria:**
- [ ] `docker-compose up` starts backend, frontend, and PostgreSQL
- [ ] Health checks confirm all services are ready
- [ ] Sample transcripts are pre-loaded or loading is documented
- [ ] Frontend is accessible at http://localhost:3000
- [ ] Backend API is accessible at http://localhost:8000

**US-5.2: Observability and Debugging**
- **As a** client engineer
- **I want to** understand what the system is doing when errors occur
- **So that** I can troubleshoot and extend the solution

**Acceptance Criteria:**
- [ ] Structured JSON logs for all API requests
- [ ] Retrieval queries and results are logged
- [ ] LLM prompts and responses are logged (redacted if sensitive)
- [ ] Database queries are traced
- [ ] Clear error messages with correlation IDs
- [ ] Health endpoint reports component status

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)
1. Set up FastAPI backend structure
2. Configure PostgreSQL schema and migrations
3. Implement session and message persistence
4. Create health and status endpoints
5. Set up Docker Compose with all services

### Phase 2: Knowledge Base (Days 2-3)
6. Build transcript ingestion pipeline
7. Implement chunking strategy (overlap, metadata preservation)
8. Set up vector database or in-memory FAISS index
9. Create embedding generation workflow
10. Test retrieval quality with sample queries

### Phase 3: Agent Layer (Days 3-4)
11. Integrate Anthropic Claude Agent SDK
12. Implement conversational assistant skill
13. Build Ship 30 for 30 content generation skill
14. Create agent routing logic
15. Add source citation and grounding validation

### Phase 4: LLM Configuration (Day 4)
16. Build configuration layer for model switching
17. Integrate Anthropic/OpenAI cloud provider
18. Integrate Ollama local provider
19. Implement fallback and error handling
20. Test quality parity between models

### Phase 5: Frontend (Days 5-6)
21. Build React chat interface
22. Implement session management
23. Create Artifact Viewer component
24. Add HTML sanitization and sandboxing
25. Implement responsive layout
26. Add accessibility features

### Phase 6: Testing & Documentation (Day 6-7)
27. Write unit tests for backend
28. Write integration tests for RAG pipeline
29. Create manual test plan for UI
30. Complete README with setup instructions
31. Finalize PRD, architecture.md, design.md
32. Document agent transcripts

### Phase 7: Demo & Handoff (Day 7)
33. Record demo video
34. Final verification from fresh clone
35. Submit to evaluation form

---

## Open Questions for Client

1. **Transcript Access:** Do we have API access to Lenny's transcripts, or should we scrape from public sources?
2. **User Segmentation:** Are there different user roles (viewer vs. editor) or is everyone an admin?
3. **Content Sensitivity:** Are any episodes or topics considered sensitive and should be filtered?
4. **Deployment Target:** Is this intended to run on team members' laptops, a shared server, or eventually cloud infrastructure?
5. **Integration:** Does this need to integrate with existing tools (Slack, Notion, Google Docs)?

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-16  
**Author:** Forward Deployed Engineer Candidate
