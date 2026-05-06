---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation-skipped
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
status: complete
completedAt: 2026-05-06
releaseMode: phased
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-skate-ecommerce.md
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 0
workflowType: 'prd'
classification:
  projectType:
    - web_app
    - api_backend
    - ai_application_layer
  domain:
    primary: e-commerce
    secondary: AI-assisted decision systems
  complexity: high
  drivers:
    - Multi-agent orchestration (ADK)
    - Hybrid deterministic (rules) + probabilistic (LLM) system
    - Real-time streaming requirements (SSE)
    - Cost-bounded inference at scale
    - Integration with existing commerce systems
  projectContext: brownfield-extension
---

# Product Requirements Document - skate-ecommerce AI Shopping Assistant

**Author:** Jeremycamusvarela
**Date:** 2026-05-06

## Executive Summary

The skate-ecommerce platform has a structured product catalog (~10k SKUs), Firebase-backed user accounts, a checkout system, and a conventional search/browse UI. It has no AI capabilities. This PRD specifies a new product — an AI-powered Shopping Assistant — that adds a conversational discovery and recommendation layer over the existing platform without modifying its checkout, payments, inventory, or order systems.

The assistant accepts natural-language requests, asks clarifying questions when the intent is underspecified (skill, terrain, budget, riding style), reasons about cross-product compatibility (deck width ↔ truck width, durometer ↔ terrain), and proposes individual products or complete deck+trucks+wheels setups that the user reviews and confirms before any cart write. It serves both anonymous (top-of-funnel discovery) and authenticated users; for authenticated users it persists session state for cross-device continuity.

It is built as a multi-agent system on Google's Agent Development Kit (ADK) with a Python backend, a Next.js frontend, PostgreSQL for the catalog and a deterministic Compatibility Layer, and Firebase for authentication and realtime session state. It is designed to operate at 50,000 DAU / 2,000 peak concurrent users / ~3 prompts/session, with P95 end-to-end latency < 3s, < 1s to first user-visible token, P95 cost per session ≤ $0.05, and zero hallucinated SKUs as a strict success criterion.

### What Makes This Special

The product is best framed as **deterministic commerce with an LLM front door**. Two concerns are separated rigorously and connected by deterministic orchestration:

- The **LLM** owns intent translation, clarification, and explanation — the messy human side, where natural-language reasoning is the right tool.
- A **deterministic Compatibility Layer** owns validity — encoding skate-domain rules (deck-truck-wheel pairings, durometer-terrain mappings, riding-style archetypes) as versioned, expert-authored Postgres-backed rules.

ADK workflow agents (`SequentialAgent`, `ParallelAgent`) make this separation a *system property*, not a prompt aspiration: the LLM **cannot** skip the Compatibility Layer. This is what enables the "0 hallucinated SKUs" guarantee that distinguishes this product from typical LLM commerce wrappers, where plausible-but-ungrounded answers are the dominant failure mode.

Three additional architectural decisions reinforce the differentiator:

1. **Intent-first, structured-retrieval-second.** A small/fast LLM extracts intent into a typed JSON filter against PostgreSQL. Vector search is *deliberately not* in the critical path for attribute-driven queries; RAG is reserved for unstructured content (reviews, technique guides). This is materially faster and more accurate than embedding-only retrieval for the queries that dominate skate purchasing.
2. **Multi-agent specialization with deterministic orchestration.** Specialized agents (intent classifier, parallel per-scope retrievers, compatibility validator, explainer) each have isolated context windows and are independently evaluable in an LLM-judge harness — enabling localized regression diagnosis on quarterly model upgrades.
3. **Latency and cost engineered into the architecture.** Tiered models, prompt caching on a stable system+domain prefix, semantic caching on head queries, parallel tool execution, and token streaming. The latency budget is decomposed at sub-component granularity and committed to in the Success Criteria, not aspirational.

The user-visible "aha" moment: a shopper types *"durable street setup, intermediate, around $200"* and receives three coherent, compatibility-validated setups with skater-vernacular trade-off explanations and one-click confirm-to-cart. They never had to know inches, durometer, or truck axle math.

## Project Classification

| Field | Value |
|---|---|
| **Project Type** | `web_app` (user-facing) + `api_backend` (service layer) + `ai_application_layer` (agent orchestration) |
| **Domain** | Primary: e-commerce · Secondary: AI-assisted decision systems |
| **Complexity** | High |
| **Project Context** | Brownfield extension — new product on top of an existing skate e-commerce platform; the existing platform is **not modified**, but the assistant integrates across multiple read/write surfaces (catalog, cart, account) |
| **Complexity Drivers** | Multi-agent orchestration (ADK); hybrid deterministic (rules) + probabilistic (LLM) system; real-time SSE streaming; cost-bounded inference at scale; integration with existing commerce systems |

## Success Criteria

### User Success

The product succeeds for users when each of the following is true in production:

- **Vocabulary-free purchase.** A user with zero skate-domain vocabulary articulates intent in plain language ("durable street setup, intermediate, around $200") and reaches a recommendation they would actually buy. Measured by: completion of intent → recommendation → confirmed cart-add within ≤3 conversational turns at the 95th percentile.
- **Coherent setups, one click to cart.** When the assistant proposes a complete setup (deck + trucks + wheels), every recommended SKU is in stock, validly priced, and compatibility-validated; the user adds the entire setup with a single confirmation action.
- **Trade-off transparency.** Recommendations include skate-vernacular trade-off explanations (e.g., durability vs. weight, beginner vs. advanced, street vs. cruising) that the user can act on without further clarification.
- **Cross-device continuity (authenticated users).** A conversation started on desktop resumes on mobile without re-prompting for context already gathered.
- **Anonymous parity for discovery.** Anonymous users get the same recommendation quality as authenticated users for top-of-funnel discovery; auth-only features (history-based personalization, cross-device resume) are additive, not gating.

### Business Success

Business outcomes that indicate the product is working:

- **Anonymous-to-cart conversion lift** vs. baseline keyword search — the headline business signal this assistant exists to move. Provisional target: measurable lift validated via A/B; absolute target set in week 4 against the baseline established at launch.
- **CTR on assistant-recommended products** vs. baseline search: **+15% to +25% relative lift** (provisional; A/B-validated).
- **Complete-setup attach rate** (≥2 of 3 of deck/trucks/wheels in cart when the assistant proposed a setup): baseline established at launch; 4-week target set post-baseline.
- **Returns-rate reduction** on assistant-recommended setups vs. non-assistant carts: tracked as a secondary metric; not a launch KPI.

### Technical Success

Technical outcomes that are launch-blocking:

- **End-to-end latency.** P95 < 3s.
- **First user-visible token.** < 1s (achieved via early-acknowledgement stub from the fast-model layer while the upstream pipeline runs).
- **Per-session cost.** P95 ≤ $0.05 — **hard constraint**, not aspirational.
- **Grounding.** Zero hallucinated SKUs in production (recommended product not present in the catalog with the claimed attributes).
- **Reliability.** Zero runaway-loop incidents in production; per-session iteration / token / wall-clock caps enforced at the gateway layer.
- **Cache efficacy.** Combined cache hit rate (prompt cache + semantic cache) on head queries: instrumented from launch; ≥ 40% by week 4 (realistic without historical data).
- **Mutation safety.** Zero cart-mutation events outside the documented allow-list (cart-add only, on user confirmation).
- **Observability.** Per-trace cost / latency / agent-decision telemetry operational from launch day one.

### Measurable Outcomes

The success criteria above are made falsifiable by the following operational artifacts:

- **Eval harness as a launch blocker.** A curated Ground Truth Set of **≥200 stratified queries** spanning intents (recommendation, clarification, refinement, FAQ, off-topic), skill levels (beginner / intermediate / advanced), and categories (deck-only, wheels-only, trucks-only, complete setups, accessories). Each entry has documented author and review date; skate domain expert sign-off required.
- **LLM-judge methodology.** Production-grade reasoning model with a structured rubric (relevance, accuracy, completeness, safety). Inter-rater agreement spot-checked against human reviewers on a 10% sample.
- **Statistical threshold.** Lower bound of 95% CI ≥ 85% recommendation relevance.
- **CI gating.** Every prompt change, model upgrade, or agent topology change runs the eval; failures block merge.
- **Per-trace telemetry.** Every production turn records: agent path taken, per-stage latency, total token cost, tool-call counts, hashed user identifier, cache hit / miss, compatibility verdict counts. Launch dashboards expose all success-criteria metrics live.
- **Falsifiability of the multi-agent bet.** Pre-launch, if per-agent isolation contributes < 2% absolute relevance gain over a single-agent + tools baseline **and** orchestration latency exceeds 200ms at P95, the topology decision is reopened in an Architecture Decision Record.

## Product Scope

### MVP — Minimum Viable Product

Required for launch:

- Conversational discovery and recommendation in natural language
- Multi-turn clarification (skill, terrain, budget, riding style) when intent is underspecified
- Single-product recommendations and complete deck+trucks+wheels setup recommendations
- User-confirmed add-to-cart (single items and full setups) via the existing cart API; **no autonomous mutations**
- Anonymous and authenticated usage
- Cross-device session continuity for authenticated users (Firestore listeners)
- Deterministic Compatibility Layer (versioned, expert-authored)
- Eval harness with stratified Ground Truth Set, LLM-judge, CI gating
- Per-trace observability dashboards live at launch
- Data & Privacy baseline: 30-day conversation retention, PII-stripped analytics, authenticated opt-out, region-pinned LLM provider
- LLM-provider degradation path: circuit-breaker → fallback to existing keyword search
- English only

**Out of MVP** (explicit, to prevent scope creep):

- Voice input/output
- Image-based search
- Order tracking, returns, refunds
- Payments and checkout (handed off to existing system unchanged)
- Social, gamification, community features
- Multi-language support
- Any mutation outside the cart-add allow-list

### Growth Features (Post-MVP)

Items the v1 architecture is *deliberately designed to support* without rework:

- **Catalog-quality feedback loop.** IntentAgent extractions that fail attribute matching are already logged; surface them as a backfill queue for merchandising (assistant becomes a catalog QA tool at zero marginal cost).
- **Compatibility Layer reuse beyond chat.** Power product-detail-page "works with" badges, PLP filter validation, and existing-cart setup-completion nudges with the same deterministic ruleset (zero LLM cost on these surfaces).
- **Personalization beyond session scope.** Long-term riding profile inferred from authenticated user history; saved preferences feeding intent extraction.
- **Outbound notifications via Firebase.** "We found 3 boards matching your saved query" — re-engagement using realtime infrastructure already paid for in v1.

### Vision (Future)

Longer-horizon expansions, not informing v1 architectural decisions beyond what's already noted:

- Image-based search ("looks like this") for users who cannot articulate what they want.
- Voice input on mobile.
- Multi-language support starting with Spanish and Portuguese.
- Post-purchase advisor (setup tuning, replacement recommendations, technique guides keyed to owned products).
- Reusable agent-and-eval substrate for future product surfaces (search-bar natural-language entry, on-product Q&A).

## User Journeys

### Journey 1 — Maya: anonymous beginner, vocabulary-free purchase (happy path)

**Persona.** Maya, 19, just moved to a city with a real skate scene. Skated occasionally on a friend's board in high school, never bought her own gear, has zero vocabulary. Lands on the site after a friend's recommendation, with $250 in her budget and a vague mental picture of "a chill board for cruising and learning some tricks at the park."

**Opening scene.** She lands on the homepage and sees the conventional category nav — *Decks · Trucks · Wheels · Bearings · Hardware · Grip · Apparel*. She doesn't know what trucks are. She clicks Decks and is hit with a faceted filter showing **width 7.5"–8.75"**, **wheelbase 13.75"–14.5"**, **concave low/medium/high**. None of these mean anything to her. On the previous platform UX she would close the tab. Instead, she sees a chat affordance: *"Tell me what you're looking for."*

**Rising action.** She types: *"Looking for a board for cruising around the city and learning some tricks at the skatepark, beginner, around $250."* The assistant comes back in under a second with an acknowledgement (*"Got it — let me put together some setups for that."*) and within three seconds streams a recommendation: *three coherent setups* — each with a deck, trucks, and wheels selected. The middle option is described as: *"Best balance for what you described. Element 8.0" deck (forgiving for tricks but stable for cruising), Independent 139mm trucks (correct width for that deck), Spitfire 99a 54mm wheels (a touch grippier than pure street wheels — better on rough pavement). Setup total $228 in stock."* Each option includes a short trade-off paragraph in skater terms.

**Climax.** Maya taps "Add this setup" on the middle option. A confirmation panel shows the three SKUs with stock and price. She confirms. Three items land in her cart in one action. She proceeds to the existing checkout flow — unchanged from the platform's current behavior.

**Resolution.** Maya never had to know that 8.0" decks pair with 139mm trucks, or that 99a is a durometer rating, or that 54mm wheels are a compromise between street and cruiser sizes. She got an expert's advice, validated for compatibility, in plain language, in under five seconds end-to-end. **Capabilities revealed:** intent extraction, multi-turn affordance, parallel retrieval, compatibility validation, streaming explanation with trade-off rationale, single-action setup-add, anonymous usage path.

### Journey 2 — Diego: ambiguous query, missing data, graceful degradation (edge case)

**Persona.** Diego, 28, longtime skater, knows exactly what he wants but states it in a way the system has to work harder to interpret. He's looking for a niche component the catalog only partially covers.

**Opening scene.** Diego types: *"I need replacement bushings for my Indy 149s, medium-soft, something that won't dive too hard on long fast descents."*

**Rising action.** The IntentAgent extracts: `{category: bushings, truck_brand: Independent, truck_size: 149, durometer: medium-soft, riding_style: downhill}`. Parallel retrieval runs against the bushings scope. Two issues surface: (a) most bushing SKUs in the catalog have durometer in the data but are missing the `riding_style: downhill` tag (sparse coverage on this attribute), and (b) the existing platform doesn't carry one of the brands Diego would expect. The Compatibility Layer flags candidates with NULL on the riding-style attribute and rejects them from setup recommendations — but they remain eligible as single-item recommendations. The IntentAgent logs the missing-attribute hits to the catalog-quality backfill queue.

**Climax.** The assistant responds: *"I found three options that match the size and durometer band you described. None of them have an explicit 'downhill' tag in our catalog yet, so I can't be 100% sure they handle high-speed dive the way you want — but based on durometer (88a–90a) and the fact that they're poured for Indy 149s, these are the right shape. Bones Hardcore Medium 88a, Riptide APS 90a, and Indy stock 90a. Want me to compare them side-by-side?"*

**Resolution.** Diego appreciates that the assistant didn't fabricate a tag it didn't have, and didn't paper over a real catalog gap. He picks the Riptide based on the side-by-side, adds it to cart, and goes. **Capabilities revealed:** intent extraction with niche attributes, missing-data graceful degradation, no-hallucination behavior on absent tags, transparent disclosure of confidence boundaries, catalog-quality logging for downstream backfill, refinement turn ("compare them side-by-side").

### Journey 3 — Sam: authenticated, cross-device session continuity

**Persona.** Sam, 24, a returning customer with two prior orders in their history and a cart already in progress on their laptop. They started a conversation with the assistant during a lunch break at work, got distracted, and now they're on their phone on the bus heading home.

**Opening scene.** Sam opens the platform on their phone. They're already logged in (Firebase ID token persists). The chat affordance shows *"Continue your conversation"* — the assistant remembers where they left off. Their previous turn was: *"I wanted some grip tape for the deck I ordered last week — something with good traction but not too coarse, my last roll tore up my shoes."*

**Rising action.** The assistant has access to Sam's authenticated context: the last order included a specific deck SKU; the current cart contains hardware bolts. With history-based personalization, it skips re-asking deck width and proposes three grip-tape options sized to the previously-ordered deck, ranked by traction-vs-coarseness. The reasoning cites Sam's prior order explicitly: *"For your Welcome Wax 8.5" — here are three sheets in stock, ranked from grippiest to gentlest..."*

**Climax.** Sam picks one, confirms add-to-cart, and the cart now contains the bolts (from the laptop session) plus the grip tape (from the phone session) — same cart, two devices, no friction. The Firestore listener pushed the cart update immediately.

**Resolution.** The cross-device continuity feels invisible. Sam doesn't think *"the assistant is fancy"* — they just experience it as the platform working the way they expect software to work in 2026. **Capabilities revealed:** Firebase Auth + Firestore session-state propagation, cross-device cart consistency, history-based personalization (last-ordered deck attributes), refresh hydration of mid-conversation state.

### Journey 4 — Priya: ML/AI Ops engineer responding to eval drift after a model upgrade

**Persona.** Priya is the on-call AI/ML Ops engineer for the assistant. Her primary surface is the observability dashboard (Langfuse-class) and the eval harness CI report.

**Opening scene.** A scheduled CI eval run fires on a Sonnet point-release upgrade PR. The harness reports: relevance dropped from 87.3% (lower CI bound) to 81.6% on the **complete-setup recommendation** intent slice — below the 85% gate. The PR is auto-blocked.

**Rising action.** Priya opens the dashboard. The per-agent telemetry shows the regression is localized: IntentAgent and CompatibilityAgent metrics are unchanged, but ExplanationAgent is producing recommendations that more often violate the trade-off-explanation rubric (mentioning trade-offs that don't apply to the specific products it recommended). Because each agent is independently evaluated, she can pinpoint the regression without reading every trace.

**Climax.** Priya bisects the system prompt change history; the regression correlates with a recent prompt revision in the ExplanationAgent prefix. She reverts that one prompt change, reruns the eval, and the gate clears. The Sonnet upgrade now passes.

**Resolution.** A model upgrade that would have caused a global quality regression in a monolithic ReAct system is contained and resolved at the per-agent level in a single afternoon. **Capabilities revealed:** per-agent eval slicing, per-trace observability, prompt-change audit log, CI gating with merge-blocking, structured rubric for LLM-judge.

### Journey 5 — Tariq: Compatibility-Layer rule author publishing a new rule

**Persona.** Tariq is a skate domain expert (former pro shop manager) contracted to author and review compatibility rules. He's not a developer; he writes rules in a structured format the system understands.

**Opening scene.** A new wheel brand has launched a 60mm cruiser wheel that's larger than typical and requires a riser pad to clear deck wheel-bite at standard truck heights. Without a rule, the assistant could recommend these wheels with a low-rise truck, producing a setup that physically rubs.

**Rising action.** Tariq drafts a new rule: *"Wheels ≥58mm with truck risers <1/8" require risers; flag setup as needs-riser-pad."* He submits a PR against the rules repository. Code review (by another engineer) confirms the schema, version, and owner fields. The rule ships with the next deploy.

**Climax.** Within hours, the new rule is enforced live. Setups proposed for users that pair these large wheels with low-rise trucks now either get a riser-pad add-on automatically suggested, or the wheel is excluded if no riser is in stock. The Compatibility Layer's rule-application metrics dashboard shows the new rule firing on ~40 proposed setups in the first day.

**Resolution.** A real-world physical hazard (wheel bite) is encoded once, deployed once, and prevented globally — without retraining a model, without rewriting prompts, and without runtime LLM cost. **Capabilities revealed:** versioned rule authoring workflow, expert review gate, deterministic enforcement at request time, per-rule observability metrics, zero-LLM-cost evolution of the trust layer.

### Journey Requirements Summary

The five journeys above reveal the following capability clusters that the PRD must specify (these will be developed as Functional Requirements in subsequent steps):

- **Conversational discovery & recommendation.** Intent extraction, multi-turn clarification, slot-filling, refinement, side-by-side compare. (Journeys 1, 2, 3)
- **Compatibility-validated setups.** Deterministic rule enforcement on every setup; transparent handling of missing data; no-hallucination guarantee. (Journeys 1, 2, 5)
- **Confirmation-gated cart writes.** Single-action setup-add via existing cart API; user always confirms. (Journeys 1, 3)
- **Anonymous + authenticated dual-mode.** Identical recommendation quality; auth adds personalization and continuity, doesn't gate access. (Journeys 1, 3)
- **Cross-device session continuity (auth users).** Firestore-backed session state, immediate device-to-device propagation. (Journey 3)
- **Streaming UX with early-acknowledgement TTFT.** First user-visible token < 1s, full response < 3s P95. (Journeys 1, 2)
- **Observability and eval-driven model lifecycle.** Per-agent telemetry, structured rubric, CI-gated upgrades, prompt-change audit. (Journey 4)
- **Compatibility-Layer authoring & operations.** Rule schema, version control, expert sign-off, per-rule firing metrics. (Journey 5)
- **Catalog-quality feedback loop.** Missing-attribute logging surfaces a backfill queue. (Journey 2)
- **Graceful degradation.** Honest disclosure of confidence boundaries; LLM-provider circuit-breaker fallback to keyword search; rate-limited anonymous abuse protection. (Journey 2 + cross-cutting)

## Domain-Specific Requirements

This product spans two complexity domains: **e-commerce** (consumer-facing transactional system on top of an existing platform) and **AI-assisted decision systems** (an LLM directly influences user-facing recommendations and cart construction). The canonical BMad domain catalog has no entry for either; the requirements below are authored for this combined surface.

### Compliance & Regulatory

- **Privacy regulations.** Compliance with applicable consumer-privacy regimes for the operating region (CCPA / CPRA in the US, GDPR if served to EU users). Conversation logs, recommendation events, and tool-call traces are personal data; the Data & Privacy Baseline (30-day retention, PII-stripped analytics, opt-out) is the operative standard.
- **PCI scope avoidance.** The assistant **must not** touch payment instruments, card data, or payment tokens at any point. Checkout and payments remain entirely within the existing platform. PCI scope is structurally avoided by the mutation allow-list (cart-add only).
- **Accessibility.** Conversational UI must meet **WCAG 2.2 AA** for keyboard navigation, screen-reader semantics, color contrast, and focus management. Streaming-text affordances must remain accessible. EU EAA-aligned where applicable.
- **AI transparency disclosure.** First interaction must clearly disclose that the user is interacting with an AI assistant, not a human. Recommendations must be visually distinguishable as system suggestions, not authoritative manufacturer claims. Aligns with EU AI Act transparency provisions for limited-risk systems and FTC guidance on AI representations.
- **Children's data.** The assistant inherits the existing platform's policy on minors; if the platform restricts or warns under 13 (COPPA-aligned), the assistant must do the same. The assistant is not designed for or marketed to children.

### Technical Constraints

- **Authentication & authorization.**
  - All authenticated traffic carries a Firebase ID token, verified by `firebase-admin` at the Python service edge.
  - Anonymous traffic is permitted but scoped, rate-limited, and cost-capped (token-bucket per anonymous session ID + per-IP rate limit + per-session cost cap + CAPTCHA escalation on anomalous patterns).
  - LLM-provider API keys are scoped, rotated, and stored in a secret manager — never embedded, never shared with checkout-system credentials.
- **Tool-permission sandbox.** The assistant's tool surface is whitelisted at the gateway. The only mutation tool is `cart-add` (single item or 2–3-item setup), invoked only on user confirmation. All other mutations — order, inventory, account, payment, address — are structurally inaccessible to the LLM.
- **Prompt-injection defense.** All retrieved content (product reviews, seller descriptions, technique guides) is treated as untrusted input. Pre-launch pen-test of the tool surface is a launch gate. Input/output guardrails (denylist patterns, structured-output schemas, response-validity checks) are enforced.
- **Audit logs.** Every cart-mutation event is logged with: hashed user identifier, session ID, timestamp, SKU set, recommendation source, idempotency key. Retained for the longer of legal-minimum and 90 days for fraud-investigation purposes.
- **Performance, scalability, reliability, accessibility.** Quantitative constraints (latency, concurrency, cost, uptime, WCAG conformance) are catalogued as NFR1–NFR30 below. The domain-specific intent is that the assistant is **not** on the critical path for browse, search, or checkout (architectural non-coupling — see NFR21).

### Integration Requirements

The assistant integrates with the existing platform across four read/write surfaces. Each must be specified contractually in the Architecture document.

| Surface | Direction | Contract |
|---|---|---|
| **Catalog (PostgreSQL)** | Read | Direct DB read with a dedicated read-only role; SQL-level access for parallel attribute filters. (Open Question: confirm direct access vs. internal API.) |
| **Cart API** | Write | Idempotent single-item add; batch / transactional setup add (all-or-nothing for 2–3 SKUs). Adapter layer if existing API does not natively support. |
| **User Accounts** | Read | Read-only access for authenticated personalization (recent orders, current cart contents). Mediated by Firebase ID token. |
| **Firebase Auth** | Verify | ID-token verification via `firebase-admin`. Identity system-of-record question is open (see Open Questions). |

External integrations:

- **Firestore** — message and session persistence; realtime listeners for cross-device continuity. Not used as a token-streaming bus.
- **LLM provider(s)** — primary + designated fallback for the circuit-breaker. Region-pinned to match data residency.
- **Observability platform** — per-trace cost / latency / agent-decision tracing. Vendor unselected (Open Question).
- **pgvector** — embedding-based retrieval for unstructured content only (reviews, technique guides). Not on the attribute-query critical path.

### Risk Mitigations

Domain-specific risks beyond the general engineering risks already enumerated:

- **Hallucinated SKUs or specs in user-facing recommendations.** *Mitigation:* the LLM never emits raw SKU or attribute values; every product cited is grounded in a tool result. Compatibility Layer post-validation rejects ungrounded candidates. Final pre-response check ensures every cited SKU exists with the claimed attributes.
- **Indirect prompt injection via product reviews and seller descriptions.** *Mitigation:* treat all retrieved unstructured content as untrusted; sandboxed tool permissions; structured-output schema enforcement on LLM responses; pre-launch red-team / pen-test.
- **Recommendation bias and fairness.** Two specific concerns for AI commerce: (a) **margin/inventory bias** — system silently preferring high-margin or overstocked SKUs against user interest; (b) **demographic-correlated assumptions** — e.g., inferring deck size or style from inferred gender. *Mitigation:* the LLM-judge eval rubric includes fairness slices (rotated personas, controlled-attribute pairs); recommendation distributions are audited periodically against catalog distributions; no demographic features are passed to the recommender.
- **Disclosure failures.** Risk that users believe they are talking to a human or that recommendations are authoritative manufacturer claims. *Mitigation:* persistent AI-assistant disclosure in the UI; recommendations visually framed as system suggestions; copy reviewed by counsel before launch.
- **Runaway agent loops as cost incidents.** *Mitigation:* hard per-session caps on iterations, tokens, wall-clock; loop detection (same tool, same args ≥3 → halt); gateway-level token-budget enforcement.
- **LLM provider outage or sustained tail-latency excursion.** *Mitigation:* circuit-breaker on provider error rate / TTFT P99 → frontend renders existing keyword-search UI with the user's prompt as keyword input. Documented degradation path; assistant outage is not a site outage.
- **ADK production-readiness caveats** (in-memory session defaults, per-user agent isolation patterns reported through 2025–early 2026). *Mitigation:* pin ADK version; wire a persistent session service from day one; validate per-user isolation under load; LangGraph fallback path retained.
- **Anonymous-access cost abuse.** *Mitigation:* layered controls — token-bucket per anonymous session ID, per-IP rate limit, hard per-anonymous-session cost cap, CAPTCHA escalation on suspicious traffic, edge bot detection.
- **Streaming-vs-persistence consistency window.** *Mitigation:* durable write to Firestore with retry before client acknowledges turn complete; out-of-band reconciliation for orphaned streams.
- **Catalog data quality (sparse or missing attributes).** *Mitigation:* graceful degradation in the assistant's responses (transparently disclose confidence boundaries); IntentAgent extractions that fail attribute matching feed a backfill queue for merchandising.
- **Eval drift on quarterly model upgrades.** *Mitigation:* LLM-judge harness with stratified Ground Truth Set is a launch blocker; CI gates on prompt and model changes; per-agent telemetry localizes regressions.

## Project-Type Specific Requirements

### Project-Type Overview

This product spans three project types simultaneously: a `web_app` (Next.js chat UI embedded in the existing platform), an `api_backend` (Python service hosting the agent orchestration), and an `ai_application_layer` (multi-agent ADK reasoning, eval harness, and LLM lifecycle). Each axis has distinct technical requirements; this section captures them. Cross-cutting concerns (authentication, data residency, observability, integration surfaces) are documented elsewhere and referenced rather than duplicated here.

### Technical Architecture Considerations

#### Web Application (Next.js Frontend)

- **App shape.** SPA-style chat surface as the primary new UX. Existing platform pages (catalog, PLP, PDP, cart, checkout) remain server-rendered as today and are not modified by this product. The assistant ships as an embedded widget plus a dedicated chat route.
- **Browser support.** Evergreen browsers (Chrome, Firefox, Safari, Edge — latest 2 major versions). Mobile Safari and Chrome Android required (cross-device journey demands phone parity).
- **SEO.** Not required for the chat surface (private, authenticated or session-scoped). The widget integration must **not regress** SEO on the existing SSR pages; client-side hydration of the chat affordance must be deferred until after main content paint.
- **Real-time.** SSE for streaming explanations from the backend; Firestore `onSnapshot` listeners for cross-device session-state propagation and message-history hydration.
- **Accessibility.** WCAG 2.2 AA (committed in Domain Requirements). Streaming text updates must be announced to assistive technologies; keyboard-navigable confirmation flow for cart-add; visible focus states; no-motion preference respected for typing animations.
- **Responsive design.** Mobile-first. Chat input, recommendation cards, and confirmation panels must function in narrow viewports (≥320px). Touch targets ≥44px.
- **Performance targets.** TTFB on the existing platform pages must not regress. The chat widget's initial bundle must be code-split and lazy-loaded — must not ship on pages where the user hasn't engaged the assistant.

#### API Backend (Python Service)

- **Endpoint surface (high-level; full OpenAPI in Architecture):**
  - `POST /v1/chat/turn` — primary turn endpoint. Accepts user message, session ID, optional Firebase ID token. Returns SSE stream with event types: `token` (partial text), `tool_call` (debug, optional), `recommendation` (structured payload), `clarification` (system question back to user), `done`, `error`.
  - `POST /v1/chat/cart-add` — user-confirmed cart-add. Accepts session ID, recommendation ID, idempotency key. Returns cart state from the existing cart API.
  - `GET /v1/chat/session/:id` — hydrate session for cross-device resume (auth-gated).
  - `POST /v1/chat/session/clear` — opt-out / delete session history (Data & Privacy Baseline).
  - `GET /health`, `GET /readiness` — operational endpoints (used by the load balancer and the circuit breaker).
- **Authentication model.**
  - **Authenticated:** Firebase ID token in `Authorization: Bearer` header; verified by `firebase-admin` at the service edge. Per-user rate limits and cost budgets apply.
  - **Anonymous:** opaque session ID server-issued on first turn; cookie or local-storage backed on the client. Rate-limited (token-bucket per session ID + per-IP), cost-capped per session, CAPTCHA escalation on suspicious patterns.
- **Data formats.** JSON for request bodies; SSE (`text/event-stream`) for chat responses with named event types and JSON payloads.
- **Rate limits & quotas.** Per-anonymous-session token-bucket; per-IP rate limit; per-authenticated-user daily token cap; per-session iteration cap (hard max ~10 agent steps per turn); per-session wall-clock cap. All enforced at the gateway, not inside the agents.
- **Versioning.** API path-versioned (`/v1/...`); SSE event-schema versioned independently in the event payload. Breaking changes ship under `/v2/` with overlap.
- **SDK.** None for v1. Single internal consumer (Next.js frontend); contract enforced via shared schema (Pydantic on backend, TypeScript types generated from JSON Schema export on frontend).
- **Error codes & semantics.** Structured error envelope on every error response. Distinguishable error classes: `400` validation, `401/403` auth, `429` rate/quota, `502` upstream LLM provider, `503` degraded mode (assistant unavailable, fallback active), `504` timeout. Circuit-breaker decisions surface as `503` with a documented machine-readable reason code.

#### AI Application Layer (ADK Multi-Agent Orchestration)

- **Agent topology (committed):** `IntentAgent → ParallelAgent(DeckRetrievalAgent, TruckRetrievalAgent, WheelRetrievalAgent) → CompatibilityAgent → ExplanationAgent → CartAgent` (CartAgent invoked only on user confirmation). Documented in the product brief.
- **Model tiering.** Fast/small model for IntentAgent and the early-acknowledgement TTFT stub. Reasoning model for ExplanationAgent. Both pinned per deploy via configuration; model upgrades gated by the eval harness.
- **Prompt-cache strategy.** Stable system+domain prefix (skate-domain knowledge, tool schemas, few-shot examples) shared across agents. 5-minute TTL on the prefix; session pacing must keep it warm. Cache hit metrics instrumented per agent.
- **Semantic-cache strategy.** Head-query cache fronts IntentAgent extractions. Cache key derived from normalized intent JSON. Quality gate (similarity threshold + periodic revalidation) prevents stale serving when catalog changes.
- **Tool-call concurrency.** Parallel SQL/tool execution within `ParallelAgent`. Tool schema enforced against the mutation allow-list (cart-add only mutates).
- **Loop & cost controls.** Hard caps per turn: iterations, tokens-per-request, total tokens, wall-clock. Loop detection halts on same-tool / same-args ≥3 occurrences within a turn. Token-budget enforcement at the gateway layer in addition to per-agent caps.
- **Eval harness (already specified in Success Criteria).** Per-agent evals plus system-level eval; stratified Ground Truth Set ≥200 queries; CI-gated on every prompt or model change.
- **Observability.** Per-trace fields: agent path taken, per-stage latency, total token cost, tool-call counts, hashed user ID, cache hit/miss, compatibility verdict counts. Dashboards live at launch. Vendor selection is an Open Question.
- **Session state persistence.** ADK persistent session service backed by Firestore (or a Postgres-backed alternative — Architecture decides). **Not** in-memory defaults; the production-readiness caveat in the brief is the reason this is called out at PRD level.
- **Falsifiability commitment.** The multi-agent topology is reverted to single-agent + tools if pre-launch evaluation shows per-agent isolation contributes < 2% absolute relevance gain over a single-agent + tools baseline **and** orchestration latency exceeds 200ms at P95.

### Implementation Considerations

- **Repository structure.** Backend (Python ADK service) and frontend (Next.js) are independent repos. Coupling is via the versioned API contract; shared types are generated from a single source-of-truth JSON Schema export.
- **ADK version pinning.** Pinned at deploy; version bumps gated by the eval harness and a load-test on staging at peak-concurrent levels. LangGraph fallback path is retained as a contingency.
- **CI / CD pipeline.**
  - Backend: pytest (unit + integration), eval harness (CI-gated), linter, type-checker, container build.
  - Frontend: typecheck, Playwright / Cypress E2E, accessibility checks (axe-core or equivalent), bundle-size budget enforced.
  - Pre-deploy load test against staging at peak-concurrent levels (2k concurrent simulated).
- **Rollout strategy.** Feature-flagged percentage rollout — 1% → 10% → 50% → 100% over ≥2 weeks. Each ramp gated by: (a) eval harness still passing in production-traffic conditions, (b) latency / cost SLOs holding, (c) zero hallucinated-SKU incidents.
- **Operational handoff.** Runbooks for: LLM provider outage (circuit-breaker activation), Firebase Auth outage, Postgres pool saturation, runaway-cost incident response, eval-harness CI failure triage. Runbooks ship before launch, not after.
- **Compliance handoff.** Data & Privacy Baseline mapped to operational responsibilities (retention job ownership, deletion-request SLA, audit-log query path, accessibility-conformance attestation).

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach: Problem-solving MVP with a strict trust-and-safety floor.**

The product cannot ship without four load-bearing systems: the deterministic Compatibility Layer, the LLM-judge eval harness, per-trace observability, and the mutation allow-list. These are *not* polish items deferred to a post-launch hardening sprint — they are what makes the differentiator ("deterministic commerce with an LLM front door") true at launch rather than aspirational. Cutting any of them would invalidate the product's core claim to the user and introduce reputational risk that no amount of MVP velocity could justify.

Within that non-negotiable floor, the MVP deliberately narrows surface area to maximize signal: English only; no voice; no image search; no multi-language; no post-purchase features; no autonomous cart mutations. This narrowness is the *MVP discipline*, not a deficiency — every excluded surface is intentional, with a documented home in Phase 2 or Phase 3 where it doesn't compete with launch-quality work on the core conversational discovery flow.

**Resource sizing (illustrative).** The exercise frames an L3-implementable scope; sizing should be confirmed at planning time. A reasonable team shape:

- **Backend (Python / ADK / FastAPI):** 1–2 senior engineers
- **Frontend (Next.js / SSE / Firebase SDKs):** 1 senior engineer
- **AI / ML Ops (eval harness, observability, prompt engineering):** 1 engineer
- **Compatibility-Layer authoring:** part-time skate domain expert (contract)
- **Shared with platform team:** SRE / infrastructure, security review, accessibility review

### MVP Feature Set (Phase 1)

**Core user journeys supported** (all five from the User Journeys section are launch-required):

- **Journey 1 (Maya — anonymous happy path).** Vocabulary-free intent → coherent setup → confirm-to-cart in ≤3 turns. The headline use case.
- **Journey 2 (Diego — edge case, missing data).** Graceful degradation, transparent confidence boundaries, catalog-quality logging. Required at launch — without it, the assistant either hallucinates or stays silent on real catalog gaps.
- **Journey 3 (Sam — authenticated, cross-device).** Firestore-backed continuity; history-aware personalization for signed-in users.
- **Journey 4 (Priya — ML / AI Ops).** Eval harness + observability are *launch blockers*, not nice-to-haves. The product's commitments to relevance and grounding are unenforceable without them.
- **Journey 5 (Tariq — rule author).** The Compatibility Layer is non-functional without an authoring/review workflow; this journey is the operational backbone of the differentiator.

**Must-have capabilities for MVP** are enumerated in *Product Scope → MVP* (see above) and bound to the journeys above. Every capability in that list is required for launch; none is deferred.

### Post-MVP Features

Phase 2 (Growth) and Phase 3 (Expansion / Vision) items are enumerated in *Product Scope → Growth Features (Post-MVP)* and *Product Scope → Vision (Future)*. The strategic framing here is that v1's architectural substrate (deterministic Compatibility Layer, eval harness, observability, Firestore realtime infrastructure, intent-extraction logging) is **deliberately built to support Phase 2 items as small additive epics** rather than rework. Phase 3 items are intentionally *not* shaping v1 architecture beyond what is explicitly called out.

### Risk Mitigation Strategy

**Technical risks.**
- *Hallucinated SKUs / specs, prompt injection, runaway agent loops, streaming-vs-persistence consistency, ADK production caveats* — all enumerated in Domain Requirements with operational mitigations. The strategic decision is to treat these mitigations as launch blockers, not as fast-follow items. Pen-test, eval harness, and observability dashboards are part of MVP definition-of-done.
- *Capacity at peak.* 2k peak concurrent at sub-3s P95 is non-trivial. Pre-launch load test on staging at peak-concurrent levels is a launch gate; provider rate-limit headroom must be ≥2× peak.

**Market / product risks.**
- *Conversion lift unproven.* The headline business signal (anonymous-to-cart conversion lift, CTR lift) is validated via A/B against baseline keyword search. The eval harness gives us *quality* signal pre- and post-launch; A/B gives us *commercial* signal. We do not know *a priori* that the assistant will outperform the existing search on conversion; we know that it should outperform on relevance and on setup-attach. If A/B shows neutral or negative conversion despite quality wins, the product question is real and surfaceable in week 4.
- *Skater authenticity.* A knowledgeable user who catches a wrong recommendation publicly is a brand risk. *Mitigation:* domain-expert sign-off on the Ground Truth Set; pre-launch QA with actual skaters; in-production reporting affordance for users to flag bad recommendations.

**Resource risks.**
- *If engineering capacity is tighter than planned*, the falsifiability clause provides a pre-baked simplification path: revert to single-agent + tools if eval shows < 2% relevance gain from the multi-agent topology *and* orchestration latency exceeds 200ms at P95. This is an honest engineering off-ramp, not a face-saving compromise.
- *If catalog data quality is worse than assumed*, the graceful-degradation behavior (transparent disclosure on missing attributes; backfill queue feed) is already specified, and the assistant remains useful at reduced confidence — it does not break.

## Functional Requirements

### Conversational Discovery

- **FR1:** User can submit a natural-language request describing their shopping intent (e.g., "durable street setup, intermediate, around $200").
- **FR2:** User can engage the assistant in a multi-turn conversation, with each turn building on prior context within the session.
- **FR3:** System can ask the user clarifying questions when intent is underspecified (e.g., skill level, terrain, budget, riding style).
- **FR4:** User can refine a recommendation by providing additional constraints (e.g., "show me cheaper options", "compare these side by side").
- **FR5:** System can decline gracefully and disclose its confidence boundaries when the catalog cannot satisfy the user's intent.
- **FR6:** User can engage with the assistant without authentication (anonymous mode).
- **FR7:** User can request a side-by-side comparison of two or more recommended products.

### Recommendation Reasoning & Explanation

- **FR8:** System can extract structured intent (typed attributes) from natural-language user input.
- **FR9:** System can retrieve candidate products from the catalog using the extracted intent.
- **FR10:** System can recommend a single product that matches the user's intent.
- **FR11:** System can recommend a complete setup (deck + trucks + wheels) as a coherent, jointly-reasoned group.
- **FR12:** System can produce a natural-language explanation for each recommendation, including trade-offs expressed in skater vernacular (e.g., durability vs. weight, beginner vs. advanced, street vs. cruising).
- **FR13:** System can stream the recommendation explanation to the user as it is generated.
- **FR14:** System emits an early-acknowledgement signal so the user sees a first response token within the low-latency budget while the full recommendation is computed.
- **FR15:** System grounds every recommended product in the actual catalog; no hallucinated SKUs or attributes are emitted.

### Compatibility Validation

- **FR16:** System validates every proposed setup against a deterministic Compatibility Layer before presenting it to the user.
- **FR17:** System rejects candidate products from setup recommendations when required compatibility attributes are missing or invalid.
- **FR18:** System can repair a proposed setup by substituting compatible alternatives when the initial proposal is invalid.
- **FR19:** System discloses to the user when a recommendation has reduced confidence due to missing catalog data (e.g., absent attribute tags).
- **FR20:** System logs missing-attribute occurrences to a catalog-quality backfill queue.

### Cart Construction

- **FR21:** User can review a recommendation in detail (SKUs, stock, prices, total) before any cart action.
- **FR22:** User can confirm and add a single recommended product to the existing cart.
- **FR23:** User can confirm and add a complete recommended setup (multiple SKUs) to the existing cart in a single action.
- **FR24:** System guarantees all-or-nothing semantics on setup adds: either all items are added, or none are.
- **FR25:** System never autonomously mutates the cart; every cart write requires explicit user confirmation.
- **FR26:** System never accesses or mutates checkout, payments, orders, inventory, or account state.

### Identity & Session

- **FR27:** Anonymous users can interact with the assistant with feature parity on recommendation quality (auth-only features are additive, not gating).
- **FR28:** Authenticated users can interact with the assistant via verified Firebase Auth identity.
- **FR29:** Authenticated users' conversations are persisted across sessions.
- **FR30:** Authenticated users can resume an in-progress conversation on a different device (cross-device continuity).
- **FR31:** System can use an authenticated user's recent-order history and current cart contents as personalization signals.
- **FR32:** System enforces rate limits and cost caps on anonymous sessions to prevent abuse and cost incidents.

### AI Operations & Observability

- **FR33:** System captures per-trace telemetry for every conversational turn (agent path taken, per-stage latency, total token cost, tool-call counts, hashed user identifier, cache hit/miss, compatibility-verdict counts).
- **FR34:** AI Ops engineer can view aggregate metrics on a dashboard for relevance, latency, cost, grounding, and cache efficacy.
- **FR35:** System runs an LLM-judge evaluation against a curated Ground Truth Set on every prompt change, model change, or agent topology change.
- **FR36:** AI Ops engineer can localize a quality regression to a specific agent in the topology via per-agent evaluation slices.
- **FR37:** System blocks a model upgrade or prompt change in CI when eval relevance falls below the configured threshold.
- **FR38:** System enforces hard caps per turn (iterations, tokens, wall-clock) and halts on loop detection.

### Compatibility Rule Authoring

- **FR39:** Rule author can define a new compatibility rule in a structured, reviewable format (rule schema).
- **FR40:** Rule author can submit a new rule for code review through the standard repository workflow.
- **FR41:** Each compatibility rule has an explicit version, owner, and effective date in its metadata.
- **FR42:** Rule author can view per-rule firing metrics on a dashboard (how often a rule applied, accepted, repaired, or rejected candidates).

### Privacy & Data Control

- **FR43:** System informs users at first interaction that they are interacting with an AI assistant, not a human.
- **FR44:** Authenticated users can disable persistent conversation history (opt-out).
- **FR45:** Users can request deletion of their conversation history; system honors deletion within the documented retention SLA.
- **FR46:** System retains conversation logs for no longer than 30 days; aggregated analytics are PII-stripped before retention.
- **FR47:** System does not store raw free-text user queries alongside user identifiers.

### Operational Resilience

- **FR48:** System falls back to the existing keyword-search experience when the LLM provider is unavailable or sustained tail latency exceeds threshold (circuit-breaker behavior).
- **FR49:** System provides a degraded-mode response with a documented machine-readable reason code when the assistant cannot meet its service-level objectives.
- **FR50:** Existing platform flows (browse, cart, checkout) remain operational regardless of assistant availability; assistant outage does not constitute a site outage.

## Non-Functional Requirements

### Performance

- **NFR1:** End-to-end response latency P95 < 3 seconds (measured from request acceptance to last streamed token).
- **NFR2:** First user-visible token latency < 1 second P95 (delivered via early-acknowledgement stub from the fast-model layer).
- **NFR3:** Per-stage latency budgets hold at P95: edge auth ≤ 80 ms, semantic-cache lookup ≤ 50 ms, intent extraction ≤ 600 ms, parallel retrieval (slowest branch) ≤ 400 ms, compatibility validation ≤ 100 ms, explanation TTFT ≤ 800 ms.
- **NFR4:** Streaming explanation throughput sustained across full response length without observable inter-token gaps > 200 ms.
- **NFR5:** TTFB on the existing platform pages must not regress more than 50 ms attributable to assistant widget code; chat widget is code-split and lazy-loaded on pages where the user has not engaged it.

### Security

- **NFR6:** All authenticated traffic carries a verified Firebase ID token; verification occurs at the service edge before any agent execution.
- **NFR7:** All anonymous traffic is rate-limited (token-bucket per session ID + per-IP) and cost-capped per session, with CAPTCHA escalation on anomalous patterns.
- **NFR8:** LLM-provider API keys are stored in a managed secret store, scoped by environment, rotated on schedule; no credential overlap with checkout-system secrets.
- **NFR9:** Tool-permission allow-list enforced at the gateway: `cart-add` is the only mutation tool; all other mutation surfaces are structurally inaccessible to the LLM.
- **NFR10:** Pre-launch red-team / penetration test of the assistant's tool surface, including indirect prompt injection vectors via product reviews and seller descriptions, is a launch gate.
- **NFR11:** Audit log retains every cart-mutation event with hashed user ID, session ID, timestamp, SKU set, recommendation source, and idempotency key for ≥ 90 days.
- **NFR12:** Compliance with applicable consumer-privacy regimes (CCPA / CPRA in the US, GDPR if EU users); data residency configurable per deployment with LLM-provider region pinned to match.
- **NFR13:** PCI scope is structurally avoided — the assistant never touches payment instruments, card data, or payment tokens.

### Scalability

- **NFR14:** System supports 50,000 daily active users sustained.
- **NFR15:** System supports 2,000 peak concurrent users at the documented latency SLOs.
- **NFR16:** Pre-launch load test on staging at peak-concurrent levels is a launch gate; provider rate-limit headroom verified ≥ 2× peak requests-per-second.
- **NFR17:** Postgres connection pool sized for `concurrent users × parallel-retrieval fan-out × agents` with documented headroom (capacity numbers specified in the Architecture document).
- **NFR18:** Per-session cost P95 ≤ $0.05 — hard constraint enforced via gateway-level token-budget caps.
- **NFR19:** System scales horizontally: stateless request handlers behind load balancer, persistent state in PostgreSQL and Firestore. Stateful behavior at the request handler layer is forbidden.

### Reliability

- **NFR20:** Assistant uptime target: 99.5% over rolling 30-day windows.
- **NFR21:** Existing platform flows (browse, cart, checkout) target ≥ 99.95% over rolling 30-day windows; assistant outage does not affect this metric (architectural non-coupling).
- **NFR22:** LLM-provider circuit-breaker trips on sustained provider error rate or TTFT P99 exceeding configured thresholds (specific thresholds set in Architecture); on trip, the frontend renders the existing keyword-search UI seeded with the user's prompt as keyword input.
- **NFR23:** Zero runaway-loop incidents in production; per-session iteration, token, and wall-clock caps enforced at the gateway in addition to per-agent caps.
- **NFR24:** Streaming-vs-persistence durability: a completed assistant message is durably written to Firestore (with retry) before the client acknowledges turn-complete; an out-of-band reconciliation job detects and repairs orphans.
- **NFR25:** Operational runbooks for LLM-provider outage, Firebase Auth outage, Postgres pool saturation, runaway-cost incident, and eval-CI failure ship before launch.

### Accessibility

- **NFR26:** Chat UI conforms to WCAG 2.2 AA across keyboard navigation, screen-reader semantics, color contrast, and focus management.
- **NFR27:** Streaming text updates are announced to assistive technologies via appropriate ARIA live-region semantics.
- **NFR28:** All interactive controls (input, send, confirm, opt-out, dismiss) are keyboard-operable with visible focus indicators.
- **NFR29:** Users' `prefers-reduced-motion` setting is respected; typing animations and streaming visualizations degrade to instant text rendering.
- **NFR30:** Touch targets on mobile are ≥ 44 × 44 CSS pixels; viewport supported down to 320 px width.

### Integration

- **NFR31:** Catalog data is accessed read-only by the assistant via a dedicated PostgreSQL role with SQL-level access for parallel attribute filters (or, alternatively, via an internal catalog API — Open Question).
- **NFR32:** Cart-add operations flow through the existing cart API using per-request idempotency keys; setup adds use a batch endpoint (or a transactional server-side adapter) with all-or-nothing semantics.
- **NFR33:** User-account reads (recent orders, current cart contents) are read-only and mediated by a verified Firebase Auth ID token.
- **NFR34:** Firebase Auth ID-token verification chain validated end-to-end (Next.js → Python service → `firebase-admin`) on every authenticated request.
- **NFR35:** Firestore is used exclusively for session/message persistence and realtime listeners; it is not used as a token-streaming bus.
- **NFR36:** Per-trace observability vendor (Langfuse / Phoenix / LangSmith — Open Question) is instrumented from launch with cost, latency, and agent-decision tracing across every conversational turn.

### AI Quality

- **NFR37:** Recommendation relevance ≥ 85% (lower bound of 95% CI) on the curated Ground Truth Set, measured via LLM-judge with a structured rubric (relevance, accuracy, completeness, safety).
- **NFR38:** Zero hallucinated SKUs in production — every recommended product exists in the catalog with the attributes the system claims for it.
- **NFR39:** Combined cache hit rate (prompt cache + semantic cache) on head queries ≥ 40% by week 4 post-launch (instrumented from launch).
- **NFR40:** Eval-harness CI gate blocks any prompt change, model upgrade, or agent topology change that drops eval relevance below the configured threshold.
- **NFR41:** Per-agent evaluation slices are produced by every CI eval run, enabling regression localization to a single agent on quarterly model upgrades.
- **NFR42:** Inter-rater agreement between LLM-judge and human reviewers is spot-checked on a 10% sample of GTS entries; discrepancies above a documented threshold trigger judge-rubric review.
