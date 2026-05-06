---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
status: complete
completedAt: 2026-05-06
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/product-brief-skate-ecommerce.md
---

# skate-ecommerce AI Shopping Assistant — Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the skate-ecommerce AI Shopping Assistant, decomposing requirements from the PRD, UX Design Specification, and Architecture Decision Document into implementable stories.

## Requirements Inventory

### Functional Requirements

**Conversational Discovery (FR1–FR7)**

- **FR1:** User can submit a natural-language request describing their shopping intent (e.g., "durable street setup, intermediate, around $200").
- **FR2:** User can engage the assistant in a multi-turn conversation, with each turn building on prior context within the session.
- **FR3:** System can ask the user clarifying questions when intent is underspecified (e.g., skill level, terrain, budget, riding style).
- **FR4:** User can refine a recommendation by providing additional constraints (e.g., "show me cheaper options", "compare these side by side").
- **FR5:** System can decline gracefully and disclose its confidence boundaries when the catalog cannot satisfy the user's intent.
- **FR6:** User can engage with the assistant without authentication (anonymous mode).
- **FR7:** User can request a side-by-side comparison of two or more recommended products.

**Recommendation Reasoning & Explanation (FR8–FR15)**

- **FR8:** System can extract structured intent (typed attributes) from natural-language user input.
- **FR9:** System can retrieve candidate products from the catalog using the extracted intent.
- **FR10:** System can recommend a single product that matches the user's intent.
- **FR11:** System can recommend a complete setup (deck + trucks + wheels) as a coherent, jointly-reasoned group.
- **FR12:** System can produce a natural-language explanation for each recommendation, including trade-offs expressed in skater vernacular (e.g., durability vs. weight, beginner vs. advanced, street vs. cruising).
- **FR13:** System can stream the recommendation explanation to the user as it is generated.
- **FR14:** System emits an early-acknowledgement signal so the user sees a first response token within the low-latency budget while the full recommendation is computed.
- **FR15:** System grounds every recommended product in the actual catalog; no hallucinated SKUs or attributes are emitted.

**Compatibility Validation (FR16–FR20)**

- **FR16:** System validates every proposed setup against a deterministic Compatibility Layer before presenting it to the user.
- **FR17:** System rejects candidate products from setup recommendations when required compatibility attributes are missing or invalid.
- **FR18:** System can repair a proposed setup by substituting compatible alternatives when the initial proposal is invalid.
- **FR19:** System discloses to the user when a recommendation has reduced confidence due to missing catalog data (e.g., absent attribute tags).
- **FR20:** System logs missing-attribute occurrences to a catalog-quality backfill queue.

**Cart Construction (FR21–FR26)**

- **FR21:** User can review a recommendation in detail (SKUs, stock, prices, total) before any cart action.
- **FR22:** User can confirm and add a single recommended product to the existing cart.
- **FR23:** User can confirm and add a complete recommended setup (multiple SKUs) to the existing cart in a single action.
- **FR24:** System guarantees all-or-nothing semantics on setup adds: either all items are added, or none are.
- **FR25:** System never autonomously mutates the cart; every cart write requires explicit user confirmation.
- **FR26:** System never accesses or mutates checkout, payments, orders, inventory, or account state.

**Identity & Session (FR27–FR32)**

- **FR27:** Anonymous users can interact with the assistant with feature parity on recommendation quality (auth-only features are additive, not gating).
- **FR28:** Authenticated users can interact with the assistant via verified Firebase Auth identity.
- **FR29:** Authenticated users' conversations are persisted across sessions.
- **FR30:** Authenticated users can resume an in-progress conversation on a different device (cross-device continuity).
- **FR31:** System can use an authenticated user's recent-order history and current cart contents as personalization signals.
- **FR32:** System enforces rate limits and cost caps on anonymous sessions to prevent abuse and cost incidents.

**AI Operations & Observability (FR33–FR38)**

- **FR33:** System captures per-trace telemetry for every conversational turn (agent path taken, per-stage latency, total token cost, tool-call counts, hashed user identifier, cache hit/miss, compatibility-verdict counts).
- **FR34:** AI Ops engineer can view aggregate metrics on a dashboard for relevance, latency, cost, grounding, and cache efficacy.
- **FR35:** System runs an LLM-judge evaluation against a curated Ground Truth Set on every prompt change, model change, or agent topology change.
- **FR36:** AI Ops engineer can localize a quality regression to a specific agent in the topology via per-agent evaluation slices.
- **FR37:** System blocks a model upgrade or prompt change in CI when eval relevance falls below the configured threshold.
- **FR38:** System enforces hard caps per turn (iterations, tokens, wall-clock) and halts on loop detection.

**Compatibility Rule Authoring (FR39–FR42)**

- **FR39:** Rule author can define a new compatibility rule in a structured, reviewable format (rule schema).
- **FR40:** Rule author can submit a new rule for code review through the standard repository workflow.
- **FR41:** Each compatibility rule has an explicit version, owner, and effective date in its metadata.
- **FR42:** Rule author can view per-rule firing metrics on a dashboard (how often a rule applied, accepted, repaired, or rejected candidates).

**Privacy & Data Control (FR43–FR47)**

- **FR43:** System informs users at first interaction that they are interacting with an AI assistant, not a human.
- **FR44:** Authenticated users can disable persistent conversation history (opt-out).
- **FR45:** Users can request deletion of their conversation history; system honors deletion within the documented retention SLA.
- **FR46:** System retains conversation logs for no longer than 30 days; aggregated analytics are PII-stripped before retention.
- **FR47:** System does not store raw free-text user queries alongside user identifiers.

**Operational Resilience (FR48–FR50)**

- **FR48:** System falls back to the existing keyword-search experience when the LLM provider is unavailable or sustained tail latency exceeds threshold (circuit-breaker behavior).
- **FR49:** System provides a degraded-mode response with a documented machine-readable reason code when the assistant cannot meet its service-level objectives.
- **FR50:** Existing platform flows (browse, cart, checkout) remain operational regardless of assistant availability; assistant outage does not constitute a site outage.

### NonFunctional Requirements

**Performance (NFR1–NFR5)**

- **NFR1:** End-to-end response latency P95 < 3 seconds (measured from request acceptance to last streamed token).
- **NFR2:** First user-visible token latency < 1 second P95 (delivered via early-acknowledgement stub from the fast-model layer).
- **NFR3:** Per-stage latency budgets hold at P95: edge auth ≤ 80 ms, semantic-cache lookup ≤ 50 ms, intent extraction ≤ 600 ms, parallel retrieval (slowest branch) ≤ 400 ms, compatibility validation ≤ 100 ms, explanation TTFT ≤ 800 ms.
- **NFR4:** Streaming explanation throughput sustained across full response length without observable inter-token gaps > 200 ms.
- **NFR5:** TTFB on the existing platform pages must not regress more than 50 ms attributable to assistant widget code; chat widget is code-split and lazy-loaded on pages where the user has not engaged it.

**Security (NFR6–NFR13)**

- **NFR6:** All authenticated traffic carries a verified Firebase ID token; verification occurs at the service edge before any agent execution.
- **NFR7:** All anonymous traffic is rate-limited (token-bucket per session ID + per-IP) and cost-capped per session, with CAPTCHA escalation on anomalous patterns.
- **NFR8:** LLM-provider API keys are stored in a managed secret store, scoped by environment, rotated on schedule; no credential overlap with checkout-system secrets.
- **NFR9:** Tool-permission allow-list enforced at the gateway: `cart-add` is the only mutation tool; all other mutation surfaces are structurally inaccessible to the LLM.
- **NFR10:** Pre-launch red-team / penetration test of the assistant's tool surface, including indirect prompt injection vectors via product reviews and seller descriptions, is a launch gate.
- **NFR11:** Audit log retains every cart-mutation event with hashed user ID, session ID, timestamp, SKU set, recommendation source, and idempotency key for ≥ 90 days.
- **NFR12:** Compliance with applicable consumer-privacy regimes (CCPA / CPRA in the US, GDPR if EU users); data residency configurable per deployment with LLM-provider region pinned to match.
- **NFR13:** PCI scope is structurally avoided — the assistant never touches payment instruments, card data, or payment tokens.

**Scalability (NFR14–NFR19)**

- **NFR14:** System supports 50,000 daily active users sustained.
- **NFR15:** System supports 2,000 peak concurrent users at the documented latency SLOs.
- **NFR16:** Pre-launch load test on staging at peak-concurrent levels is a launch gate; provider rate-limit headroom verified ≥ 2× peak requests-per-second.
- **NFR17:** Postgres connection pool sized for `concurrent users × parallel-retrieval fan-out × agents` with documented headroom.
- **NFR18:** Per-session cost P95 ≤ $0.05 — hard constraint enforced via gateway-level token-budget caps.
- **NFR19:** System scales horizontally: stateless request handlers behind load balancer, persistent state in PostgreSQL and Firestore. Stateful behavior at the request handler layer is forbidden.

**Reliability (NFR20–NFR25)**

- **NFR20:** Assistant uptime target: 99.5% over rolling 30-day windows.
- **NFR21:** Existing platform flows (browse, cart, checkout) target ≥ 99.95% over rolling 30-day windows; assistant outage does not affect this metric (architectural non-coupling).
- **NFR22:** LLM-provider circuit-breaker trips on sustained provider error rate or TTFT P99 exceeding configured thresholds; on trip, the frontend renders the existing keyword-search UI seeded with the user's prompt as keyword input.
- **NFR23:** Zero runaway-loop incidents in production; per-session iteration, token, and wall-clock caps enforced at the gateway in addition to per-agent caps.
- **NFR24:** Streaming-vs-persistence durability: a completed assistant message is durably written to Firestore (with retry) before the client acknowledges turn-complete; an out-of-band reconciliation job detects and repairs orphans.
- **NFR25:** Operational runbooks for LLM-provider outage, Firebase Auth outage, Postgres pool saturation, runaway-cost incident, and eval-CI failure ship before launch.

**Accessibility (NFR26–NFR30)**

- **NFR26:** Chat UI conforms to WCAG 2.2 AA across keyboard navigation, screen-reader semantics, color contrast, and focus management.
- **NFR27:** Streaming text updates are announced to assistive technologies via appropriate ARIA live-region semantics.
- **NFR28:** All interactive controls (input, send, confirm, opt-out, dismiss) are keyboard-operable with visible focus indicators.
- **NFR29:** Users' `prefers-reduced-motion` setting is respected; typing animations and streaming visualizations degrade to instant text rendering.
- **NFR30:** Touch targets on mobile are ≥ 44 × 44 CSS pixels; viewport supported down to 320 px width.

**Integration (NFR31–NFR36)**

- **NFR31:** Catalog data is accessed read-only by the assistant via a dedicated PostgreSQL role with SQL-level access for parallel attribute filters.
- **NFR32:** Cart-add operations flow through the existing cart API using per-request idempotency keys; setup adds use a batch endpoint (or a transactional server-side adapter) with all-or-nothing semantics.
- **NFR33:** User-account reads (recent orders, current cart contents) are read-only and mediated by a verified Firebase Auth ID token.
- **NFR34:** Firebase Auth ID-token verification chain validated end-to-end (Next.js → Python service → `firebase-admin`) on every authenticated request.
- **NFR35:** Firestore is used exclusively for session/message persistence and realtime listeners; it is not used as a token-streaming bus.
- **NFR36:** Per-trace observability vendor (Langfuse self-hosted on GCP) is instrumented from launch with cost, latency, and agent-decision tracing across every conversational turn.

**AI Quality (NFR37–NFR42)**

- **NFR37:** Recommendation relevance ≥ 85% (lower bound of 95% CI) on the curated Ground Truth Set, measured via LLM-judge with a structured rubric (relevance, accuracy, completeness, safety).
- **NFR38:** Zero hallucinated SKUs in production — every recommended product exists in the catalog with the attributes the system claims for it.
- **NFR39:** Combined cache hit rate (prompt cache + semantic cache) on head queries ≥ 40% by week 4 post-launch (instrumented from launch).
- **NFR40:** Eval-harness CI gate blocks any prompt change, model upgrade, or agent topology change that drops eval relevance below the configured threshold.
- **NFR41:** Per-agent evaluation slices are produced by every CI eval run, enabling regression localization to a single agent on quarterly model upgrades.
- **NFR42:** Inter-rater agreement between LLM-judge and human reviewers is spot-checked on a 10% sample of GTS entries; discrepancies above a documented threshold trigger judge-rubric review.

### Additional Requirements

Architecture-derived requirements that materially shape epics and stories:

**Starter / scaffolding (Epic 1 Story 1 prerequisite):**

- Architecture commits to **dual scaffolding**: `create-next-app` + `shadcn/ui` CLI for the frontend; manual `uv` + FastAPI + Google ADK + Alembic init for the backend. No off-the-shelf single-template starter covers the combined stack.
- **Project bootstrap is the explicit first implementation story** per Architecture Step 3.

**Cloud infrastructure (GCP):**

- **Cloud Run gen-2** (backend), **Vercel** (frontend), **Cloud SQL Postgres 16 HA + read replica** (data), **Firestore** (sessions/messages), **Memorystore Redis Standard HA 5 GB** (rate-limit + semantic cache), **GCP Secret Manager** (all secrets), **Cloud Armor + reCAPTCHA Enterprise** (edge), **Artifact Registry** (containers), **VPC + private IP** for all data services.
- **Terraform** as IaC for all GCP resources.
- **Cloud Run Job** as Alembic migration runner, executed pre-deploy.

**Schema migration discipline (intake-mandated):**

- **Alembic mandatory**, async-aware.
- All migrations idempotent and reversible (downgrade supported).
- CI gate runs `upgrade head` + `downgrade -1` + `upgrade head` test on every PR.
- Migrations auto-applied on deploy via Cloud Run Job pre-step.
- Application startup checks `alembic_version` table; refuses to start on schema drift.

**LLM provider routing:**

- **Anthropic Claude Sonnet via Anthropic API** for ExplanationAgent (reasoning).
- **Vertex AI Gemini Flash** for IntentAgent + early-acknowledgement stub (fast/small).
- **Vertex AI text-embedding-005** for semantic-cache keys and unstructured RAG embeddings.
- LLM circuit-breaker fallback is **not** another LLM — it is the existing keyword-search route.

**Observability stack:**

- **Langfuse self-hosted on Cloud Run** (LLM-specific traces, prompt/completion, token cost, eval feedback).
- **OpenTelemetry dual-emit** to Langfuse + Cloud Trace + Cloud Logging + Cloud Monitoring.
- Per-trace telemetry on every chat turn (agent path, per-stage latency, cost, tool-calls, hashed user ID, cache hit/miss, compatibility verdicts).

**CI/CD pipeline (GitHub Actions):**

- Stages: lint → typecheck → unit → integration → eval-harness → Alembic upgrade+downgrade → axe-core a11y → Lighthouse → bundle-size budget → container build + vulnerability scan → staging deploy + smoke test + load test → manual or canary promotion to production.
- **Canary deploys** at 10% for 30 min before promotion.
- **Eval harness** is a launch gate; relevance ≥ 85% lower-CI-bound is required to pass.

**Existing-platform integration (brownfield):**

- **Catalog read** via direct PostgreSQL connection on a Cloud SQL **read replica** with `assistant_read_only` role. SQLAlchemy read-only view in `app/models/catalog.py`.
- **Cart write** via thin Python adapter (`app/services/cart_client.py`) wrapping the existing platform's cart API; idempotency-key-aware; transactional all-or-nothing for setup adds; adapter is in v1 scope.
- **User account read** via existing platform's HTTPS API, mediated by Firebase ID token forwarding.

**Frontend infrastructure:**

- TypeScript types **generated** from JSON Schema export of Pydantic models — committed to the frontend repo (single source of truth).
- **Storybook** (or Ladle) for component development, with `axe-core` integration for component-level a11y CI.
- **Bundle-size budget** ≤ 50 KB gzipped for the chat widget initial bundle (NFR5 enforcement).
- **Code-split chat widget** via Next.js dynamic import; does not ship on existing platform pages where unused.

**Eval harness infrastructure:**

- **Ground Truth Set** ≥ 200 stratified queries across intents, skill levels, categories. Authored with skate domain expert sign-off.
- LLM-judge runs production-grade reasoning model with structured rubric (relevance, accuracy, completeness, safety).
- 10% human inter-rater check on sampled entries.
- CI integration: every prompt/model/topology change triggers eval; lower-CI-bound < 85% blocks merge.

**Failure-mode matrix (Architecture deliverable):**

- Per-dependency policy (Anthropic API, Vertex AI, Cloud SQL primary, Cloud SQL replica, Firestore, Firebase Auth, cart API, account API, Memorystore Redis, Secret Manager, Langfuse, Cloud Trace, reCAPTCHA Enterprise) for: timeout, retry, circuit-breaker, user-visible degradation. **Implementing the matrix is launch-required** (NFR22, NFR25).

**Operational runbooks (NFR25, launch-blocking):**

- LLM provider outage (circuit-breaker activation procedure)
- Firebase Auth outage
- Postgres pool saturation
- Runaway-cost incident response
- Eval-harness CI failure triage

### UX Design Requirements

UX-DRs are extracted as discrete, story-shaped items per Step-1 instructions ("each UX-DR must be specific enough to generate a story with testable acceptance criteria"). Components, design system foundations, and patterns each get their own UX-DR.

**Custom components (UX-DR1–UX-DR13):**

- **UX-DR1: `ChatInput` component.** Persistent embedded chat input. Three variants: header-embedded (compact, single-line), bottom-docked (mobile, larger touch target, safe-area-respect), full-route-expanded (multi-line). Rotating placeholder among 3–4 example prompts. Global `/` keyboard shortcut. Stays focused after submit. WCAG 2.2 AA conformant.
- **UX-DR2: `ConversationStream` component.** Vertical thread with role-distinct alignment (user right, assistant left). `aria-live="polite"` on streaming region only (not static thread). Auto-scroll to bottom only when at bottom. Cross-device hydration anchor. Two variants: in-context, full-route.
- **UX-DR3: `RecommendationCard` component.** Hero image → product name → sticker tags → why-this rationale → mono price → CTA. Five states (skeleton, streaming, final, out-of-stock, low-confidence). Three variants (standard, lead with 1.25× hero on desktop + accent shadow + "Best balance" flag, compact for compare).
- **UX-DR4: `SetupCardStack` component.** Signature pattern. Header strip (lead flag · setup name · total price · CompatibilityChip) → 3-up product sub-cards (deck, trucks, wheels) → unified rationale → single CTA. Stacks vertically on mobile, horizontal grid on desktop (768 px+). Includes `partially-out-of-stock` state.
- **UX-DR5: `CompatibilityChip` component.** Pill with check icon + label using `grounded` token. Three variants: setup-validated, pairs-with, works-with-yours (Phase 2). Color-independent (icon + text + border).
- **UX-DR6: `WhyThisRationale` component.** Text block (1–3 sentences) for recommendation explanation. Three states (skeleton, streaming token-by-token fill, final). Two variants (standard, expanded for compare).
- **UX-DR7: `ConfidenceBoundaryDisclosure` component.** `surface-overlay` background, 3 px `uncertain` left-border, uppercase label, body copy. `role="note"` (never `role="alert"`). Three variants (partial-match, limited-catalog-data, no-confidence).
- **UX-DR8: `StickerTag` component.** Small uppercase pill, bold display font, 0.1em tracking. Three states (default, in-stock with grounded color, out-of-stock with strikethrough). Three variants (attribute, stock, brand).
- **UX-DR9: `CartAddBottomSheet` / `CartAddInlineConfirmation` component.** Mobile bottom-sheet (with grip indicator, drag-to-dismiss) and desktop inline panel sharing content (action title, SKU list with mono prices, total row, primary CTA, secondary "Keep looking" CTA). Focus trap, Escape close, `role="dialog"`. Three variants (single-item, setup-add, composite).
- **UX-DR10: `DegradedModePanel` component.** Eyebrow ("Assistant temporarily unavailable") → heading ("Search by keyword while the assistant is busy.") → search input pre-filled with last query → search button → calm body copy. `role="status"` (not `role="alert"`). Two variants (full-replacement, inline).
- **UX-DR11: `ClarificationTurn` component.** Small assistant-message bubble with clarifying question + 2–4 quick-reply chips + "Skip — give me your best guess" affordance. Visually distinct from recommendation turns. Two variants (single-question, multi-slot).
- **UX-DR12: `AIDisclosurePill` component.** Small uppercase pill with green-dot indicator, label "Assistant" / "Search Mode" by state. Tooltip on hover/focus reveals fuller AI disclosure; click opens FAQ modal.
- **UX-DR13: Internal admin surfaces (`OpsDashboard*` + `RuleAuthoringSurfaces*`).** Five components: `RelevanceDashboard` (Priya), `PerAgentEvalSlice` (Priya), `RuleFiringDashboard` (Tariq), `RuleDetail` (Tariq), `PromptChangeAuditLog` (Priya). Denser layout than consumer surfaces; keyboard-first.

**Design system foundation (UX-DR14–UX-DR16):**

- **UX-DR14: Design token system.** Implement Tailwind CSS v4 token configuration with the committed semantic palette (surface, surface-elevated, surface-overlay, text-primary/secondary/muted, border, border-subtle, accent=Signal Red `#F03A3A`, grounded, uncertain, error). Both **dark default** and **light theme** variants share component code via CSS variables. Spacing scale (4 px base, tokens space-1 through space-16). Radius scale (none/sm/full only). Touch-target floor 44 × 44 px.
- **UX-DR15: Typography system.** Three families: Geist Sans (display + text via weight) and Geist Mono (numeric attributes). Type scale tokens (display-1, display-2, headline-1/2, body-large, body, caption, tag, mono-body, mono-caption). Variable fonts loaded via `next/font/google`.
- **UX-DR16: Iconography system.** Lucide line icons as default + small set of skate-specific custom glyphs (deck silhouette, truck profile, wheel circle) used only for compatibility indicators. SVG-based. Icons never standalone (always paired with text or `aria-label`).

**UX patterns (UX-DR17–UX-DR20):**

- **UX-DR17: Streaming UX pattern.** Implement `useStreamingText` hook used by `RecommendationCard`, `SetupCardStack`, `WhyThisRationale`, `ClarificationTurn`. Skeleton-then-stream sequence (skeleton renders immediately on submit; streaming begins as SSE tokens arrive). 2 px accent vertical-bar cursor at streaming edge on active region. `prefers-reduced-motion: reduce` honored — instant render. Live region announces final summary, never per-token.
- **UX-DR18: Conversation pattern.** User messages right-aligned with accent background + white text (display verbatim, no markdown). Assistant messages left-aligned with no bubble (markdown supported, strong-tagged opener allowed). Recommendation cards rendered inline within assistant turn (not separate messages). Timestamps on hover (desktop) or long-press (mobile). Cross-device hydration on session resume invisible to user (no "Welcome back!" performance).
- **UX-DR19: Honest-confidence pattern.** When Compatibility Layer returns `partial-match` or `limited-catalog-data` verdict, render `ConfidenceBoundaryDisclosure` inline alongside the affected recommendation card (never alone, never instead of recommendation). Copy template: *"I matched on **[X]**, but **[Y]**. **[Implication]**."* Declarative, never apologetic, no hedging language. Distinct visual register from error states.
- **UX-DR20: Direction A "Calm Floor" with selective borrowings.** Implement the chosen visual direction across all consumer surfaces: airy density, sharp-edged cards (rounded-none), subtle SetupCardStack grouping (shared border + accent header strip), generous whitespace. **Selective borrowings:** sticker-tag treatment on attribute chips (from Direction B), 1.25× hero on the lead recommendation card on desktop only (from Direction C). Reference HTML mockup (`ux-design-directions.html`) as the visual contract.

**Cross-cutting accessibility, responsiveness, and platform (UX-DR21–UX-DR23):**

- **UX-DR21: WCAG 2.2 AA conformance across all consumer surfaces.** Color contrast ≥ 4.5:1 body / ≥ 3:1 large text; focus indicators 2 px outline ≥ 3:1; keyboard navigation Tab/Shift-Tab + skip-to-main link + `/` chat shortcut; `aria-live="polite"` for streaming with final-summary announcement; required `alt` on every product image; touch targets ≥ 44 × 44 px lint-enforced; `prefers-reduced-motion` honored at hook level; color-independence (icon + text always paired); 200% zoom support; `forced-colors: active` rules for Windows High Contrast.
- **UX-DR22: Responsive layout across mobile (320–639 px), tablet (640–1023 px), desktop (≥ 1024 px) breakpoints.** Mobile-first cascading. Bottom-docked chat input on mobile with `env(safe-area-inset-bottom)`. Header-embedded on tablet+. Single-column → 2-column → 12-column grid progression. SetupCardStack switches to horizontal at 768 px. Cart-add uses bottom-sheet on mobile and inline panel on desktop.
- **UX-DR23: Existing platform integration UX.** Chat widget code-split + lazy-loaded — does not ship on existing platform pages where the user has not engaged the assistant. SSR performance on host pages must not regress > 50 ms TTFB. Widget mounts as embedded affordance in the global header on existing pages; dedicated `/chat` route exists for full-screen experience. "See more like this" affordance hands off to a filtered PLP without losing chat context.

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR1 | Epic 1 | Natural-language intent submission |
| FR2 | Epic 1 | Multi-turn conversation within session |
| FR3 | Epic 3 | Clarifying questions when intent underspecified |
| FR4 | Epic 3 | Refinement via natural language |
| FR5 | Epic 3 | Graceful decline with confidence boundaries |
| FR6 | Epic 1 | Anonymous engagement |
| FR7 | Epic 3 | Side-by-side product comparison |
| FR8 | Epic 1 | Structured intent extraction |
| FR9 | Epic 1 | Catalog retrieval using extracted intent |
| FR10 | Epic 1 | Single-product recommendation |
| FR11 | Epic 1 | Complete-setup recommendation |
| FR12 | Epic 1 | Skater-vernacular rationale with trade-offs |
| FR13 | Epic 1 | Streaming explanation |
| FR14 | Epic 1 | Early-acknowledgement signal (TTFT < 1s) |
| FR15 | Epic 1 | Grounding (no hallucinated SKUs) |
| FR16 | Epic 1 | Compatibility Layer validation on every setup |
| FR17 | Epic 3 | Reject candidates with missing required attributes |
| FR18 | Epic 3 | Repair invalid setup with substitutions |
| FR19 | Epic 3 | Confidence-boundary disclosure |
| FR20 | Epic 3 | Catalog-quality backfill queue logging |
| FR21 | Epic 1 | Detail review before cart action |
| FR22 | Epic 1 | Confirm-add single product |
| FR23 | Epic 1 | Confirm-add complete setup (single action) |
| FR24 | Epic 1 | All-or-nothing setup add semantics |
| FR25 | Epic 1 | Confirmation-gated mutations only |
| FR26 | Epic 1 | No checkout / payments / orders / inventory access |
| FR27 | Epic 1 | Anonymous parity on recommendation quality |
| FR28 | Epic 2 | Firebase Auth identity verification |
| FR29 | Epic 2 | Persisted conversations across sessions |
| FR30 | Epic 2 | Cross-device session resume |
| FR31 | Epic 2 | History-based personalization |
| FR32 | Epic 1 | Anonymous rate limits + cost caps |
| FR33 | Epic 1 | Per-trace telemetry pipeline |
| FR34 | Epic 4 | AI Ops aggregate-metrics dashboards |
| FR35 | Epic 1 | LLM-judge eval harness on prompt/model/topology change |
| FR36 | Epic 4 | Per-agent eval slice for regression localization |
| FR37 | Epic 1 | CI eval gate blocks below-threshold merges |
| FR38 | Epic 1 | Per-turn iteration / token / wall-clock caps |
| FR39 | Epic 5 | Compatibility-rule authoring schema |
| FR40 | Epic 5 | PR workflow rule submission |
| FR41 | Epic 5 | Rule version + owner + effective date metadata |
| FR42 | Epic 5 | Per-rule firing metrics dashboard |
| FR43 | Epic 1 | AI assistant disclosure on first interaction |
| FR44 | Epic 2 | Authenticated-user history opt-out |
| FR45 | Epic 2 | Conversation history deletion request |
| FR46 | Epic 2 | 30-day retention + PII-stripped analytics |
| FR47 | Epic 2 | No raw queries joined to user IDs |
| FR48 | Epic 1 | LLM circuit-breaker → keyword-search fallback |
| FR49 | Epic 1 | Degraded-mode response with reason code |
| FR50 | Epic 1 | Architectural non-coupling (assistant outage ≠ site outage) |

**All 50 FRs assigned. Coverage complete.**

## Epic List

### Epic 1: Anonymous Discovery → Cart (Maya's defining experience)

**User outcome:** An anonymous user types a plain-language sentence about what they want, receives compatibility-validated setup recommendations within seconds, and confirms one to cart in a single action — without authentication, without learning catalog vocabulary, without leaving the chat surface. Includes the foundational scaffolding (project bootstrap, GCP infrastructure, design tokens, observability + eval-harness scaffolding) needed to ship safely, plus the LLM-degraded-mode fallback for launch readiness.

**FRs covered:** FR1, FR2, FR6, FR8–FR16, FR21–FR27, FR32, FR33, FR35, FR37, FR38, FR43, FR48–FR50

**Standalone:** Ships a working anonymous-only assistant with degraded-mode fallback. Production-shippable on its own as a v1.0.0 release.

### Epic 2: Authenticated Continuity (Sam's journey)

**User outcome:** A returning, signed-in user has their conversation persisted across sessions and devices, receives history-personalized recommendations, and can opt out of conversation history or request deletion. Auth is purely additive — Epic 1's anonymous flow continues to work unchanged.

**FRs covered:** FR28, FR29, FR30, FR31, FR44, FR45, FR46, FR47

**Standalone:** Builds on Epic 1's foundation but does not require Epic 3, 4, or 5 to function. Ships as v1.1.0.

### Epic 3: Honest Confidence & Refinement (Diego's journey)

**User outcome:** When the catalog has gaps or the user's intent is ambiguous, the system discloses its confidence boundaries calmly (rather than silently dropping candidates) and lets the user refine, compare, or clarify. Lifts the assistant from "works on the happy path" to "is honest about its boundaries."

**FRs covered:** FR3, FR4, FR5, FR7, FR17, FR18, FR19, FR20

**Standalone:** Builds on Epic 1's Compatibility Layer. Without Epic 3, Epic 1 still functions but with cruder fallback copy ("no recommendations available; refine your search") instead of the Diego-grade *"I matched on X, but don't have Y yet"* disclosure. Ships as v1.2.0.

### Epic 4: AI Operations Surfaces (Priya's journey)

**User outcome:** The on-call AI/ML Ops engineer has dashboards for relevance, latency, cost, grounding, and cache efficacy; can localize a regression to a specific agent on a model upgrade; and has a prompt-change audit log. Eval-harness CI gate already ships in Epic 1 — this epic adds the operator UIs and per-agent eval slicing.

**FRs covered:** FR34, FR36

**Standalone:** Builds on Epic 1's eval-harness scaffolding + per-trace telemetry. Without Epic 4, the eval gate still blocks bad merges, but ops engineers debug via raw Langfuse traces rather than purpose-built dashboards. Ships as v1.3.0 (or earlier as an internal tool).

### Epic 5: Compatibility Rule Operations (Tariq's journey)

**User outcome:** A skate domain expert can author new compatibility rules in a structured format, submit them through a PR workflow, see them deploy and enforce live, and observe per-rule firing metrics on a dashboard. Compatibility Layer schema and seed rules already ship in Epic 1; this epic adds the authoring + operations surfaces.

**FRs covered:** FR39, FR40, FR41, FR42

**Standalone:** Builds on Epic 1's Compatibility Layer. Without Epic 5, rule authoring works through the bare Git/PR flow — Epic 5 adds the per-rule firing dashboard and any tooling beyond a code editor + GitHub. Ships as v1.4.0 (or earlier as an internal tool).

## Epic 1: Anonymous Discovery → Cart (Maya's defining experience)

**Goal:** An anonymous user types a plain-language sentence, receives compatibility-validated setup recommendations within seconds, and confirms one to cart in a single action. Includes foundational scaffolding (project bootstrap, GCP infrastructure, design tokens, observability + eval-harness scaffolding) plus LLM-degraded-mode fallback for launch readiness.

### Story 1.1: Project Foundation & GCP Infrastructure

As a development team,
I want the project scaffolded with all required GCP infrastructure provisioned via Terraform,
So that subsequent stories build on a verified, reproducible foundation.

**Acceptance Criteria:**

**Given** a new GCP project with billing enabled
**When** Terraform plan and apply runs from the IaC repository
**Then** VPC, Secret Manager, Artifact Registry, and per-purpose IAM service accounts (Cloud Run runtime, CI, Migration Job) exist with least-privilege roles
**And** Terraform state is stored in a managed GCS backend with versioning enabled

**Given** the foundation is provisioned
**When** `pnpm create next-app` and `uv init` + FastAPI + ADK scaffolds complete
**Then** both projects build cleanly and deploy successfully (Vercel preview for frontend, Cloud Run staging for backend)
**And** `/health` and `/readiness` endpoints return 200 with structured JSON

**Given** the projects exist
**When** a PR is opened
**Then** GitHub Actions CI runs lint + typecheck + container build + vulnerability scan + staging deploy
**And** failures block merge

**Given** the deployed staging service
**When** any HTTP request hits it
**Then** trace IDs appear in Cloud Trace and structured logs in Cloud Logging

### Story 1.2: Cloud SQL Provisioning + Alembic Initial Schema + CI Gate

As a development team,
I want Cloud SQL provisioned with Alembic-managed schema migrations and CI gates,
So that all schema changes flow through versioned, reversible migrations from day one with zero drift.

**Acceptance Criteria:**

**Given** the GCP foundation exists
**When** Terraform provisions Cloud SQL Postgres 16 (HA primary + read replica)
**Then** the database is reachable via private IP from Cloud Run with `assistant_read_only` and `assistant_read_write` roles created
**And** automatic backups (35-day retention) and PITR are enabled

**Given** Cloud SQL exists
**When** `alembic upgrade head` runs the initial migration
**Then** baseline tables are created (`alembic_version`, `audit_log` placeholder)
**And** the migration is fully reversible (`downgrade -1` returns to baseline)

**Given** an Alembic migration is committed in a PR
**When** the migration CI gate runs
**Then** CI executes `upgrade head` → `downgrade -1` → `upgrade head` and any failure blocks merge

**Given** the FastAPI service starts
**When** the application boots
**Then** it queries `alembic_version`; if the schema version does not match the application's expected version, the service refuses to start with a clear error logged to Cloud Logging

**Given** a deploy is in progress
**When** the new Cloud Run revision is created
**Then** a separate Cloud Run Job runs `alembic upgrade head` to completion before traffic shifts to the new revision

### Story 1.3: Design System Foundation

As a frontend developer,
I want the design token system, typography, base components, and accessibility tooling configured,
So that every subsequent UI story builds on consistent tokens with axe-core a11y CI from day one.

**Acceptance Criteria:**

**Given** the Next.js project exists
**When** Tailwind v4 is configured with semantic palette tokens (surface, surface-elevated, surface-overlay, text-primary/secondary/muted, border, accent=Signal Red `#F03A3A`, grounded, uncertain, error)
**Then** dark and light theme variants share component code via CSS variables
**And** `prefers-color-scheme` is honored on first visit with manual-override persistence

**Given** the design system is configured
**When** Geist Sans + Geist Mono are loaded via `next/font/google` and the type scale tokens (display-1/2, headline-1/2, body-large, body, caption, tag, mono-body, mono-caption) are defined
**Then** typography is referenceable in any component without raw font-size or font-family values

**Given** Storybook is configured with shadcn/ui starter components installed (Button, Input, Dialog, Sheet, Toast, Tabs, Tooltip, Popover, Accordion, Skeleton, ScrollArea, Avatar, Badge, Card, Switch, Select, Separator, DropdownMenu)
**When** stories exist for each component
**Then** axe-core runs against every story in CI and merge is blocked on a11y violations

**Given** any interactive element is added
**When** ESLint runs in CI
**Then** the custom touch-target lint rule fails the build for any `<button>`, `<a>`, or Radix-derived interactive control with computed dimensions < 44 × 44 px

**Given** all design tokens are committed
**When** the contrast-lint job runs
**Then** any text-on-surface combination below WCAG 2.2 AA threshold for its size class fails the build

### Story 1.4: Anonymous Session & Chat Surface Shell

As an anonymous visitor,
I want the chat input visible and usable on every page without authentication,
So that I can ask the assistant a question immediately on first visit.

**Acceptance Criteria:**

**Given** I land on any page of the platform
**When** I view the global header (desktop) or bottom of the viewport (mobile)
**Then** the ChatInput component is visible with a rotating placeholder among 3-4 example prompts
**And** the AIDisclosurePill displays "Assistant" with an active indicator

**Given** I am on desktop and not focused on any input
**When** I press the `/` key
**Then** focus moves to the ChatInput
**And** the placeholder is read as a label to screen readers via visually-hidden `<label>`

**Given** I am an anonymous user with no existing session
**When** I submit my first message
**Then** the frontend obtains a server-issued anonymous session JWT (UUID v4 + HS256, 1h-from-last-activity expiry) carried in an httpOnly + secure + sameSite=lax cookie
**And** subsequent requests carry this session ID

**Given** an anonymous session exists
**When** I view the ConversationStream
**Then** user messages render right-aligned (accent background, white text); assistant messages render left-aligned without bubble background
**And** the stream supports `aria-live="polite"` on streaming regions only (not the static thread)

**Given** I am at 320 px viewport width
**When** I interact with ChatInput
**Then** the input is bottom-docked with `env(safe-area-inset-bottom)` respected
**And** all touch targets are ≥ 44 × 44 px

### Story 1.5: Chat Turn Endpoint + SSE Delivery Contract

As the backend service,
I want a versioned chat-turn endpoint with a strict SSE delivery contract,
So that the frontend can consume tokens reliably with ordering, deduplication, and resume semantics.

**Acceptance Criteria:**

**Given** the FastAPI service is running
**When** a POST to `/v1/chat/turn` arrives with a valid Firebase ID token or anonymous session JWT
**Then** the service authenticates, validates the request body against a Pydantic schema, generates a `turn_id`, and opens an SSE response

**Given** an SSE stream is open
**When** any event is emitted
**Then** it carries `event_id` (monotonic integer per turn) and `turn_id` (stable per turn) in the payload
**And** the SSE-native `id:` field is set to `event_id`
**And** the server emits `: heartbeat` keepalive every 15 seconds during long pauses

**Given** the SSE stream drops mid-turn
**When** the client reconnects with `Last-Event-ID: <id>`
**Then** the server resumes from `event_id + 1` for that `turn_id`
**And** turns abandoned > 5 minutes return a documented error code

**Given** an error occurs during a turn
**When** the orchestrator emits the terminal event
**Then** the response is exactly one `done` OR one `error` event (never both, never neither)

**Given** any error response
**When** the structured error envelope is emitted
**Then** it contains `{ code, message, request_id, retry_after?, details? }` matching HTTP status code semantics from the project-type spec

### Story 1.6: IntentAgent (Vertex Gemini Flash) + Early Acknowledgement

As the assistant,
I want a fast IntentAgent that extracts typed intent from natural-language input and emits an early acknowledgement,
So that users see a response token within 1 second of submitting (NFR2).

**Acceptance Criteria:**

**Given** a user message arrives at the orchestrator
**When** the IntentAgent runs
**Then** it calls Vertex AI Gemini Flash via `services/llm.py` and returns a typed `Intent` Pydantic object with style, skill, terrain, budget, attribute filters, and clarification-needed flag

**Given** the IntentAgent is processing
**When** the orchestrator detects the request has begun
**Then** an early-acknowledgement `token` SSE event is emitted ≤ 1 second from request acceptance with a confident on-brand line ("Got it — pulling some setups for that.")

**Given** an Intent is extracted
**When** it is passed to downstream agents
**Then** it conforms exactly to the Intent Pydantic schema (no ad-hoc dicts), and validation failures raise a typed `IntentValidationError`

**Given** any LLM call from `services/llm.py`
**When** the call completes
**Then** a per-call cost record is emitted with model, prompt tokens, completion tokens, and cost-cents, observable via Langfuse

### Story 1.7: Catalog Read & Parallel Retrieval Agents

As the assistant,
I want to retrieve candidate products from the catalog in parallel based on the extracted intent,
So that the latency budget for retrieval stays within ≤ 400 ms (slowest branch) per NFR3.

**Acceptance Criteria:**

**Given** Cloud SQL read-replica access is provisioned with `assistant_read_only` role
**When** the backend starts
**Then** it connects to the catalog read replica via Cloud SQL Connector
**And** `app/models/catalog.py` defines a versioned read-only SQLAlchemy view of catalog tables

**Given** an Intent is available
**When** the orchestrator runs `ParallelAgent` fan-out
**Then** DeckRetrievalAgent, TruckRetrievalAgent, and WheelRetrievalAgent each issue concurrent SQL queries against the read replica

**Given** the parallel retrieval completes
**When** the orchestrator collects results
**Then** the slowest branch returns within 400 ms P95
**And** each branch yields a list of `RetrievalCandidate` Pydantic objects with SKU + retrieved attributes + provenance

**Given** any retrieval branch fails or times out
**When** the orchestrator handles the partial result
**Then** the system continues with available candidates and logs the failure to Langfuse, never silently drops the turn

### Story 1.8: Compatibility Layer (Schema + Service + Seed Rules + CompatibilityAgent)

As the assistant,
I want a deterministic Compatibility Layer that validates every recommended setup,
So that no LLM-emitted SKU can bypass compatibility validation (FR16, NFR38).

**Acceptance Criteria:**

**Given** an Alembic migration is run
**When** the schema is applied
**Then** Postgres tables `compatibility_rule`, `compatibility_rule_version`, and `compatibility_rule_metric` exist with explicit `version`, `owner`, `effective_at`, `superseded_by` fields and CHECK constraints on rule integrity

**Given** the rules service is loaded
**When** `compatibility/service.py` evaluates a candidate set
**Then** it returns one of three verdicts per candidate (accept, repair, reject) with a `CompatibilityVerdict` Pydantic object including `rule_refs`

**Given** the seed rules are loaded
**When** the system starts
**Then** at least 5 expert-authored rules exist covering deck-width ↔ truck-width pairing, durometer ↔ terrain mapping, riding-style → setup archetypes, and stock/price guardrails

**Given** the orchestrator includes the CompatibilityAgent in the topology
**When** any candidate set passes through the pipeline
**Then** the LLM cannot skip CompatibilityAgent (architecturally enforced via SequentialAgent ordering)
**And** per-candidate verdicts are emitted as `compatibility_verdict` SSE events (debug-only in production)

### Story 1.9: ExplanationAgent (Anthropic Claude Sonnet) + Streaming + Grounding

As the assistant,
I want an ExplanationAgent that streams natural-language rationale tied to user intent and grounds every cited SKU in the catalog,
So that the user sees a coherent explanation built up token-by-token with zero hallucinated SKUs (FR15, NFR38).

**Acceptance Criteria:**

**Given** a validated candidate set is available
**When** the ExplanationAgent runs
**Then** it calls Anthropic Claude Sonnet via `services/llm.py` with a prompt-cached system+domain prefix (using `cache_control`)
**And** the call returns a structured `Recommendation` Pydantic object via tool-use / structured output

**Given** the ExplanationAgent is producing the rationale
**When** tokens stream from Anthropic
**Then** each token is emitted as a `token` SSE event in real time with `event_id` and `turn_id`
**And** the `recommendation` event is emitted once per complete card

**Given** prompt caching is configured
**When** repeated requests share the system+domain prefix within 5 minutes
**Then** the cache hit is observable in Langfuse via per-call cost reduction

**Given** the rationale text is generated
**When** it is validated against the structured-output schema
**Then** every recommended SKU exists in the catalog with the claimed attributes (zero-hallucination grounding check)
**And** any failure raises a typed `GroundingViolationError`

### Story 1.10: Recommendation Components (Card + Rationale + Sticker + Compat Chip + Streaming Hook)

As an anonymous user,
I want recommendation cards to render with progressive token-fill and clear product information,
So that I see the assistant working and can scan the result quickly (UX-DR3, UX-DR5, UX-DR6, UX-DR8, UX-DR17).

**Acceptance Criteria:**

**Given** an SSE stream begins
**When** the first `recommendation` event arrives
**Then** a RecommendationCard renders with hero image, product name (headline-2), sticker-tag row, why-this rationale region (initially skeleton), price (mono-body), and primary CTA

**Given** the rationale text is streaming
**When** tokens arrive
**Then** the WhyThisRationale region fills text left-to-right via the `useStreamingText` hook
**And** a 2 px accent vertical-bar cursor appears at the streaming edge until completion

**Given** the user has `prefers-reduced-motion: reduce` set
**When** streaming would normally animate
**Then** the text renders instantly without animation
**And** the cursor does not blink

**Given** a recommendation is validated as compatible
**When** the card renders
**Then** the CompatibilityChip displays "Pairs with [size]" using the `grounded` token (color + check icon + text — color-independent)
**And** sticker tags display style/skill/stock attributes via the StickerTag component

**Given** the card is rendered to assistive technology
**When** streaming completes
**Then** the live region announces a single completion summary ("Three setups available"), not every streamed token

### Story 1.11: SetupCardStack — Signature Pattern

As an anonymous user,
I want complete deck+trucks+wheels setups to render as a single visually-grouped buyable unit,
So that I can review and confirm the entire setup with one action (UX-DR4).

**Acceptance Criteria:**

**Given** the orchestrator produces a complete-setup recommendation
**When** the SetupCardStack renders
**Then** it shows a header strip (lead flag if applicable, setup name, total price as mono, CompatibilityChip "Setup validated"), three sub-cards (deck, trucks, wheels) with hero + name + sticker tags + per-item price, a unified WhyThisRationale, and a single primary CTA "Add complete setup · $XXX.XX"

**Given** I am on a 320 px mobile viewport
**When** the SetupCardStack renders
**Then** the three sub-cards stack vertically and the CTA sits at the bottom
**And** all interactive elements are ≥ 44 × 44 px

**Given** I am on a desktop ≥ 1024 px
**When** the SetupCardStack renders
**Then** the three sub-cards arrange in a horizontal grid with shared borders
**And** the lead recommendation card uses a 1.25× hero image with a 1 px accent shadow

**Given** any sub-card has a stock-zero attribute
**When** the SetupCardStack renders
**Then** the card displays "Out of stock" sticker, the CTA reads "Out of stock — see alternatives", and the partially-out-of-stock state is announced to screen readers

### Story 1.12: Cart-Add Flow (Bottom Sheet + Inline + Adapter + Audit Log + Mutation Allow-List)

As an anonymous user,
I want to confirm a recommendation and add it to the existing cart in one action,
So that I never have to leave the chat surface to make a purchase decision (FR21–FR26, UX-DR9).

**Acceptance Criteria:**

**Given** I tap "Add complete setup" on a SetupCardStack
**When** I am on mobile
**Then** a CartAddBottomSheet appears with grip indicator, action title ("Add this setup?"), SKU list (full names + mono prices), divider, total row (uppercase label + larger value), primary CTA, and secondary "Keep looking"
**And** focus is trapped to the sheet with Escape close

**Given** I am on desktop
**When** I tap the same CTA
**Then** a CartAddInlineConfirmation panel renders inline with equivalent content and keyboard-equivalent dismissal

**Given** I confirm "Add to cart"
**When** the request fires
**Then** `app/services/cart_client.py` posts to the existing cart API with an `Idempotency-Key` header (UUID v4) and all-or-nothing setup-add semantics
**And** an audit log row is written to `cart_mutation_audit` with hashed user ID, session ID, timestamp, SKU set, recommendation source, idempotency key

**Given** the cart-add succeeds
**When** the response arrives
**Then** a calm confirmation toast displays "Setup added · View cart" for ≥ 4 seconds and is dismissible

**Given** any agent code attempts a tool call to a non-cart-add endpoint
**When** the gateway middleware sees the request
**Then** the request is rejected with a structured `403 MUTATION_NOT_ALLOWED` error
**And** the violation is logged to Cloud Logging

### Story 1.13: Rate Limits, Cost Caps & Anonymous Abuse Mitigation

As the platform operator,
I want layered rate limits, cost caps, and anonymous abuse mitigation,
So that anonymous traffic cannot drive cost incidents or consume unfair shares of capacity (FR32, NFR7, NFR18, NFR23).

**Acceptance Criteria:**

**Given** Memorystore Redis is provisioned (Standard HA, 5 GB)
**When** any request arrives at the FastAPI middleware
**Then** the gateway applies a token-bucket rate limit per anonymous session ID + per IP (anonymous tier: stricter; authenticated tier: higher) tied to chat turns AND cart mutations as separate buckets

**Given** the orchestrator processes a turn
**When** it invokes any LLM call
**Then** per-session iteration / token / wall-clock caps are enforced before the call, and exceeding any cap halts the turn with a documented error code

**Given** Cloud Armor is configured
**When** traffic arrives at the edge
**Then** IP-based DDoS / bot detection is enforced before requests reach Cloud Run

**Given** an anonymous session hits the rate limit ≥ 3 times in an hour or matches bot-signature heuristics
**When** the next request arrives
**Then** reCAPTCHA Enterprise is invoked with adaptive scoring and challenge presented to the user

**Given** any request exceeds rate limits or cost caps
**When** the response is sent
**Then** it returns HTTP `429` with both `Retry-After` header and `retry_after` field in the structured error envelope

### Story 1.14: Semantic Cache (Memorystore Redis + Vertex Embeddings)

As the platform operator,
I want a semantic cache fronting IntentAgent extractions on head queries,
So that we hit the per-session cost target ≤ $0.05 P95 and reach the ≥ 40% cache hit rate by week 4 (NFR18, NFR39).

**Acceptance Criteria:**

**Given** an Intent extraction request arrives
**When** the IntentAgent first runs
**Then** it computes a Vertex AI text-embedding-005 embedding of the normalized user query, and checks Redis (separate keyspace from rate-limit) for a similarity-matched cached Intent

**Given** a cached Intent is found above the configured similarity threshold
**When** the cache hit is validated
**Then** the IntentAgent returns the cached Intent without calling Gemini Flash, emitting a `cache_hit: true` field in the trace

**Given** a fresh Intent is extracted
**When** the call succeeds
**Then** the Intent + embedding are written to Redis with a TTL aligned to catalog change cadence

**Given** the catalog changes (new SKUs, deprecated SKUs)
**When** a configured periodic revalidation triggers
**Then** cache entries older than the revalidation window are evicted to prevent stale serving

**Given** Redis is unreachable
**When** the cache call fails
**Then** the system bypasses the cache (logs failure, increments a metric) and falls through to the LLM call without blocking the user

### Story 1.15: Observability Foundation (Langfuse + OpenTelemetry)

As an AI Ops engineer,
I want per-trace observability for every chat turn including cost, latency, and agent decisions,
So that I can debug production behavior from day one (FR33, NFR36).

**Acceptance Criteria:**

**Given** Langfuse is self-hosted on Cloud Run with its own Cloud SQL instance
**When** the backend starts
**Then** the Langfuse SDK is initialized with API key from Secret Manager
**And** every LLM call from `services/llm.py` emits a Langfuse trace with prompt, completion, model, tokens, cost, and latency

**Given** OpenTelemetry instrumentation is configured
**When** any agent or service is invoked
**Then** spans are emitted to both Langfuse and Cloud Trace (dual-emit), tagged with `agent_path`, `service_name`, and `request_id`

**Given** any conversational turn is processed
**When** the turn completes
**Then** a per-trace record exists with: agent path taken, per-stage latency (intent / retrieval / compat / explanation), total token cost, tool-call counts, hashed user ID, cache hit/miss for both prompt and semantic cache, compatibility verdict counts

**Given** Cloud Logging and Cloud Monitoring are configured
**When** any request emits structured logs
**Then** logs include `request_id`, `hashed_user_id`, `status`, `duration_ms`, and `agent_path`
**And** logs are queryable in Cloud Logging UI without raw stack traces

**Given** observability emission fails
**When** Langfuse or Cloud Trace is unavailable
**Then** the failure is logged but never blocks the user request (fire-and-forget, buffered)

### Story 1.16: Eval Harness Scaffolding + Ground Truth Set + CI Gate

As an AI Ops engineer,
I want an LLM-judge eval harness with a curated Ground Truth Set running in CI,
So that prompt or model regressions are caught before merge (FR35, FR37, NFR37, NFR40).

**Acceptance Criteria:**

**Given** the eval harness scaffolding exists in `tests/eval/`
**When** the harness is invoked
**Then** it loads a Ground Truth Set of ≥ 200 stratified queries from YAML/JSON files (intents × skill levels × categories), each with a documented author and review date

**Given** the harness runs
**When** the LLM-judge evaluates a recommendation
**Then** it uses a structured rubric (relevance, accuracy, completeness, safety) and emits a per-query score plus an aggregate relevance percentage with 95% CI

**Given** a PR modifies any prompt, model selection, or agent topology file
**When** GitHub Actions CI runs
**Then** the eval harness executes against staging
**And** a result with lower-bound-95%-CI < 85% blocks merge

**Given** the eval completes
**When** results are emitted
**Then** per-agent eval slices are produced (intent / retrieval / compatibility / explanation) so regressions can be localized to a single agent

**Given** eval results exist
**When** Priya inspects them
**Then** she can view results in Langfuse with prompt-completion-eval-score linkage

### Story 1.17: LLM Circuit-Breaker + DegradedModePanel

As an anonymous user,
I want a graceful degradation experience when the LLM provider is unavailable,
So that I can still search the platform without seeing scary error messages (FR48, FR49, FR50, NFR22, UX-DR10).

**Acceptance Criteria:**

**Given** `services/llm.py` is wired with circuit-breaker logic per provider
**When** sustained provider error rate > 10% over 1 minute OR P99 TTFT > 5 s for 30 seconds is detected
**Then** the circuit breaker trips and subsequent calls return `503 LLM_DEGRADED` with a documented machine-readable reason code

**Given** the circuit-breaker has tripped
**When** the frontend receives a `503 LLM_DEGRADED` response
**Then** the chat surface renders the DegradedModePanel (full-replacement variant) with eyebrow "Assistant temporarily unavailable", heading "Search by keyword while the assistant is busy.", search input pre-filled with the user's last query, and a Search button

**Given** the user submits the search input
**When** the search button is clicked
**Then** the user is redirected to the existing platform's keyword search with the query as input
**And** the search result page renders normally

**Given** the circuit breaker is tripped
**When** the configured cooldown period elapses
**Then** the breaker enters a half-open state and probes the LLM provider; on success, normal flow resumes

**Given** the assistant is in degraded mode
**When** the existing platform pages (browse, cart, checkout) are accessed
**Then** they function normally (architectural non-coupling — assistant outage does not affect site operation)

### Story 1.18: Pre-Launch Hardening — Load Test, Runbooks, A11y Audit, Canary Deploy

As the platform operator,
I want pre-launch hardening completed before the assistant ships to production,
So that the launch is safe, observable, and recoverable (NFR16, NFR25, NFR26).

**Acceptance Criteria:**

**Given** the staging environment is provisioned
**When** a load test runs at 2,000 peak concurrent simulated users via locust or k6
**Then** P95 latency stays < 3 s, TTFT < 1 s, and provider rate-limit headroom remains ≥ 2× peak
**And** failures block production deploy

**Given** the launch is approaching
**When** runbook authoring is completed
**Then** runbooks exist and are accessible for: LLM provider outage (circuit-breaker activation procedure), Firebase Auth outage, Postgres pool saturation, runaway-cost incident response, eval-harness CI failure triage

**Given** the consumer surfaces are complete
**When** a manual accessibility audit is performed by VoiceOver (iOS Safari + macOS Safari) and NVDA (Firefox + Windows)
**Then** every primary user flow (Maya's happy path) is completable
**And** any blockers are resolved before launch

**Given** the production release is ready
**When** GitHub Actions deploys to production
**Then** the deploy uses a canary at 10% traffic for 30 minutes
**And** is auto-promoted to 100% only on green eval, latency, and zero-hallucinated-SKU metrics

**Given** any hardening item fails
**When** the launch readiness review is run
**Then** the launch is blocked until the failure is resolved

## Epic 2: Authenticated Continuity (Sam's journey)

**Goal:** A returning, signed-in user has their conversation persisted across sessions and devices, receives history-personalized recommendations, and can opt out of conversation history or request deletion. Auth is purely additive — Epic 1's anonymous flow continues to work unchanged.

### Story 2.1: Firebase Auth Integration + ID-Token Verification

As an authenticated user,
I want my Firebase identity verified on every request,
So that the assistant knows who I am and can apply per-user limits and personalization (FR28, NFR6, NFR34).

**Acceptance Criteria:**

**Given** Firebase Auth is configured for the project
**When** the frontend signs in a user via the Firebase client SDK
**Then** an ID token is obtained, attached to all backend requests as `Authorization: Bearer <token>`
**And** the token is automatically refreshed by the SDK before expiry

**Given** the FastAPI middleware receives a request with an ID token
**When** the middleware verifies via `firebase-admin`
**Then** verification uses JWKS with 5-minute cache
**And** `request.state.user_id` is populated on success

**Given** an expired or invalid token
**When** verification fails
**Then** the response is `401` with `{ "code": "TOKEN_EXPIRED" }` or appropriate code
**And** the frontend triggers Firebase SDK refresh and retries once

**Given** a user is authenticated
**When** rate-limit middleware applies
**Then** authenticated tier limits (higher than anonymous) are used keyed on `user_id`

### Story 2.2: Firestore Session + Message Persistence

As an authenticated user,
I want my conversations persisted to Firestore,
So that I can return later and find my message history intact (FR29, NFR24, NFR35).

**Acceptance Criteria:**

**Given** an authenticated user completes a chat turn
**When** SSE streaming finishes
**Then** the completed assistant message + recommendations + metadata are durably written to Firestore at `users/{user_id}/sessions/{session_id}/messages/{message_id}` with retry on transient failure
**And** the client only acknowledges turn-complete after the durable write succeeds

**Given** a turn is interrupted between SSE-complete and Firestore-write
**When** an out-of-band reconciliation job runs
**Then** orphaned in-memory turns are detected and either committed or marked failed within 5 minutes

**Given** Firestore security rules
**When** any client reads `users/{user_id}/...`
**Then** rules enforce the requesting user's `auth.uid` matches the path; cross-user reads are denied at the rule layer

**Given** a Firestore write fails after exhausting retries
**When** the user views the chat
**Then** a non-blocking toast displays "Session sync delayed" and the in-memory state remains usable

### Story 2.3: Cross-Device Session Resume

As an authenticated user,
I want my conversation to resume invisibly on a different device,
So that I can pick up where I left off without re-prompting or "Welcome back!" performance (FR30, UX-DR18).

**Acceptance Criteria:**

**Given** I have an in-progress conversation on desktop
**When** I open the platform on my phone (signed in as the same Firebase user)
**Then** the last N messages from Firestore are hydrated and rendered on first paint
**And** the chat surface shows no "Resuming…" or modal performance

**Given** Firestore listeners are attached to my session document
**When** any change occurs (new message from another device, session opt-out toggle)
**Then** the UI updates within 1 second on the other device(s) without manual refresh

**Given** I do not have an authenticated session on a device
**When** I open that device
**Then** a fresh anonymous session begins and no authenticated history leaks into it

### Story 2.4: History-Based Personalization

As an authenticated returning user,
I want recommendations that reference my recent orders and current cart,
So that the assistant feels like it knows what I already own (FR31, NFR33).

**Acceptance Criteria:**

**Given** I am authenticated
**When** the IntentAgent processes a turn
**Then** it fetches `recent_orders` and `current_cart_contents` via the existing platform's user-account API (`app/services/account_client.py`) using my Firebase ID token

**Given** account-context data is available
**When** the ExplanationAgent generates a recommendation
**Then** the rationale may reference owned products explicitly (e.g., "For your Welcome Wax 8.5"…")

**Given** the account API call fails or times out
**When** the orchestrator handles the failure
**Then** personalization gracefully degrades — recommendations still ship without referencing prior orders, no user-visible error

**Given** I have not authorized data sharing
**When** the orchestrator queries account context
**Then** no PII data is included in prompts sent to the LLM provider beyond what is operationally necessary; hashed identifiers are used in observability traces

### Story 2.5: Conversation History Opt-Out & Deletion

As an authenticated user,
I want to disable persistent conversation history or delete my history on request,
So that I have control over what data the assistant retains about me (FR44, FR45).

**Acceptance Criteria:**

**Given** I am authenticated
**When** I open the user menu and toggle "Save conversation history" off
**Then** the toggle state is persisted to my user profile and subsequent turns are not written to Firestore
**And** the AIDisclosurePill or settings indicator reflects the opt-out state

**Given** I have opted out
**When** I submit a chat turn
**Then** the turn is processed as usual but no message persistence occurs (in-memory only for the duration of the turn); no Firestore write is attempted

**Given** I request deletion via the settings UI
**When** I confirm "Delete all conversation history"
**Then** all `users/{user_id}/sessions/...` documents are deleted from Firestore within the documented retention SLA
**And** a confirmation message displays "Your conversation history has been deleted"

**Given** an active session is present at deletion time
**When** the deletion runs
**Then** the in-memory session state is also reset; the user sees a fresh chat surface

### Story 2.6: Retention Job + PII-Stripped Analytics

As the platform operator,
I want conversation logs retained for no more than 30 days and analytics PII-stripped,
So that the Data & Privacy Baseline is operational from launch (FR46, FR47, NFR12).

**Acceptance Criteria:**

**Given** Cloud Scheduler is configured with a daily retention job
**When** the job runs
**Then** Firestore documents under `users/{user_id}/sessions/{session_id}/messages/...` older than 30 days are deleted
**And** the deletion count is logged to Cloud Monitoring

**Given** an analytics export pipeline exists
**When** events are exported for aggregate analysis
**Then** raw free-text user queries are not joined to user identifiers; only hashed identifiers (HMAC-SHA256 with rotating salt) are present
**And** PII fields (email, phone, address) are scrubbed before export

**Given** a deletion request is honored under FR45
**When** retention windows complete
**Then** no analytics record retains a recoverable link from a deleted user's data to that user

**Given** the retention job fails for any reason
**When** the failure is detected
**Then** the on-call team is alerted via Cloud Monitoring within 15 minutes

## Epic 3: Honest Confidence & Refinement (Diego's journey)

**Goal:** When the catalog has gaps or the user's intent is ambiguous, the system discloses its confidence boundaries calmly (rather than silently dropping candidates) and lets the user refine, compare, or clarify. Lifts the assistant from "works on the happy path" to "is honest about its boundaries."

### Story 3.1: ConfidenceBoundaryDisclosure Component + Honest-Confidence Pattern

As a domain-savvy user,
I want the system to disclose calmly when it has imperfect data,
So that I can trust its recommendations when it does have full data (FR19, UX-DR7, UX-DR19).

**Acceptance Criteria:**

**Given** the Compatibility Layer returns `partial-match` or `limited-catalog-data` on a candidate
**When** the recommendation is rendered to the user
**Then** a `ConfidenceBoundaryDisclosure` component is rendered inline, attached to the affected card, with `surface-overlay` background, 3 px `uncertain` left-border, uppercase label ("Partial match" / "Limited catalog data"), and 1–3 sentences of body copy

**Given** the disclosure renders
**When** assistive technology navigates it
**Then** it is announced as `role="note"` (NEVER `role="alert"`)
**And** the label and body text are read together as a single semantic unit

**Given** the disclosure copy is generated
**When** the explainer composes it
**Then** the template follows: *"I matched on [X], but [Y]. [Implication]."* — declarative, never apologetic, no hedging language ("we think", "maybe")

**Given** a recommendation has reduced confidence
**When** the system ships it
**Then** the recommendation is **never dropped** — it is shown alongside the disclosure
**And** the disclosure visual register is distinct from `error` styling (different token, different copy register)

### Story 3.2: Catalog-Quality Backfill Queue

As a merchandising / catalog-management team,
I want missing-attribute occurrences logged for backfill,
So that the catalog improves over time without manual triage (FR20).

**Acceptance Criteria:**

**Given** an Alembic migration is run
**When** the schema is applied
**Then** a `catalog_quality_backfill` table exists with columns: `sku`, `missing_attributes` (JSON array), `intent_context` (JSON), `occurrence_count`, `last_seen_at`, with a unique constraint on (`sku`, `missing_attributes`) for upsert semantics

**Given** the CompatibilityAgent encounters a candidate with NULL on a required attribute
**When** the rejection or partial-match path executes
**Then** a row is upserted to `catalog_quality_backfill`

**Given** the same SKU + missing attribute combination occurs multiple times
**When** the log entry already exists
**Then** the row's `occurrence_count` is incremented and `last_seen_at` is updated rather than inserting a duplicate

**Given** a Phase 2 dashboard surfaces this queue (out-of-scope here; deferred)
**When** the table is queryable from the catalog-management surface
**Then** the underlying data is structured cleanly enough that a future dashboard query is trivial

### Story 3.3: Compatibility Layer Repair & Reject Logic

As the assistant,
I want the Compatibility Layer to repair invalid setups by substituting compatible alternatives where possible,
So that users get the best valid setup the catalog can offer (FR17, FR18).

**Acceptance Criteria:**

**Given** the CompatibilityAgent evaluates a candidate setup with one invalid component
**When** a substitution is possible (alternative SKU exists that satisfies the same intent constraint with valid attributes)
**Then** the verdict is `repair` and the substituted SKU is reflected in the final Recommendation

**Given** no valid substitution exists
**When** the CompatibilityAgent evaluates
**Then** the verdict is `reject` and the candidate is excluded from setup recommendations
**And** the candidate may still appear as a single-item recommendation if other intent attributes are matched

**Given** a candidate has a NULL on a required attribute
**When** evaluation runs
**Then** the candidate is rejected from setup recommendations and logged to the catalog-quality backfill queue (Story 3.2)

**Given** repair operations occurred
**When** the response is delivered
**Then** the user sees the repaired setup naturally, with no UI indication that a repair happened (the system handled it silently — only `reject` triggers a `ConfidenceBoundaryDisclosure`)

### Story 3.4: ClarificationTurn Component + Clarification Flow

As an anonymous user with an ambiguous query,
I want the assistant to ask one short clarifying question rather than guess,
So that I get a recommendation that actually matches what I meant (FR3, UX-DR11).

**Acceptance Criteria:**

**Given** the IntentAgent extracts intent with `clarification_needed: true`
**When** the orchestrator processes the turn
**Then** instead of running retrieval, it emits a `clarification` SSE event with `{ "question": "...", "quick_replies": [...] }`

**Given** the frontend receives a `clarification` event
**When** the ClarificationTurn component renders
**Then** a small assistant-message bubble shows the clarifying question
**And** 2–4 quick-reply chips display below
**And** a "Skip — give me your best guess" affordance is visible

**Given** I tap a quick-reply chip
**When** the value is submitted
**Then** a follow-up chat turn fires with the answer attached to the prior intent context, and the assistant proceeds to recommendations

**Given** I tap "Skip — give me your best guess"
**When** the action fires
**Then** the IntentAgent is re-invoked with a "best-guess" flag and proceeds to recommendation regardless

**Given** the clarification turn is rendered to assistive technology
**When** screen-reader users navigate
**Then** the question is read in normal reading order and the chips are real `<button>` elements with `aria-label`

### Story 3.5: Refinement Turns

As any user with an existing recommendation,
I want to type "show me cheaper" or "for park instead" and have the assistant refine,
So that I don't have to start over for adjustments (FR4).

**Acceptance Criteria:**

**Given** a recommendation has been delivered in the current session
**When** I send a new message that the IntentAgent recognizes as a refinement (e.g., "cheaper", "for park", "lighter")
**Then** the orchestrator merges the refinement constraint with the prior intent context and runs retrieval/explanation against the merged intent

**Given** a refinement is applied
**When** the response renders
**Then** new recommendations are shown that respect both the original intent and the refinement
**And** the user can chain multiple refinements within the session

**Given** I am at refinement turn N within a session
**When** I send a new "fresh" intent (not a refinement)
**Then** the assistant detects the topic shift and resets the intent context, treating the message as a new conversation thread

### Story 3.6: Side-by-Side Compare Turn

As any user reviewing multiple options,
I want to ask "compare these side by side" and see them in a structured comparison,
So that I can decide between similar candidates quickly (FR7).

**Acceptance Criteria:**

**Given** the assistant has delivered ≥ 2 recommendations in the current turn or recent history
**When** I send a message that the IntentAgent classifies as a compare request
**Then** the orchestrator runs a comparison-explanation flow that emits a `recommendation` event with the `compact` variant for each compared product

**Given** the compare layout renders
**When** I view the comparison
**Then** product images, prices, and key attributes (deck width, durometer, etc.) are aligned in a tabular layout that reads clearly on both mobile and desktop

**Given** the compare view is rendered
**When** I scroll or interact
**Then** I can tap any product to expand to its full recommendation detail or add to cart from the compare context

### Story 3.7: Graceful Decline & Off-Topic Redirect

As a user with an off-topic or unanswerable query,
I want the assistant to decline politely and offer a redirect,
So that I'm not left confused or rejected with shame register (FR5).

**Acceptance Criteria:**

**Given** the IntentAgent classifies the input as off-topic (not skate-gear-related)
**When** the orchestrator processes the turn
**Then** the assistant returns a calm decline + redirect: *"I help with skate gear — want me to suggest a setup, or are you looking for something else on the site?"*
**And** the response uses the same calm visual register as success states (no error styling)

**Given** the catalog cannot satisfy the user's stated intent at all (no matching SKUs)
**When** the orchestrator detects this
**Then** the response includes a `ConfidenceBoundaryDisclosure` (limited-catalog-data variant) explaining what was searched and what was not found
**And** offers refinement or clarification next steps

**Given** any decline or redirect occurs
**When** rendered
**Then** no apologetic copy ("Sorry, I can't…") is used
**And** no `role="alert"` is applied — the response is `role="status"` with `aria-live="polite"`

## Epic 4: AI Operations Surfaces (Priya's journey)

**Goal:** The on-call AI/ML Ops engineer has dashboards for relevance, latency, cost, grounding, and cache efficacy; can localize a regression to a specific agent on a model upgrade; and has a prompt-change audit log. Eval-harness CI gate already ships in Epic 1 — this epic adds the operator UIs and per-agent eval slicing.

### Story 4.1: Internal Admin App Shell + Auth

As an AI Ops engineer,
I want an internal admin surface separate from the consumer app, with appropriate auth gating,
So that operator tools live in a dedicated, secure surface (UX-DR13).

**Acceptance Criteria:**

**Given** the Next.js project structure is committed
**When** an internal admin route group is added (e.g., `app/(admin)/...`)
**Then** routes under that group require authenticated Firebase Auth users with an `admin: true` custom claim
**And** non-admin users redirect to an unauthorized page

**Given** the admin shell exists
**When** an admin user signs in
**Then** the admin layout renders with left nav (Relevance, Per-Agent Eval, Prompt Audit, Rules — Epic 5) and the consumer chat UI is not loaded
**And** the design tokens are reused from the consumer design system

**Given** the admin shell is loaded
**When** an admin lands on the home admin route
**Then** they see a default operational summary (recent eval results, active circuit-breaker state)

### Story 4.2: RelevanceDashboard Component

As Priya, the on-call AI Ops engineer,
I want a dashboard with aggregate relevance, latency, cost, grounding, and cache metrics,
So that I can see system health at a glance and drill into anomalies (FR34).

**Acceptance Criteria:**

**Given** the RelevanceDashboard component exists
**When** I open the admin Relevance route
**Then** I see metric cards for: relevance % (lower-CI bound, last 24h), P95 latency end-to-end, P95 TTFT, per-session cost P95, hallucinated-SKU count (must be 0), prompt-cache hit rate, semantic-cache hit rate, runaway-loop incident count

**Given** a time-range selector is available
**When** I change the range (last hour, last 24h, last 7d, last 30d)
**Then** all metrics update to reflect the selected range

**Given** I click any metric card
**When** the drill-down opens
**Then** I see per-trace records linked to Langfuse for that metric (e.g., the 10 longest-latency traces in the last 24h)

**Given** the dashboard fetches data
**When** the underlying metric source (Langfuse / Cloud Monitoring) is unavailable
**Then** the card shows "Data unavailable" with a calm `uncertain` token treatment, not an error alarm

### Story 4.3: PerAgentEvalSlice Component

As Priya,
I want eval results sliced per-agent (intent, retrieval, compatibility, explanation),
So that I can localize a regression to a specific agent on a quarterly model upgrade (FR36, NFR41).

**Acceptance Criteria:**

**Given** an eval CI run completes
**When** the run emits results
**Then** per-agent eval scores are computed and stored, with delta-from-baseline calculated against the last green production run

**Given** I open the Per-Agent Eval admin route
**When** the page loads
**Then** I see a stacked view showing relevance % per agent (intent / retrieval / compatibility / explanation) for the last N runs
**And** delta-from-baseline indicators (green/red, sized by delta magnitude)

**Given** I click an agent's slice
**When** the drill-down opens
**Then** I see the GTS queries that scored worst on that agent, with per-query rubric scores and links to Langfuse traces

**Given** an agent's eval drops below the per-agent threshold
**When** CI runs
**Then** the merge is blocked AND a Cloud Monitoring alert fires to the on-call channel

### Story 4.4: PromptChangeAuditLog Component

As Priya,
I want a chronological log of prompt and model changes with diff view,
So that I can correlate eval regressions with specific changes (NFR41).

**Acceptance Criteria:**

**Given** any prompt or model configuration change is committed
**When** the change is merged to the prompts repository
**Then** an entry is written to a prompt audit table with: commit SHA, author, timestamp, file path, prompt diff (before/after), eval delta from prior run

**Given** I open the Prompt Audit admin route
**When** the page loads
**Then** I see a chronological list of audit entries with date, author, commit SHA, files changed, and eval delta

**Given** I click an audit entry
**When** the diff view opens
**Then** I see the prompt before/after side-by-side, the eval scores from the run that included this change, and any agent-level eval deltas

**Given** an entry's eval delta is negative beyond a threshold
**When** the audit log is reviewed
**Then** the entry is highlighted as a regression candidate

## Epic 5: Compatibility Rule Operations (Tariq's journey)

**Goal:** A skate domain expert can author new compatibility rules in a structured format, submit them through a PR workflow, see them deploy and enforce live, and observe per-rule firing metrics on a dashboard. Compatibility Layer schema and seed rules already ship in Epic 1; this epic adds the authoring + operations surfaces.

### Story 5.1: Rule Authoring Documentation + PR Template + Lint

As Tariq, a skate domain expert authoring compatibility rules,
I want clear documentation, a PR template, and lint validation,
So that I can author a new rule with confidence it will integrate correctly (FR39, FR40, FR41).

**Acceptance Criteria:**

**Given** the rule schema is documented
**When** I open the rule-authoring guide in the project repo
**Then** I see: rule schema definition (Pydantic model with field-level docs), example rules, conventions for `version`, `owner`, `effective_at`, and a step-by-step authoring walkthrough

**Given** I author a new rule
**When** I open a PR with the new rule file
**Then** a PR template guides me to fill in: rule purpose, expected impact on recommendations, manual test cases, and reviewer (engineer + co-domain expert)

**Given** I submit the PR
**When** CI runs the rule-lint job
**Then** the rule is validated against the schema (Pydantic), syntactic correctness, version uniqueness, and required metadata fields
**And** any failure provides actionable error messages without raw stack traces

**Given** the PR passes review and merges
**When** the next deploy runs
**Then** the rule is loaded into the Compatibility Layer at startup, versioned, owner-attributed, and effective from the deploy timestamp

### Story 5.2: RuleFiringDashboard Component

As Tariq,
I want a dashboard showing how often each rule fires and what verdicts it produces,
So that I can see whether my rules are catching real issues or are dead code (FR42).

**Acceptance Criteria:**

**Given** a `RuleFiringDashboard` component exists in the admin app
**When** I open the Rules route
**Then** I see a list of all active compatibility rules with columns: rule name, version, owner, applied count (last 24h), accept/repair/reject distribution, sparkline showing trend

**Given** the underlying `compatibility_rule_metric` table is populated
**When** the dashboard queries it
**Then** counts reflect real-time data (within 1 minute lag)

**Given** I sort by any column
**When** I click a column header
**Then** the list re-sorts (e.g., most-fired rules first, or rules with highest reject rate first)

**Given** I see a rule that has fired 0 times in 30 days
**When** I review it
**Then** the rule is visually flagged as potentially-dead-code; a hover tooltip explains the heuristic

### Story 5.3: RuleDetail Component + Version History

As Tariq,
I want a single-rule view with its version history and per-rule firing graph,
So that I can audit a specific rule's evolution and impact (FR41, FR42).

**Acceptance Criteria:**

**Given** I click a rule in the RuleFiringDashboard
**When** the RuleDetail page loads
**Then** I see: rule definition (full schema as code), version history (all `compatibility_rule_version` rows for this rule with author, effective_at, superseded_by), per-rule firing graph (last 30 days), recent rejections with sample SKUs

**Given** I navigate to a prior version
**When** I click a version row
**Then** I see the rule definition at that version and any associated context

**Given** I want to retire a rule
**When** I open a PR that sets `superseded_by` on the active version
**Then** after merge and deploy, the rule no longer fires for new evaluations
**And** the dashboard reflects the retired status with appropriate visual treatment
