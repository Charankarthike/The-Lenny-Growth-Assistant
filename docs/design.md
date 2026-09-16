# Design Documentation: The Lenny Growth Assistant

## Design Philosophy

The Lenny Growth Assistant is designed around three core principles:

1. **Conversational Clarity:** Users should feel like they're chatting with an expert colleague, not interrogating a database
2. **Trust Through Transparency:** Every answer shows its sources; every limitation is acknowledged openly
3. **Artifact-First Creation:** Generated content is a first-class deliverable, not a chat byproduct

---

## Information Architecture

### Application Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         Top Bar                              │
│  Logo | Session Title | Model Indicator | New Session Btn   │
└─────────────────────────────────────────────────────────────┘
┌───────────────┬─────────────────────┬───────────────────────┐
│               │                     │                       │
│   Session     │   Chat Interface    │   Artifact Viewer     │
│   Sidebar     │                     │   (Conditional)       │
│               │   ┌─────────────┐   │                       │
│  ● Session 1  │   │  Messages   │   │   [Markdown/HTML]     │
│  ○ Session 2  │   │  (Scroll)   │   │                       │
│  ○ Session 3  │   │             │   │                       │
│               │   └─────────────┘   │                       │
│  [+ New]      │   ┌─────────────┐   │                       │
│               │   │ Message     │   │                       │
│               │   │ Input       │   │                       │
│               │   └─────────────┘   │                       │
└───────────────┴─────────────────────┴───────────────────────┘
```

### Layout Modes

**1. Chat-Only Mode (Default):**
- Session sidebar: 20% width (collapsible)
- Chat interface: 80% width
- Artifact viewer: Hidden

**2. Chat + Artifact Mode:**
- Session sidebar: 15% width (collapsible)
- Chat interface: 42.5% width
- Artifact viewer: 42.5% width
- Split view with resizable divider

**3. Mobile/Narrow Screen (<768px):**
- Session sidebar: Drawer overlay
- Chat and artifact stack vertically
- Artifact opens as modal or bottom sheet

---

## UI/UX Principles

### 1. Progressive Disclosure

**Problem:** AI assistants can overwhelm users with features and options.

**Solution:**
- Primary path is simple: type a question, get an answer
- Advanced features (model selection, session management) tucked into secondary UI
- Artifact viewer only appears when content is generated

**Example:**
- New users see: input box + "Ask me anything about product and growth"
- After first artifact generation: artifact panel slides in with subtle animation
- Model selector accessed via top bar dropdown, not prominent by default

### 2. Conversational Affordances

**Design Decision:** Chat UI should feel like messaging, not a terminal.

**Implementation:**
- User messages: right-aligned, blue background (familiar from iMessage/WhatsApp)
- Assistant messages: left-aligned, light gray background
- Timestamps shown on hover, not always visible (reduce clutter)
- "Typing" indicator when assistant is generating
- Smooth scroll to bottom when new message arrives

### 3. Source Transparency

**Problem:** Users don't trust AI without seeing its work.

**Solution:**
- Every assistant message includes expandable "Sources" section
- Sources show:
  - Episode number and title
  - Guest name (with avatar if available)
  - Relevant excerpt (200 characters)
  - Confidence/relevance score (visual indicator)
- Clicking a source highlights it in the message text

**Visual Treatment:**
```
┌─────────────────────────────────────────────────────┐
│ [Assistant Avatar]                                   │
│                                                      │
│ Based on Episode 42 with Elena Verna, pricing...   │
│                                                      │
│ ▼ Sources (2)                                       │
│   ┌───────────────────────────────────────────────┐ │
│   │ 🎙️ Episode 42 • Elena Verna                   │ │
│   │ "You have to understand your value metric..." │ │
│   │ Relevance: ●●●●○ (0.89)                       │ │
│   └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 4. Artifact Materialization

**Design Decision:** Artifacts should feel like created documents, not code snippets.

**Visual Hierarchy:**
1. **Artifact Header:**
   - Title (editable inline)
   - Type badge (Markdown / HTML / JSON)
   - Actions: Copy, Download, Regenerate, Full Screen
   
2. **Artifact Content:**
   - Rendered in viewer (not raw code by default)
   - Option to toggle "View Source" for markdown or HTML
   
3. **Artifact Metadata:**
   - Word count, reading time (for essays)
   - Sources cited
   - Generation timestamp

**Interaction States:**
- **Loading:** Skeleton screen with pulsing placeholder
- **Rendered:** Full content with smooth fade-in
- **Error:** Friendly error message with "Try Again" button

### 5. Model Awareness

**Problem:** Users should know which LLM is responding (quality varies).

**Solution:**
- Top bar shows active model: "Using: Llama 3.1 (Local)" or "Claude 3.5 Sonnet"
- Color-coded indicator:
  - 🟢 Green: Cloud LLM (high quality)
  - 🟡 Yellow: Local LLM (good quality, no API costs)
  - 🔴 Red: Fallback mode (degraded service)
- Dropdown allows switching models mid-session

---

## Key Interaction Flows

### Flow 1: First-Time User - Ask a Question

**Steps:**
1. User lands on app → sees empty chat with prompt: *"Ask me about product management, growth, or pricing strategy from Lenny's Podcast"*
2. User types: *"What does Lenny say about retention?"*
3. Loading state: typing indicator appears
4. Response appears with:
   - Answer text
   - 2-3 source cards (collapsed by default)
   - Confidence indicator
5. User can:
   - Ask follow-up (input remains focused)
   - Expand sources to read excerpts
   - Start new session (clear context)

**Design Considerations:**
- Zero onboarding friction
- Sources are visible but not intrusive
- Follow-up questions are natural next step

### Flow 2: Generate Ship 30 for 30 Content

**Trigger Phrases:**
- "Write a Ship 30 for 30 essay about..."
- "Generate a Ship 30 for 30 post on..."
- "Create content about..."

**Steps:**
1. User types trigger phrase
2. Assistant responds: *"I'll create a Ship 30 for 30 essay for you. This will take about 10-15 seconds..."*
3. Artifact viewer slides in from right (if not already visible)
4. Skeleton loader shows in artifact panel
5. Content streams in (if streaming enabled) or appears complete
6. Artifact displays with:
   - Generated title
   - Full rendered markdown (headings, bold, bullets)
   - Metadata footer (word count, sources)
7. User can:
   - Copy entire content to clipboard
   - Download as .md file
   - Request edits: *"Make it more concise"*
   - Generate new artifact on different topic

**Design Considerations:**
- Clear intent recognition (user doesn't need exact syntax)
- Artifact panel gives content prominence
- Inline editing for title (feel of ownership)
- Export options for using content elsewhere

### Flow 3: Browse Previous Sessions

**Steps:**
1. User clicks session in sidebar
2. Loading state: session list item highlights
3. Chat interface updates:
   - Scrolls to top of conversation
   - Loads all messages (lazy load if >50 messages)
   - If session had artifacts, artifact viewer shows last artifact
4. User can resume conversation or review history
5. Session title updates in top bar

**Design Considerations:**
- Session list shows preview of first message (helps recall)
- Most recent session selected by default
- Smooth transition (no jarring page reload)

### Flow 4: Handle "No Information Available"

**Trigger:**
- User asks question outside transcript scope
- Retrieval returns low-confidence results

**Steps:**
1. Assistant responds: *"I don't have information about that in the available transcripts. The podcast primarily covers product management, growth, and SaaS strategy. Could you rephrase or ask something else?"*
2. No sources shown (since none are relevant)
3. Suggested topics appear below:
   - "Ask about retention strategies"
   - "Ask about pricing psychology"
   - "Ask about PLG vs. sales-led"

**Design Considerations:**
- Honest acknowledgment builds trust
- Suggestions help user recover and explore
- No fabricated answers or speculation

### Flow 5: Error Handling - Ollama Not Running

**Trigger:**
- Backend attempts to use Ollama, but service is down
- Health check fails

**Steps:**
1. User sends message
2. Error state appears in chat:
   ```
   ⚠️ Local model server is not running
   
   To use Ollama:
   1. Open terminal
   2. Run: ollama serve
   3. In another terminal: ollama pull llama3.1:8b
   4. Try your question again
   
   Or switch to a cloud model in settings.
   ```
3. Input remains enabled (user can switch models)
4. Settings dropdown highlights with pulse animation (call to action)

**Design Considerations:**
- Actionable error messages (not technical jargon)
- Users can self-recover without developer knowledge
- System doesn't crash or hang

---

## Component Design Specifications

### Component: Message Bubble

**User Message:**
```
┌─────────────────────────────────────────┐
│                    What does Lenny say  │ ← Right-aligned
│                    about pricing?       │   Blue background (#3b82f6)
│                               10:30 AM  │   White text
└─────────────────────────────────────────┘   Rounded corners (12px)
```

**Assistant Message:**
```
┌──────────────────────────────────────────────────────┐
│ [Avatar]  Based on Episode 42...                     │ ← Left-aligned
│                                                       │   Gray background (#f3f4f6)
│           ▼ Sources (2)                              │   Dark text
│           [Source cards...]                          │   Avatar: 32x32px circle
│                                                       │
│           10:30 AM                                   │
└──────────────────────────────────────────────────────┘
```

**Typography:**
- Font: Inter (sans-serif, optimized for readability)
- User message: 15px, 500 weight
- Assistant message: 15px, 400 weight
- Timestamps: 12px, 400 weight, muted color
- Source excerpts: 13px, 400 weight, monospace for code

**Spacing:**
- Padding inside bubble: 12px vertical, 16px horizontal
- Gap between messages: 16px
- Gap between source cards: 8px

### Component: Source Card

```
┌────────────────────────────────────────────────────┐
│ 🎙️ Episode 42 • Elena Verna            ●●●●○ 0.89│ ← Header
├────────────────────────────────────────────────────┤
│ "You have to understand your value metric before  │ ← Excerpt
│ you can set a price. Most companies get this..."  │   (Truncated to 150 chars)
└────────────────────────────────────────────────────┘
```

**Styling:**
- Border: 1px solid light gray
- Border radius: 8px
- Background: white (or light tint matching theme)
- Hover state: subtle shadow, cursor pointer
- Click action: Expands to show full context + scrolls to relevant part of message

**Relevance Indicator:**
- 5 dots representing score quintiles
- Filled dots: dark gray
- Empty dots: light gray
- Score displayed as decimal: 0.89

### Component: Artifact Viewer

**Header:**
```
┌────────────────────────────────────────────────────┐
│ 📄 Ship 30 for 30: Pricing Strategy  [Edit Title]│
│ Markdown • 1,248 words • 6 min read               │
│                                                    │
│ [Copy] [Download] [Regenerate] [View Source] [⛶] │ ← Actions
└────────────────────────────────────────────────────┘
```

**Content Area:**
- White background
- Padding: 32px (generous whitespace)
- Max width: 680px (optimal reading width)
- Centered within panel

**Markdown Styling:**
- H1: 32px, 700 weight, 1.4em margin-top
- H2: 24px, 600 weight, 1.2em margin-top
- Body: 16px, 400 weight, 1.6 line-height
- Bold: 600 weight, slight color darkening
- Lists: 8px left indent, 0.5em spacing
- Code blocks: Monaco font, light gray background

**HTML Rendering (Sandboxed):**
- Iframe with `sandbox="allow-same-origin"`
- No scripts, no forms
- Width: 100%, height: auto-adjust based on content

**Footer:**
```
┌────────────────────────────────────────────────────┐
│ Sources: Episode 42 (E. Verna), Episode 67 (R...  │
│ Generated: Sep 16, 2026 at 10:35 AM               │
└────────────────────────────────────────────────────┘
```

### Component: Model Selector

**Collapsed State (Top Bar):**
```
Using: Llama 3.1 (Local) 🟡 [▼]
```

**Expanded State (Dropdown):**
```
┌─────────────────────────────────────────┐
│ Cloud Models                            │
│ ○ Claude 3.5 Sonnet    [Key Required]  │
│ ○ GPT-4 Mini           [Key Required]  │
│                                         │
│ Local Models (Ollama)                   │
│ ● Llama 3.1 8B         [Active]        │
│ ○ Mistral 7B           [Available]     │
│ ○ Phi-3 Medium         [Not Pulled]    │
│                                         │
│ [⚙️ Configure API Keys]                │
└─────────────────────────────────────────┘
```

**States:**
- Active model: filled radio button, bold text
- Available models: empty radio button, normal text
- Unavailable models: grayed out, helper text explains why

**Feedback:**
- After switching: Toast notification: *"Switched to Claude 3.5 Sonnet"*
- If switch fails: Error toast with recovery action

### Component: Session Sidebar

**Session List Item:**
```
┌──────────────────────────────────────┐
│ ● Session Title (editable)           │ ← Active: filled circle
│   "What does Lenny say about..."     │   Preview of first message
│   2 hours ago • 12 messages          │   Metadata
└──────────────────────────────────────┘
```

**States:**
- Active: Bold title, filled indicator, light background
- Inactive: Normal weight, empty circle indicator
- Hover: Slight background color change, cursor pointer

**Actions:**
- Click: Load session
- Long press / Right-click: Context menu (Rename, Delete, Export)

**New Session Button:**
```
┌──────────────────────────────────────┐
│         [+ New Conversation]          │
└──────────────────────────────────────┘
```

**Collapsed State (Mobile):**
- Hamburger icon opens drawer overlay
- Drawer slides from left

---

## Responsive Behavior

### Breakpoints

| Breakpoint | Width | Layout Changes |
|-----------|-------|----------------|
| Desktop | ≥1024px | Full 3-column layout |
| Tablet | 768px - 1023px | Sidebar collapsible, artifact stacks below chat |
| Mobile | <768px | Sidebar as drawer, single column, artifact as modal |

### Mobile Optimizations

1. **Touch Targets:**
   - Minimum 44px height for all interactive elements
   - Increased padding on buttons and inputs

2. **Gesture Support:**
   - Swipe from left edge: Open session drawer
   - Swipe right on message: Quick copy
   - Pull-to-refresh: Reload session (optional)

3. **Input Behavior:**
   - On mobile: input expands to full width when focused
   - Send button moves to keyboard (native behavior)
   - Voice input option (if browser supports)

4. **Artifact Viewing:**
   - Full-screen modal instead of side panel
   - Swipe down to dismiss
   - Actions in bottom sheet

---

## Accessibility Considerations

### WCAG 2.1 AA Compliance

#### 1. Keyboard Navigation

**All interactive elements keyboard accessible:**
- Tab order: Session sidebar → Message input → Model selector → Artifact actions
- Enter: Send message, select session, trigger actions
- Escape: Close dropdowns, exit full-screen
- Arrow keys: Navigate message history (optional enhancement)

**Focus Indicators:**
- 2px solid outline on focused elements
- High contrast color (#2563eb)
- Offset by 2px for clarity

#### 2. Screen Reader Support

**ARIA Labels:**
```html
<button aria-label="Send message">
  <SendIcon />
</button>

<div role="article" aria-label="Assistant response">
  <p>{message content}</p>
</div>

<section aria-label="Sources for this response" aria-expanded="false">
  {source cards}
</section>
```

**Live Regions:**
```html
<div role="status" aria-live="polite" aria-atomic="true">
  {typing indicator or new message announcement}
</div>
```

**Semantic HTML:**
- `<main>` for chat interface
- `<aside>` for session sidebar and artifact viewer
- `<article>` for each message
- `<nav>` for session list

#### 3. Color Contrast

**Minimum Ratios (WCAG AA):**
- Normal text: 4.5:1
- Large text (18px+): 3:1
- UI components: 3:1

**Color Palette:**
| Element | Foreground | Background | Ratio |
|---------|-----------|------------|-------|
| User message | #ffffff | #3b82f6 | 8.2:1 ✓ |
| Assistant message | #1f2937 | #f3f4f6 | 15.4:1 ✓ |
| Source card | #374151 | #ffffff | 12.6:1 ✓ |
| Primary button | #ffffff | #2563eb | 8.1:1 ✓ |

**Color Independence:**
- Relevance scores: dots + numerical value (not color only)
- Status indicators: icon + text label (not color only)
- Error states: icon + message (not red color only)

#### 4. Text Scaling

**Support up to 200% zoom:**
- Responsive typography using `rem` units
- No fixed pixel widths (use max-width with %)
- Horizontal scrolling avoided
- Content reflows without breaking layout

#### 5. Alternative Text

**Images:**
```html
<img src="avatar.png" alt="Claude AI Assistant" />
<img src="episode-icon.png" alt="" role="presentation" />  <!-- Decorative -->
```

**Icons:**
- Decorative icons: `aria-hidden="true"`
- Functional icons: `aria-label` describing action

#### 6. Form Accessibility

**Message Input:**
```html
<label for="message-input" class="sr-only">
  Type your message
</label>
<textarea 
  id="message-input"
  aria-describedby="input-hint"
  aria-required="true"
  placeholder="Ask me anything..."
/>
<div id="input-hint" class="sr-only">
  Press Enter to send, Shift+Enter for new line
</div>
```

**Error Handling:**
```html
<div role="alert" aria-live="assertive">
  Message could not be sent. Please try again.
</div>
```

---

## Visual Design System

### Color Palette

**Primary Colors:**
- Brand Blue: `#3b82f6` (user messages, CTA buttons)
- Dark Gray: `#1f2937` (primary text)
- Light Gray: `#f3f4f6` (assistant messages, backgrounds)

**Semantic Colors:**
- Success: `#10b981` (green)
- Warning: `#f59e0b` (yellow/orange)
- Error: `#ef4444` (red)
- Info: `#3b82f6` (blue)

**Status Indicators:**
- Cloud LLM: `#10b981` (green)
- Local LLM: `#f59e0b` (yellow)
- Fallback/Error: `#ef4444` (red)

### Typography Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 32px | 700 | 1.2 |
| H2 | 24px | 600 | 1.3 |
| H3 | 20px | 600 | 1.4 |
| Body | 15px | 400 | 1.6 |
| Small | 13px | 400 | 1.5 |
| Code | 14px | 400 | 1.4 |

**Font Stack:**
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 
             'Roboto', 'Helvetica Neue', Arial, sans-serif;
```

### Spacing System

**Base unit: 4px**

| Token | Value | Use Case |
|-------|-------|----------|
| xs | 4px | Icon margins, tight spacing |
| sm | 8px | List item gaps, small padding |
| md | 16px | Message gaps, button padding |
| lg | 24px | Section spacing |
| xl | 32px | Page margins, artifact padding |

### Elevation (Shadows)

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
```

**Usage:**
- sm: Source cards, subtle hover states
- md: Dropdowns, modals
- lg: Artifact viewer (emphasize importance)

### Border Radius

| Element | Radius |
|---------|--------|
| Message bubbles | 12px |
| Source cards | 8px |
| Buttons | 8px |
| Input fields | 8px |
| Artifact viewer | 16px (outer container) |

---

## Animation and Motion

**Principles:**
- **Purposeful:** Animations guide attention and communicate state
- **Fast:** Durations typically 150-300ms (never exceed 500ms)
- **Smooth:** Use `ease-out` for entrances, `ease-in` for exits

### Key Animations

**1. Message Appearance:**
```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message {
  animation: slideUp 200ms ease-out;
}
```

**2. Artifact Panel Slide-In:**
```css
@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.artifact-viewer.entering {
  animation: slideInRight 300ms ease-out;
}
```

**3. Typing Indicator:**
```css
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.typing-dot {
  animation: pulse 1.4s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
```

**4. Source Card Expand:**
```css
.source-card {
  transition: max-height 250ms ease-out, box-shadow 150ms ease;
}

.source-card:hover {
  box-shadow: var(--shadow-md);
}
```

**5. Skeleton Loader (Artifact Loading):**
```css
@keyframes shimmer {
  from { background-position: -200% 0; }
  to { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #f3f4f6 25%,
    #e5e7eb 50%,
    #f3f4f6 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

---

## Edge Cases and Error States

### 1. Empty States

**No Sessions:**
```
┌─────────────────────────────────────┐
│   No conversations yet              │
│                                     │
│   [Icon: Chat Bubble]               │
│                                     │
│   Start by asking a question about  │
│   product management or growth.     │
│                                     │
│   [+ New Conversation]              │
└─────────────────────────────────────┘
```

**No Artifacts:**
- Artifact viewer remains hidden until first generation
- No placeholder shown

### 2. Loading States

**Initial Page Load:**
- Skeleton loaders for session sidebar
- Empty chat with pulsing input field

**Message Sending:**
- User message appears immediately (optimistic UI)
- Typing indicator shows assistant is working
- If fails: User message gets error badge, inline retry button

**Artifact Generation:**
- Skeleton with title placeholder
- Progress text: "Generating content... (12s elapsed)"
- If exceeds 30s: Warning appears with cancel option

### 3. Network Errors

**Connection Lost:**
```
⚠️ Connection lost
You're offline. Messages will be sent when you reconnect.
```

**API Error:**
```
❌ Something went wrong
The server encountered an error. [Try Again] [View Details]
```

**Details Expandable:**
- Correlation ID for debugging
- Timestamp
- Error type (for technical users)

### 4. Rate Limiting

**User Exceeded Limits:**
```
⏱️ Slow down
You're sending messages too quickly. 
Please wait 30 seconds before trying again.

[Countdown: 28s remaining]
```

### 5. Content Sanitization Warnings

**HTML Blocked:**
```
⚠️ Artifact Modified for Safety
Some elements were removed from this HTML artifact:
• JavaScript code
• External image loading
• Form submissions

[View Safe Version] [View Original (Advanced)]
```

---

## Design Decisions and Trade-offs

### Decision 1: Separate Artifact Viewer vs. Inline Display

**Choice:** Dedicated panel, not inline in chat

**Rationale:**
- Artifacts are deliverables, not ephemeral messages
- Side-by-side view allows comparison while iterating
- Easier to copy, download, and manage
- Inline would clutter conversation history

**Trade-off:**
- Smaller effective chat width on desktop
- More complex responsive behavior

### Decision 2: Source Citations Collapsed by Default

**Choice:** Sources appear below message but collapsed initially

**Rationale:**
- Most users trust the answer and don't need deep verification
- Always showing sources creates visual noise
- Power users can easily expand when needed

**Trade-off:**
- Transparency slightly reduced (one extra click)
- Risk users don't discover source feature

**Mitigation:**
- First-time tooltip: "Click to see sources"
- Subtle animation draws eye to section

### Decision 3: No Voice Input (MVP)

**Choice:** Text-only input for now

**Rationale:**
- Voice transcription adds complexity (API costs, privacy)
- Primary use case is desk work (typing is efficient)
- Can add later if user research shows demand

**Trade-off:**
- Less accessible for users with typing difficulties
- Mobile users might prefer voice

**Future Enhancement:**
- Browser's native voice input (simple integration)
- Or Web Speech API for better control

### Decision 4: Sessions Persist Indefinitely

**Choice:** No automatic session expiration or cleanup

**Rationale:**
- Users may reference old conversations weeks later
- Storage is cheap (text data)
- Manual deletion gives users control

**Trade-off:**
- Database can grow large over time
- No privacy-by-default (conversations linger)

**Production Consideration:**
- Add archival feature (move old sessions to cold storage)
- Auto-delete after 90 days with warning

### Decision 5: Model Selection in UI (Not Just Config)

**Choice:** Users can switch models from top bar

**Rationale:**
- Evaluators need to compare quality easily
- Switching mid-session shows fallback behavior
- Transparency about which model is responding

**Trade-off:**
- UI complexity (more dropdowns)
- Risk of confusing non-technical users

**Mitigation:**
- Default to best available model automatically
- Settings accessible but not prominent

---

## User Feedback Mechanisms

### 1. Message Reactions (Future Enhancement)

```
[Assistant Message]
  👍 Helpful  👎 Not helpful  🔗 Copy  ⚠️ Report issue
```

**Purpose:**
- Quality feedback for model tuning
- Identify failing queries

### 2. Artifact Rating

```
How useful was this content?
⭐⭐⭐⭐⭐
[Optional: Tell us more...]
```

**Purpose:**
- Measure Ship 30 for 30 skill quality
- Inform prompt engineering

### 3. Inline Error Reporting

```
[Message with error badge]
[Report Problem]
  → Popup:
     ○ Incorrect information
     ○ Poor source citation
     ○ Unhelpful response
     ○ Technical error
     [Submit]
```

**Purpose:**
- Capture issue context automatically
- Faster debugging

---

## Internationalization Readiness (Future)

While MVP is English-only, design supports future i18n:

1. **Layout:**
   - No hardcoded text in components (use i18n keys)
   - RTL (right-to-left) compatible flexbox (no absolute positioning)

2. **Typography:**
   - Font stack includes Unicode-capable fonts
   - Line height accommodates taller scripts (Thai, Arabic)

3. **Dates/Times:**
   - Use relative format ("2 hours ago") over absolute
   - When absolute: ISO format with locale detection

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-16  
**Author:** Forward Deployed Engineer Candidate
