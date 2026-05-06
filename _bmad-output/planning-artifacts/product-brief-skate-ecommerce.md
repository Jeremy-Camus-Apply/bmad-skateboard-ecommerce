---
title: "Product Brief: skate-ecommerce — AI Shopping Assistant"
status: "complete"
created: "2026-05-06"
updated: "2026-05-06"
inputs: []
---

# Product Brief: AI Shopping Assistant for skate-ecommerce

## Executive Summary

The skate-ecommerce platform has a structured product catalog, working accounts, and a conventional search/browse UI, but no AI capabilities. Catalog navigation assumes the user already knows what they want — a poor fit for skateboarding, where buying intent is most often expressed in terms of *use* ("a durable street setup for tricks", "wheels good for cruising on rough sidewalks") rather than SKUs or attributes.

This brief specifies an AI-powered Shopping Assistant that acts as a conversational layer over the existing catalog. It interprets natural-language intent, asks clarifying questions when needed (skill, terrain, budget), reasons about product compatibility (deck width ↔ truck width, durometer ↔ terrain), and recommends individual products *or* complete setups (deck + trucks + wheels) that the user can review and add to cart in one action. Checkout, payments, and order management remain unchanged in the existing platform.

The system is best framed as **deterministic commerce with an LLM front door**: an LLM reasons about user intent and explanations, but every product cited is grounded in the catalog and every recommendation is validated by a deterministic Compatibility Layer. The assistant is built as a multi-agent system on Google's Agent Development Kit (ADK) with a Python backend, a Next.js frontend, PostgreSQL for the catalog and Compatibility Layer, and Firebase for authentication and realtime session state. It is designed to operate at 50,000 DAU / 2,000 peak concurrent users, ~3 prompts per session, with a P95 end-to-end latency target of <3s and TTFT <1s for the streamed explanation.

## The Problem

Skate buyers experience two distinct frictions on a conventional e-commerce UI:

1. **Vocabulary gap.** The user knows the *outcome* they want — a durable board for street tricks, wheels that cruise rough pavement, a beginner-friendly complete — but not the catalog vocabulary (deck width in inches, wheel durometer, truck axle width). Faceted search and keyword search both assume the user can translate intent into attributes; many cannot, and bounce.
2. **Compatibility ignorance.** A skateboard is a system: deck width constrains truck width; wheel diameter and durometer interact with terrain and deck shape. The current platform sells parts independently and gives the user no signal when their selections will not work well together. This produces returns, dissatisfaction, and lost cross-sell on complete-setup attach.

Both frictions hurt conversion (search → cart) and product discovery (cross-category). The status quo absorbs the cost as bounced sessions, undersized carts, and incompatible-setup returns.

## The Solution

A conversational assistant, available to anonymous and authenticated users, that:

- Accepts natural-language requests and asks targeted clarifying questions (multi-turn slot-filling) when the intent is underspecified.
- Maps intent → structured catalog attributes via LLM-driven extraction, then retrieves candidates with structured SQL filters (not vector search) against the existing 10k-SKU catalog.
- Validates every recommendation against a deterministic **Compatibility Layer** so that proposed setups are physically valid (deck ↔ truck ↔ wheel rules) and so that no recommended SKU is hallucinated.
- Explains its recommendations in skate vernacular, including trade-offs (durability vs. weight, beginner vs. advanced, street vs. cruising).
- **Proposes** add-to-cart actions for individual products or complete deck+trucks+wheels setups; the user **confirms** before any cart write occurs. The assistant never autonomously mutates cart, account, or order state.
- Persists session state and conversation history (for authenticated users) so a session can resume across devices, with realtime UI updates pushed via Firebase.

## The Compatibility Layer

The Compatibility Layer is the load-bearing component of this system and the most important non-LLM design decision. It is what turns "knowledgeable shop expert" from a prompt aspiration into a system property.

**What it is.** A deterministic, versioned ruleset implemented as a small set of PostgreSQL tables plus a thin service. Rules encode skate-domain truths such as:
- *Deck width 8.0–8.25" pairs with trucks 139–149mm axle (Independent sizing) or 144–149mm (Thunder).*
- *Wheels 99a–101a durometer suit street/park; 78a–87a suit cruising/rough terrain.*
- *Wheel diameter ≤56mm preferred for street to clear deck-to-wheel bite at typical truck heights.*

**Where it sits in the request flow.** Between retrieval and explanation. The LLM proposes intent + constraints; the Compatibility Layer enforces validity on every candidate before the explainer ever sees it.

**Authorship and review.** Rules are owned by this system, not by the existing platform. Authoring is reviewable by skate domain experts (pro shop staff or partner brands); each rule is versioned, has an owner, and ships through code review like any other artifact.

**Behavior on missing data.** When a candidate SKU has NULL on an attribute the rule requires, the candidate is rejected from setup recommendations and logged to a catalog-quality backfill queue (see *Roadmap*). It may still appear as a single-item recommendation if other attributes match the intent.

**Why deterministic, not learned.** Skate compatibility is a small, stable, explicit knowledge domain. Encoding it as rules is cheaper, more auditable, and far easier to defend ("who decided 8.0 deck pairs with 139 trucks?") than a learned model. The Compatibility Layer also enables non-chat surfaces — PLP "works with" badges, cart upsell nudges — to reuse the same logic at zero LLM cost.

## What Makes This Different

This is not a search-rewrite or a thin LLM wrapper. Four design choices give it the shape of a knowledgeable shop expert rather than a smarter search bar:

- **Deterministic Compatibility Layer as a first-class component.** See dedicated section above. The mechanism that makes "0 hallucinated SKUs" a system guarantee, not a model behavior we hope holds.
- **Intent-first, structured-retrieval-second.** A small/fast LLM extracts intent into a typed JSON filter against PostgreSQL. Vector search is deliberately *not* in the critical path for attribute-driven queries; RAG is used only on unstructured content (reviews, technique guides). This is materially faster and more accurate than embedding-only retrieval for known-attribute lookups, and is the pattern Instacart and similar production systems converged on.
- **Multi-agent specialization with deterministic orchestration.** ADK workflow agents (Sequential / Parallel) provide non-LLM control flow as guardrails around per-specialty LLM agents (intent, recommendation, compatibility, explanation). Each agent has an isolated context window and is independently evaluable. (See *Multi-Agent Justification*.)
- **Latency and cost engineered into the architecture, not hoped for.** Tiered models (fast/small for routing & extraction; reasoning model for explanation), prompt caching on the stable system+domain prefix, semantic caching on head queries, parallel tool execution, and token streaming. The latency budget is decomposed at sub-component granularity (see *System Architecture Overview*) — engineered, not aspirational.

## Who This Serves

**Primary user — anonymous discovery shopper.** A potential buyer who lands on the platform with intent expressed in plain language and no skate domain vocabulary. They are top-of-funnel, may not have an account, and abandon quickly if friction is high. Anonymous use is supported, with rate limiting and abuse protection on the API edge. **Anonymous-to-cart conversion is the headline business signal this assistant exists to move.**

**Secondary user — authenticated returning shopper.** A signed-in user (Firebase Auth) whose past interactions and current cart can be used as additional personalization signals. They benefit from cross-device session continuity (resume conversation on phone) backed by Firebase realtime listeners.

A third audience — the platform itself — is served indirectly: the assistant is read-mostly against the catalog, write-bounded to a single user-confirmed cart-add operation, and never modifies orders, inventory, or account state.

## Multi-Agent Justification

A core constraint of this work is that the architecture be multi-agent, and the justification must be substantive rather than nominal. We use a multi-agent design for three concrete reasons; absent these, a single agent with tools would be the correct choice (and is what well-known production systems such as Shopify Sidekick advocate by default).

1. **Per-agent evaluability and survival of quarterly model upgrades.** An LLM-judge eval harness with a curated Ground Truth Set is required to enforce the relevance and 0-hallucinated-SKU success criteria. Specialized agents (intent classifier, recommender, compatibility validator, explainer) are each independently testable; regressions on a model upgrade can be localized to one agent and remediated without touching the rest. In a monolithic ReAct loop, a model regression manifests as a global quality drop with no clean attribution.

2. **Context isolation across catalog scopes.** Reasoning about a complete deck+trucks+wheels setup requires retrieved data from three distinct catalog scopes plus the compatibility ruleset. Loading all of this into a single agent's context inflates tokens, raises latency, and lowers reasoning quality. Parallel ADK subagents (deck, trucks, wheels) operate in tight context windows with their own retrieval; their outputs are merged for final reasoning. This is also what makes parallel SQL/tool execution natural.

3. **Deterministic guardrails via workflow agents.** ADK's `SequentialAgent` and `ParallelAgent` give us non-LLM control flow at the orchestration boundary. The path "intake → parallel retrieval → compatibility validation → grounded explanation" is deterministic by construction; the LLM cannot skip the compatibility validator. This is the architectural mechanism that enforces "0 hallucinated SKUs" as a system property.

**Falsifiability clause.** This justification is engineering-driven, not dogmatic. The architecture commits to multi-agent because the three reasons above are believed to be true at this scale. If pre-launch evaluation shows that (a) per-agent isolation contributes <2% absolute relevance gain over a single-agent + tools baseline, **and** (b) orchestration latency exceeds 200ms at P95, the team will reopen the topology decision in a documented Architecture Decision Record. Multi-agent is the bet, not the religion.

What is *not* multi-agent in this design: simple FAQs, single-attribute lookups, and idle chitchat are handled inside a single agent. We do not multiply agents where a tool call suffices.

## System Architecture Overview

High-level view (full architecture lives in the Architecture document; this section establishes shape, contracts, and budget).

**Agent topology and per-turn flow.**

```
User turn (HTTP/SSE) →
  IntentAgent (small/fast model, structured output)
    ├─ if intent underspecified → return clarifying question (END turn)
    └─ if intent complete:
        ParallelAgent (per-scope retrieval, fan-out)
          ├─ DeckRetrievalAgent  (SQL on Postgres)
          ├─ TruckRetrievalAgent (SQL on Postgres)
          └─ WheelRetrievalAgent (SQL on Postgres)
        → CompatibilityAgent (calls Compatibility Layer; rejects/repairs)
        → ExplanationAgent (reasoning model, streamed via SSE)
        → [optional] CartAgent — invoked only on user confirmation
                                  of a recommendation, not autonomously.
```

The clarification path short-circuits past retrieval and explanation. CartAgent is never invoked by the LLM unprompted; the user clicks/confirms in the UI, the frontend issues an explicit cart-add intent, the backend invokes CartAgent against the existing cart API.

**Component layers.**
- **Frontend (Next.js).** Chat UI, anonymous + Firebase Auth sessions, ID-token bearer auth to the backend, SSE consumption for streaming explanations, Firestore listeners for session resume / cross-device continuity. Cart confirmations are explicit UI affordances, not implicit assistant actions.
- **Backend (Python, ADK).** Agent orchestration as above. Stateless request handlers behind a horizontally-scaled service. Per-user / per-session ADK session service is backed by a persistent store (not in-memory defaults — see *Risks*).
- **Data.**
  - **PostgreSQL** — product catalog (existing), Compatibility Layer tables, conversation/event metadata, embeddings via pgvector for unstructured RAG.
  - **Firebase Auth** — identity for authenticated users; Python verifies ID tokens via `firebase-admin`.
  - **Firestore** — message and session persistence as the system of record for chat history (after streaming completes), realtime listeners for cross-device continuity. Token streaming uses SSE direct from Python; Firestore is **not** used as a token bus.

**Existing-platform integration surface (read/write inventory).**
- **Catalog read** — the assistant reads catalog tables in the existing PostgreSQL instance. Protocol (direct DB read vs. internal API) is an Architecture decision; the brief assumes direct read with a dedicated read-only role.
- **Cart write** — the assistant writes via the existing cart API. The contract requires (a) idempotency keys per cart-add, (b) a batch endpoint or transactional client-side adapter for setup adds (3 SKUs in one action), and (c) all-or-nothing semantics for setup adds. If the existing API does not provide these, a thin adapter is built; this is not a project blocker.
- **User account read** — for authenticated personalization signals (recent orders, current cart contents). Read-only; mediated by Firebase Auth ID token + an account-read service.

**Mutation allow-list (explicit boundary).**
The assistant's only authorized mutation is `cart-add` (single item or 2- to 3-item setup) via the existing cart API, on user confirmation. All other potential mutations — order, inventory, user profile, payment, address — are explicitly forbidden at the tool-permission layer.

**Latency budget (P95 < 3s, TTFT < 1s for streamed explanation).**

| Stage | Type | Budget (P95) |
|---|---|---|
| Edge auth + token verify | serial | ≤ 80ms |
| Semantic-cache lookup (head queries) | serial | ≤ 50ms |
| IntentAgent (small/fast model, structured output, prompt-cached prefix) | serial | ≤ 600ms |
| ParallelAgent fan-in (slowest of N retrievals + tool RTT) | parallel | ≤ 400ms |
| Compatibility Layer evaluation | serial | ≤ 100ms |
| ExplanationAgent TTFT (streaming start, prompt-cached prefix) | serial | ≤ 800ms |
| Streaming remainder of explanation (typical 80–200 tokens) | streaming | ≤ 1000ms |

TTFT-to-user is the sum of the serial steps before streaming begins (~2.0s upstream + provider TTFT). This **does not** meet a strict <1s TTFT-to-user target on the main reasoning path. The brief commits to <1s TTFT for the **first user-visible token**, which is achieved by emitting an early acknowledgement / clarification token from a fast-model "thinking" stub while the upstream pipeline runs in parallel. End-to-end completion remains within the <3s P95 envelope. The detailed Gantt and per-stage P50/P95 (including provider tail latency) belong in the Architecture document.

**Capacity planning (must be confirmed in Architecture).** 50k DAU × 3 prompts/session × ~30s active window → sustained low-hundreds RPS with 2k peak concurrent. Required deliverables in Architecture: provider RPS headroom (rate limits at 2× peak), Postgres connection pool sizing (concurrent × parallel-fanout × agents), Firestore write QPS, SSE connection limits per backend instance, and budget for retry storms.

**Cost & reliability controls.** Hard caps per session on iterations, tokens, and wall-clock; loop detection (same tool, same args ≥3 times → halt); per-user and per-anonymous-session token-budget gate; full per-trace observability (cost, latency, tool calls, agent decisions). Observability vendor is a launch-blocker decision (see *Open Questions*).

**Data contracts at the four critical seams** (Pydantic / TypedDict, defined in Architecture; called out here because they are where the system will break in practice):
1. `Intent` — typed JSON of extracted user intent (style, skill, terrain, budget, attribute filters, clarification-needed flag).
2. `RetrievalCandidate` — single SKU + retrieved attributes + provenance (which retrieval call produced it).
3. `CompatibilityVerdict` — accepted / repaired / rejected, with rule references for explainability.
4. `Recommendation` — final user-facing object: one or more SKUs, rationale text, trade-offs, cart-add payload.

## Success Criteria

| Dimension | Metric | Target |
|---|---|---|
| Quality | Recommendation relevance via LLM-judge over Ground Truth Set | Lower bound of 95% CI ≥ 85% |
| Quality | Hallucinated SKUs (recommended product not present in catalog with claimed attributes) | 0 |
| Latency | End-to-end response | P95 < 3s |
| Latency | First user-visible token | < 1s |
| Engagement | CTR on assistant-recommended products vs. baseline search | +15% to +25% relative lift (provisional; validate via A/B) |
| Engagement | Setup attach rate (≥2 of 3 of deck/trucks/wheels in cart when assistant proposed a setup) | Baseline established at launch; 4-week target set in week 4 post-launch |
| Reliability | Runaway-loop incidents in production | 0 |
| Cost | Per-session cost (P95) | ≤ $0.05 (hard constraint) |
| Cost | Combined cache hit rate (prompt cache + semantic cache) on head queries | Instrumented from launch; ≥ 40% target by week 4 (realistic without historical data) |
| Secondary | Returns-rate reduction on assistant-recommended setups vs. non-assistant carts | Tracked as a secondary metric; not a launch KPI |

**Eval harness specification (launch blocker).**
- Ground Truth Set: ≥200 stratified queries spanning intents (recommendation, clarification, refinement, FAQ, off-topic), skill levels (beginner / intermediate / advanced), and categories (deck-only, wheels-only, trucks-only, complete setups, accessories).
- Authorship: skate domain expert sign-off on every entry; documented author and review date.
- Judge: production-grade reasoning model with a structured rubric (relevance, accuracy, completeness, safety). Inter-rater agreement spot-checked against human reviewers on a 10% sample.
- Statistical threshold: lower bound of 95% CI ≥ 85% relevance.
- CI gating: every prompt change, model upgrade, or agent topology change runs the eval; failures block merge.

All metrics are required to be observable in production via per-trace telemetry from launch.

## Scope

**In v1**
- Conversational discovery and recommendation
- Multi-turn clarification (skill, terrain, budget, riding style)
- Single-product and complete-setup recommendations
- User-confirmed add-to-cart (single items and full setups) via existing cart API
- Anonymous and authenticated usage
- Cross-device session continuity for authenticated users
- LLM-judge eval harness and per-trace observability
- English only

**Out of scope for v1** (explicit)
- Voice input/output
- Image-based search ("find a board that looks like this")
- Order tracking, returns, refunds
- Payments and checkout (handed off to existing system unchanged)
- Social, gamification, community features
- Multi-language support
- Any mutation outside the cart-add allow-list

## Data & Privacy Baseline (v1)

- **Data residency.** US, or region-aligned with the primary user base; configurable per deployment. LLM-provider region pinned to match.
- **Retention.**
  - Conversation logs: **30 days**, then deleted.
  - Aggregated analytics: retained beyond 30 days, **PII-stripped**.
- **PII handling.**
  - Raw free-text user queries are **not** stored alongside user identifiers.
  - Tokenization / anonymization applied before any analytics ingestion.
- **User control.**
  - Authenticated users can disable conversation history (opt-out).
  - Deletion-on-request flow honored within retention SLA.
- **Security.**
  - All authenticated requests carry a verified Firebase ID token.
  - Anonymous sessions are scoped, rate-limited, and cost-capped (see *Risks*).
- **Provider data flow.**
  - Prompts and tool inputs sent to the LLM provider are scrubbed of stored PII before transmission; per-trace observability captures hashed identifiers, not raw user IDs.

## Key Assumptions (must be validated during implementation)

1. **Catalog scale ≈ 10k SKUs** across decks, trucks, wheels, bearings, hardware, grip, completes, and apparel. Skewed distribution; head queries dominate.
2. **Catalog attributes available** include: deck width / length / concave / wheelbase; wheel diameter / durometer; truck width; brand, price, stock, category, riding-style tags. Coverage will not be complete; the assistant must degrade gracefully on missing attributes (see *Compatibility Layer*).
3. **Compatibility ruleset is owned by this system**, not the existing platform. Versioned, code-reviewed, expert-authored.
4. **Existing cart API supports** (or can be adapted to support) idempotent adds and all-or-nothing setup adds. If not natively supported, a thin server-side adapter is in scope.
5. **Direct PostgreSQL read access** to the existing catalog is available with a dedicated read-only role. To be confirmed (see *Open Questions*).
6. **ADK version selected** is verified against production-readiness caveats. LangGraph is retained as a fallback orchestrator within the same multi-agent topology if a blocking ADK issue surfaces.

## Open Questions (require decision before implementation)

- **Identity system of record.** Are existing user accounts already in Firebase Auth, or is a one-time migration required? Owner and target decision date to be set at PRD time.
- **Cart API capabilities.** Does the existing cart API support idempotency keys and batch / transactional setup adds, or is the adapter required?
- **Observability vendor.** Langfuse (self-hosted) vs. Arize Phoenix vs. LangSmith. Must be selected before launch; per-trace cost / latency / agent-decision tracing is a hard launch dependency.
- **Setup-attach-rate target.** Deferred to week 4 post-launch (no baseline available pre-launch). Confirm methodology at PRD time.

## Risks & Mitigations

- **Hallucinated specs / non-existent SKUs.** *Mitigation:* never let the LLM emit raw SKU or attribute values; every product cited must come from a tool result. The Compatibility Layer post-validates every recommendation, and a final grounding check ensures the SKU exists with the claimed attributes.
- **Prompt injection via product reviews and seller-supplied descriptions** ingested into the unstructured RAG path. *Mitigation:* all retrieved content treated as untrusted; tool-call permissions sandboxed (mutation allow-list); input/output guardrails; pre-launch pen-test of the assistant's tool surface.
- **Runaway agent loops driving cost incidents.** *Mitigation:* hard per-session caps on iterations, tokens, and wall-clock; loop detection; gateway-level token-budget enforcement.
- **ADK production-readiness caveats** (in-memory session defaults, per-user agent isolation patterns reported through 2025–early 2026). *Mitigation:* pin ADK version; wire a persistent session service from day one; validate per-user isolation under load; retain a LangGraph fallback path.
- **Anonymous-access abuse.** IP-based rate limiting alone is insufficient (CGNAT, corporate NAT, client-supplied session IDs). *Mitigation:* layered controls — token-bucket per anonymous session ID, per-IP rate limit, hard per-anonymous-session cost cap, CAPTCHA escalation on suspicious patterns, edge bot detection.
- **LLM provider outage or sustained tail-latency.** *Mitigation:* explicit fallback to non-AI search when the assistant cannot meet SLO — circuit breaker on provider error rate / TTFT P99 → frontend renders the existing search UI with the user's prompt as keyword input. Documented degradation path; not a launch blocker for the assistant itself.
- **Streaming-vs-persistence consistency window.** SSE streams to the user while Firestore persistence happens after stream completion; a write failure could lose the last assistant message. *Mitigation:* durable write with retry before client acknowledges turn complete; out-of-band reconciliation for any orphans.
- **Eval drift on model upgrades.** *Mitigation:* LLM-judge harness with curated GTS is a launch blocker, not a follow-up; CI gates on prompt and model changes.
- **Failure-mode matrix is required in the Architecture document** for each external dependency (LLM provider, Postgres, Firestore, Firebase Auth, cart API): timeout, retry policy, circuit-breaker behavior, user-visible degradation. The brief identifies the seams; the Architecture document must specify each.

## Roadmap Beyond v1

Concrete next steps once v1 is stable:

- **Catalog-quality feedback loop.** IntentAgent extractions that fail to match an attribute filter are already logged; surface them as a backfill queue for merchandising. The assistant becomes a catalog QA tool at zero marginal cost.
- **Compatibility Layer reuse beyond chat.** Power product-detail-page "works with" badges, PLP filter validation, and existing-cart setup-completion nudges with the same deterministic rules. A platform-wide trust layer.
- **Image-based search** ("looks like this") — visual discovery for users who cannot articulate what they want.
- **Personalization beyond session scope.** Long-term riding profile inferred from history; saved preferences.
- **Multi-language support** starting with Spanish and Portuguese (priority TBD by market).
- **Voice input** for mobile.
- **Outbound notifications via Firebase** ("we found 3 boards matching your saved query") — re-engagement channel using the realtime infrastructure already paid for in v1.
- **Post-purchase advisor** — setup tuning, replacement recommendations, technique guides keyed to owned products.

None of these are in v1. They are listed to make the v1 scope boundary explicit and to clarify what the assistant is *designed to grow into* — informing v1 architectural decisions today (e.g., the realtime infrastructure being designed to support future outbound notifications, and the eval harness being designed to amortize across all future agent additions).
