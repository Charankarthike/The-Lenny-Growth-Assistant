# Agent Transcript: Initial Planning and Architecture

**Date:** 2026-09-16  
**Phase:** Planning and Architecture  
**Session:** Initial project setup and documentation creation

---

## Session Summary

This session focused on understanding the Forward Deployed Engineer take-home assignment requirements and creating the foundational documentation structure. The goal was to establish clear architectural boundaries, design principles, and implementation plans before writing any code.

## Key Decisions

### [DECISION 1] Documentation-First Approach

**Context:** The assignment emphasizes deployment readiness and handoff quality.

**Decision:** Create comprehensive PRD, architecture.md, and design.md documents before any implementation.

**Rationale:**
- Forward deployment role requires strong documentation and communication skills
- Writing docs first forces architectural clarity and prevents scope creep
- Evaluators can understand system design before reviewing code
- Acts as a contract for what will be built

**Alternative Considered:** Start coding immediately, document later  
**Why Rejected:** Risk of accumulating technical debt and unclear boundaries

---

### [DECISION 2] PostgreSQL + pgvector vs. Separate Vector Database

**Context:** RAG system requires both relational data (sessions, messages) and vector embeddings.

**Decision:** Use PostgreSQL with pgvector extension instead of separate vector database (Pinecone, Qdrant, Weaviate).

**Rationale:**
- **Simplicity:** One database to manage, deploy, and monitor
- **Local deployment:** No cloud dependencies or API keys required
- **ACID guarantees:** Transactions across relational and vector data
- **Cost:** No additional infrastructure or licensing
- **Developer experience:** Familiar SQL interface

**Trade-offs:**
- Vector search performance: pgvector slower than specialized vector DBs at large scale (1M+ vectors)
- Scaling: More complex to scale horizontally compared to managed vector DB
- Features: No advanced features like real-time updates or multi-tenancy primitives

**Mitigation:**
- For MVP with ~100-200 episodes (~10K chunks), performance is adequate
- IVFFlat indexing provides fast approximate nearest neighbor search
- Can migrate to dedicated vector DB later if needed (abstraction layer helps)

**Benchmark Data (Estimated):**
- pgvector on MacBook: ~50-100ms for top-K search with 10K vectors
- Pinecone: ~20-30ms for same query
- **Conclusion:** Acceptable latency for demo, not production-scale

---

### [DECISION 3] Anthropic Agent SDK vs. Custom Agent Implementation

**Context:** Requirements allow either Anthropic Claude Agent SDK or Pi Coding Agent.

**Decision:** Use Anthropic Claude Agent SDK (if available) as primary, with abstraction layer for flexibility.

**Rationale:**
- **Official support:** Anthropic maintains SDK, likely better Claude integration
- **Structured outputs:** SDK provides built-in support for tool use and structured responses
- **Community:** More examples and documentation available
- **Future-proof:** Updates to Claude capabilities automatically supported

**Abstraction Strategy:**
- Create `BaseAgent` interface
- Implement `AnthropicAgent` and `CustomAgent` as concrete classes
- Skills are provider-agnostic (receive context, return structured output)
- Can swap implementations without changing skills

**Fallback Plan:**
- If SDK has issues or doesn't work well with Ollama, fall back to direct API calls
- Same abstraction layer supports both paths

---

### [DECISION 4] Ship 30 for 30 Skill Implementation Strategy

**Context:** Requirements specify encoding writing principles in a skill, not relying on one-off prompts.

**Decision:** Create a dedicated `Ship30ContentGenerator` skill class with:
1. Structured prompt template with encoded principles
2. Validation logic for word count, structure, and grounding
3. Post-processing for formatting (bold, headings, bullets)
4. Source citation extraction and formatting

**Encoded Principles:**
```python
SHIP_30_PRINCIPLES = {
    "word_count": {"min": 1200, "max": 1300},
    "hook_sentences": 2,
    "heading_frequency": 200,  # Words between H2 headings
    "bullet_points_required": True,
    "bold_emphasis_required": True,
    "specific_takeaway": True,
    "source_grounding": True
}
```

**Validation:**
- Pre-generation: Check if enough source material exists
- Post-generation: Validate structure, word count, and citations
- Regeneration: If validation fails, retry with adjusted prompt

**Alternative Considered:** Generic "generate content" prompt  
**Why Rejected:** No guarantee of consistency, harder to debug quality issues

---

### [DECISION 5] Artifact Security Strategy

**Context:** Generated HTML artifacts pose XSS and code injection risks.

**Decision:** Multi-layered security approach:
1. **DOMPurify sanitization:** Remove scripts, event handlers, dangerous tags
2. **Sandboxed iframe:** `sandbox="allow-same-origin"` (no scripts, no forms)
3. **Content Security Policy:** Restrict script execution in viewer
4. **URL filtering:** Block external resource loading

**Rationale:**
- Defense in depth: Multiple independent layers
- Industry standard: DOMPurify widely used and audited
- User trust: Clear communication about what's blocked

**User Experience:**
- Warning badge if content was modified: "Artifact sanitized for safety"
- Option to view safe version vs. raw (with stronger warning)
- No silent failures (user knows when content is blocked)

**Testing:**
- Create test artifacts with known malicious patterns
- Verify each layer independently
- Document in tests/security_tests/artifact_injection.md

---

### [DECISION 6] Streaming Responses vs. Batch Responses

**Context:** LLM responses can be slow, especially for long content.

**Decision:** Implement both modes with streaming as default for conversational Q&A, batch for artifacts.

**Rationale:**
- **Streaming:** Better UX for chat (perceived speed), user sees progress
- **Batch:** Better for artifacts (avoid partial rendering, cleaner validation)
- **Flexibility:** Client can choose per request

**Implementation:**
- FastAPI supports SSE (Server-Sent Events) for streaming
- Backend: yield chunks as they arrive from LLM
- Frontend: Update message incrementally vs. single render

**Trade-off:**
- Complexity: Two code paths to maintain
- Testing: Streaming is harder to test than batch

**Mitigation:**
- Shared message assembly logic
- Integration tests for both modes

---

### [DECISION 7] Model Configuration: Environment Variables vs. UI Toggle

**Context:** Evaluators need to easily switch between cloud and local models.

**Decision:** Support both:
- **Default:** Environment variables (`.env` file) for persistent config
- **Runtime:** UI dropdown for quick switching without restart

**Rationale:**
- Env vars: Standard for deployment, works in Docker
- UI toggle: Better UX for evaluation, allows A/B comparison

**Implementation:**
- Backend `/api/v1/config` endpoint returns available models
- Frontend model selector calls `/api/v1/config/update` (if allowed)
- Or simpler: env vars only, document how to change (faster MVP)

**MVP Decision:** Start with env vars only, add UI toggle if time permits

---

## Failed Approaches (None Yet)

This session was planning-only. Failed implementations will be documented as development proceeds.

---

## Architectural Highlights from Documentation

### Database Schema Decisions

1. **UUID Primary Keys:** Better for distributed systems, avoids ID collision
2. **JSONB Metadata:** Extensibility without schema migrations
3. **Separate `transcript_chunks` Table:** Optimized for vector search, doesn't pollute main transcripts table
4. **Soft Deletion (`is_active` flag):** Allows recovery, maintains referential integrity

### API Design Decisions

1. **RESTful with Resource Nesting:** `/sessions/{id}/messages` follows conventions
2. **Pagination by Default:** `limit` and `offset` on all list endpoints
3. **Structured Error Responses:** Consistent format with correlation IDs
4. **Health Endpoints:** `/health` with component-level diagnostics

### Agent Layer Decisions

1. **Skill-Based Architecture:** Each capability is a self-contained module
2. **Intent Classification:** Simple routing layer (LLM or regex) determines skill
3. **Context Assembly:** Skills receive conversation history + retrieved chunks
4. **Source Attribution:** Built into skill outputs, not added later

---

## Next Steps

1. ✅ Complete core documentation (PRD, architecture.md, design.md)
2. Set up backend project structure with FastAPI
3. Implement database schema and migrations
4. Build transcript ingestion pipeline
5. Implement RAG retrieval system
6. Integrate agent layer with skills
7. Build frontend React application
8. Create Docker Compose setup
9. Write tests and final documentation
10. Record demo video

---

## Open Questions

1. **Transcript Source:** Where to get Lenny's Podcast transcripts?
   - **Options:** Public repos, scraping, sample dataset
   - **Decision:** Research GitHub for existing transcript collections

2. **Embedding Model:** Local vs. API?
   - **Options:** 
     - Local: sentence-transformers (all-MiniLM-L6-v2) - 384 dimensions, fast
     - API: OpenAI ada-002 - 1536 dimensions, high quality, costs money
   - **Leaning toward:** Local for demo (no API dependency)

3. **Ollama Model Choice:** Which model to use for demo?
   - **Options:** Llama 3.1 8B, Mistral 7B, Phi-3 Medium
   - **Decision:** Default to Llama 3.1 8B (best balance of quality and speed)

---

## Time Estimate

Based on task breakdown:
- **Documentation (Complete):** ~4 hours
- **Backend + Database:** ~8 hours
- **Ingestion + RAG:** ~6 hours
- **Agent Layer:** ~6 hours
- **Frontend:** ~10 hours
- **Testing + Deployment:** ~4 hours
- **Demo + Final Verification:** ~2 hours

**Total:** ~40 hours (5-6 days of focused work)

**Deadline:** September 15, 2026 EOD  
**Current Date:** September 16, 2026 (DAY AFTER DEADLINE!)

**CRITICAL ISSUE IDENTIFIED:** The deadline has already passed!

---

## Session Outcome

✅ **Success:** Created comprehensive documentation covering:
- PRD with discovery brief, user stories, and acceptance criteria
- architecture.md with database schema, API endpoints, component design
- design.md with UI/UX principles, responsive behavior, accessibility

⚠️ **Issue:** Deadline awareness - need to clarify with user if this is still valid

📋 **Artifacts Created:**
- `/docs/PRD.md` (3,800+ words)
- `/docs/architecture.md` (5,500+ words)
- `/docs/design.md` (4,200+ words)
- `/agent-transcripts/README.md`

---

**Session End**  
**Next Phase:** Backend foundation and database setup
