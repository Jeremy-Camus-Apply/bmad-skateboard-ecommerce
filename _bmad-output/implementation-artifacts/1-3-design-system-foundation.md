# Story 1.3: Design System Foundation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a frontend developer,
I want the design token system, typography, base components, and accessibility tooling configured,
So that every subsequent UI story builds on consistent tokens with axe-core a11y CI from day one.

## Acceptance Criteria

1. **Given** the Next.js project exists  
   **When** Tailwind v4 is configured with semantic palette tokens (surface, surface-elevated, surface-overlay, text-primary/secondary/muted, border, accent=Signal Red `#F03A3A`, grounded, uncertain, error)  
   **Then** dark and light theme variants share component code via CSS variables  
   **And** `prefers-color-scheme` is honored on first visit with manual-override persistence

2. **Given** the design system is configured  
   **When** Geist Sans + Geist Mono are loaded via `next/font/google` and the type scale tokens (display-1/2, headline-1/2, body-large, body, caption, tag, mono-body, mono-caption) are defined  
   **Then** typography is referenceable in any component without raw font-size or font-family values

3. **Given** Storybook is configured with shadcn/ui starter components installed (Button, Input, Dialog, Sheet, Toast, Tabs, Tooltip, Popover, Accordion, Skeleton, ScrollArea, Avatar, Badge, Card, Switch, Select, Separator, DropdownMenu)  
   **When** stories exist for each component  
   **Then** axe-core runs against every story in CI and merge is blocked on a11y violations

4. **Given** any interactive element is added  
   **When** ESLint runs in CI  
   **Then** the custom touch-target lint rule fails the build for any `<button>`, `<a>`, or Radix-derived interactive control with computed dimensions < 44 × 44 px

5. **Given** all design tokens are committed  
   **When** the contrast-lint job runs  
   **Then** any text-on-surface combination below WCAG 2.2 AA threshold for its size class fails the build

## Tasks / Subtasks

- [ ] **Task 1: Update Tailwind config with semantic design tokens** (AC: 1)
  - [ ] Subtask 1.1: Replace the shadcn slate defaults in `tailwind.config.ts` with the semantic palette from UX spec: `surface` (black `#000000`), `surface-elevated` (`#0A0A0A`), `surface-overlay` (`#141414`), `text-primary` (white `#FFFFFF`), `text-secondary` (`#A3A3A3`), `text-muted` (`#737373`), `border` (`#262626`), `border-subtle` (`#1A1A1A`), `accent` (Signal Red `#F03A3A`), `grounded` (`#22C55E`), `uncertain` (`#F59E0B`), `error` (`#EF4444`).
  - [ ] Subtask 1.2: Update `src/app/globals.css` CSS variables for both `:root` (light theme) and `.dark` (dark default) to match the semantic palette. Ensure both themes maintain WCAG 2.2 AA contrast ratios from UX spec validation.
  - [ ] Subtask 1.3: Add spacing scale tokens (space-1 through space-16, 4px base) and radius scale tokens (none, sm, full only — no lg/md from shadcn defaults).
  - [ ] Subtask 1.4: Implement `prefers-color-scheme` handling: dark default on first visit; add theme toggle persistence via localStorage (can be minimal in this story — just the persistence hook; full theme-toggle UI ships in Story 1.4+).

- [ ] **Task 2: Load Geist fonts and define type scale** (AC: 2)
  - [ ] Subtask 2.1: Add Geist Sans (display + text) and Geist Mono via `next/font/google` in `src/app/layout.tsx`. Use variable font with weight range 400-700 for Geist Sans, 400-600 for Geist Mono.
  - [ ] Subtask 2.2: Define type scale tokens in Tailwind config: `display-1` (48px/1.1), `display-2` (40px/1.15), `headline-1` (32px/1.2), `headline-2` (24px/1.25), `body-large` (18px/1.5), `body` (16px/1.5), `caption` (14px/1.4), `tag` (12px/1.2 uppercase), `mono-body` (16px/1.5 mono), `mono-caption` (14px/1.4 mono).
  - [ ] Subtask 2.3: Create `@layer utilities` classes for each type scale token in `globals.css` so they're referenceable as Tailwind utilities (e.g., `text-display-1`, `text-body`, `text-mono-caption`).

- [ ] **Task 3: Install shadcn/ui starter component set** (AC: 3)
  - [ ] Subtask 3.1: Run `pnpm dlx shadcn@latest add input dialog sheet toast tabs tooltip popover accordion skeleton scroll-area avatar badge card switch select separator dropdown-menu` to populate `src/components/ui/` with the full starter set (Button already exists from Story 1.1).
  - [ ] Subtask 3.2: Verify each component uses semantic design tokens (not shadcn defaults). Update any hardcoded `bg-primary` / `text-foreground` to `bg-surface-elevated` / `text-text-primary` etc. per the semantic palette.
  - [ ] Subtask 3.3: Add `"use client";` directive to any shadcn component that uses React hooks or event handlers (per Story 1.1 review fix M12 on Button).

- [ ] **Task 4: Set up Storybook with axe-core integration** (AC: 3)
  - [ ] Subtask 4.1: Install Storybook for Next.js: `pnpm dlx storybook@latest init`. Use Storybook 8.x with the Next.js framework preset.
  - [ ] Subtask 4.2: Install `@storybook/addon-a11y` and configure it in `.storybook/main.ts` addons array.
  - [ ] Subtask 4.3: Create a story file for each shadcn component in `src/components/ui/*.stories.tsx` — one default story + variant stories (e.g., Button: default, destructive, outline, ghost, disabled).
  - [ ] Subtask 4.4: Add `.storybook/preview.tsx` to wrap all stories in the dark theme class (`<div className="dark">`) so stories render in the dark-default theme matching production.
  - [ ] Subtask 4.5: Add a `test-storybook` script to `package.json` that runs `test-storybook --url http://localhost:6006` (for CI; runs axe checks on all stories).

- [ ] **Task 5: Add Storybook CI job with axe-core gate** (AC: 3)
  - [ ] Subtask 5.1: Extend `.github/workflows/frontend-ci.yml` to add a `storybook-a11y` job that builds Storybook (`pnpm build-storybook`), serves it (`npx http-server storybook-static --port 6006 &`), and runs `pnpm test-storybook`.
  - [ ] Subtask 5.2: Make axe violations blocking: any CRITICAL or SERIOUS axe rule failure from `test-storybook` causes the job to fail with non-zero exit.

- [ ] **Task 6: Add custom touch-target ESLint rule** (AC: 4)
  - [ ] Subtask 6.1: Create a custom ESLint rule in `.eslint/rules/touch-target.js` (or use an existing plugin if available — check `eslint-plugin-jsx-a11y` for equivalent). The rule should flag any `<button>`, `<a>`, or Radix Primitive (e.g., `<DialogTrigger>`) that doesn't have explicit `className` including padding/min-width/min-height sufficient for 44x44px.
  - [ ] Subtask 6.2: If a full custom rule is too complex for Story 1.3, document the requirement in `.eslintrc.json` comments and add a manual checklist to PR templates. Full lint automation can be a Story 1.18 (pre-launch hardening) item.
  - [ ] Subtask 6.3: For now, add a comment in `.eslintrc.json` and `docs/design-system.md` stating: "All interactive elements MUST meet 44x44px touch target. Enforced manually in PR review until automated lint rule lands."

- [ ] **Task 7: Add contrast-lint job (post-MVP, nice-to-have for Story 1.3)** (AC: 5)
  - [ ] Subtask 7.1: Research if a CI-friendly tool exists for automated contrast checking (e.g., `pa11y-ci` with contrast plugins, or a custom script using `color-contrast-checker` npm package).
  - [ ] Subtask 7.2: If tooling is mature, add a `contrast-lint` step to `frontend-ci.yml` that scans committed color tokens in `globals.css` and fails if any text/surface pair is below 4.5:1 (body) or 3:1 (large text).
  - [ ] Subtask 7.3: If tooling is immature or time-consuming, defer to Story 1.18 and document in this story's Dev Notes that manual contrast verification against UX spec is required for now.

- [ ] **Task 8: Update existing Button component to use semantic tokens** (AC: 1, 2, 3)
  - [ ] Subtask 8.1: Open `src/components/ui/button.tsx` and replace any `bg-primary`, `text-foreground`, `border-border` with semantic equivalents: `bg-accent`, `text-text-primary`, `border-border`, etc.
  - [ ] Subtask 8.2: Ensure the `destructive` variant uses `bg-error`, the default variant uses `bg-accent`, and any muted/ghost variants use `bg-surface-elevated` or `text-text-muted`.
  - [ ] Subtask 8.3: Verify the Button story in Storybook renders correctly with the new tokens and passes axe-core checks.

- [ ] **Task 9: Add design system documentation** (nice-to-have)
  - [ ] Subtask 9.1: Create `docs/design-system.md` documenting: semantic palette tokens, type scale, spacing scale, radius scale, touch-target floor, axe-core CI gate, and how to reference tokens in components.
  - [ ] Subtask 9.2: Add "no raw color/spacing/font values in component code" rule to the doc with examples (good: `text-text-primary`, bad: `text-[#FFFFFF]`).

## Dev Notes

### Epic Context (from Epic 1)

- Story 1.3 is the **design system foundation** that unlocks all subsequent UI stories (1.4–1.12, 1.17).
- Every component built after this story MUST reference design tokens, never raw values.
- WCAG 2.2 AA conformance is **CI-enforced** from this story forward via axe-core; accessibility is not a post-launch audit.

### Previous Story Intelligence (Stories 1.1 & 1.2)

From **Story 1.1 (Project Foundation)**:
- Frontend scaffold already exists with Next.js 15.1.4, React 19, Tailwind 3.4.x, shadcn slate base
- Only `Button` component exists in `src/components/ui/` (intentionally kept minimal in 1.1)
- Current `tailwind.config.ts` has placeholder comment: "Real design tokens land in Story 1.3"
- Current `globals.css` has shadcn slate CSS variables with same comment
- Build/lint/typecheck pipeline is green; vitest + Playwright configured

From **Story 1.2 (Cloud SQL / Alembic / CI Gate)**:
- Backend-focused story; no frontend changes. 1.3 picks up where 1.1 left off for frontend.

**Key file locations from Story 1.1:**
- `skate-assistant-frontend/tailwind.config.ts` — semantic tokens land here
- `skate-assistant-frontend/src/app/globals.css` — CSS variables land here
- `skate-assistant-frontend/src/components/ui/button.tsx` — already exists, needs token update
- `skate-assistant-frontend/src/app/layout.tsx` — Geist fonts land here
- `skate-assistant-frontend/package.json` — Storybook deps land here
- `.github/workflows/frontend-ci.yml` — Storybook CI job extends this

### Architecture Compliance Requirements

From **Architecture § Starter Template Evaluation**:
- shadcn/ui components copied into the repo (not npm-installed) — "copy not install" philosophy
- Tailwind v4 token configuration with semantic palette committed in UX spec
- Geist Sans + Geist Mono via `next/font/google`
- Dark default + light theme via CSS variables sharing component code
- Radix UI primitives for accessibility-by-default

From **Architecture § Implementation Patterns & Consistency Rules**:
- **"No raw color, spacing, or font-size values in component code"** — enforce from Story 1.3 forward
- **All components reference design tokens from `tailwind.config.ts`**
- **`prefers-reduced-motion` honored at hook level** (implemented per-component in later stories, foundation set here)

From **UX Design Specification § Design System Foundation**:
- **Accent:** Signal Red `#F03A3A` (used sparingly: primary CTAs, current-tab indicators, user message bubbles)
- **Semantic tokens:** `grounded` for compatibility-validated (not generic success), `uncertain` for confidence boundaries (not warning/error)
- **Contrast ratios:** All pairs verified WCAG 2.2 AA in both themes (see table below)
- **Typography:** Geist Sans (display + text), Geist Mono (numeric attributes)
- **Touch targets:** ≥ 44 × 44 px (NFR30); lint-enforced
- **axe-core CI:** component-level accessibility checks on every Storybook story

### Design Token Palette (from UX Spec)

**Semantic tokens (dark theme — dark is default):**

| Token | Hex | HSL | Use |
|---|---|---|---|
| `surface` | `#000000` | `0 0% 0%` | Base background |
| `surface-elevated` | `#0A0A0A` | `0 0% 4%` | Cards, panels |
| `surface-overlay` | `#141414` | `0 0% 8%` | Modals, tooltips |
| `text-primary` | `#FFFFFF` | `0 0% 100%` | Headings, body |
| `text-secondary` | `#A3A3A3` | `0 0% 64%` | Secondary copy |
| `text-muted` | `#737373` | `0 0% 45%` | Placeholders, disabled |
| `border` | `#262626` | `0 0% 15%` | Default borders |
| `border-subtle` | `#1A1A1A` | `0 0% 10%` | Subtle dividers |
| `accent` | `#F03A3A` | `357 85% 59%` | Signal Red — CTAs, active states |
| `grounded` | `#22C55E` | `142 71% 45%` | Compatibility-validated states |
| `uncertain` | `#F59E0B` | `38 92% 50%` | Confidence-boundary disclosures |
| `error` | `#EF4444` | `0 84% 60%` | Genuine system errors |

**Light theme adjustments** (same semantic names, inverted lightness):
- `surface`: `#FFFFFF`, `surface-elevated`: `#F5F5F5`, `surface-overlay`: `#E5E5E5`
- `text-primary`: `#000000`, `text-secondary`: `#525252`, `text-muted`: `#A3A3A3`
- `border`: `#E5E5E5`, `border-subtle`: `#F5F5F5`
- Accent, grounded, uncertain, error: same hue, adjusted lightness for contrast

**Contrast ratios (dark theme, verified WCAG 2.2 AA):**

| Pair | Ratio | Verdict |
|---|---|---|
| `text-primary` on `surface` | ≈ 21:1 | AAA |
| `text-primary` on `surface-elevated` | ≈ 17:1 | AAA |
| `text-secondary` on `surface` | ≈ 8:1 | AAA large, AA normal |
| `text-muted` on `surface` | ≈ 5:1 | AA |
| `accent` (Signal Red) on `surface` | ≈ 5.5:1 | AA |
| `grounded` on `surface` | ≈ 5.8:1 | AA |
| `uncertain` on `surface` | ≈ 9:1 | AAA |

**Type scale tokens:**

| Token | Size / Line-height | Use | Tailwind class |
|---|---|---|---|
| `display-1` | 48px / 1.1 | Hero headings | `text-display-1` |
| `display-2` | 40px / 1.15 | Section headings | `text-display-2` |
| `headline-1` | 32px / 1.2 | Card titles | `text-headline-1` |
| `headline-2` | 24px / 1.25 | Product names | `text-headline-2` |
| `body-large` | 18px / 1.5 | Large body | `text-body-large` |
| `body` | 16px / 1.5 | Default body | `text-body` |
| `caption` | 14px / 1.4 | Microcopy | `text-caption` |
| `tag` | 12px / 1.2 (uppercase, 0.1em tracking) | Sticker tags | `text-tag` |
| `mono-body` | 16px / 1.5 (Geist Mono) | Numeric attributes | `text-mono-body` |
| `mono-caption` | 14px / 1.4 (Geist Mono) | Small numeric | `text-mono-caption` |

**Spacing scale (4px base):**

| Token | Value | Tailwind class |
|---|---|---|
| `space-1` | 4px | `space-1` or `p-1` / `m-1` / `gap-1` |
| `space-2` | 8px | `space-2` or `p-2` / `m-2` / `gap-2` |
| `space-3` | 12px | `space-3` |
| `space-4` | 16px | `space-4` or `p-4` / `m-4` / `gap-4` |
| `space-6` | 24px | `space-6` |
| `space-8` | 32px | `space-8` |
| `space-10` | 40px | `space-10` |
| `space-12` | 48px | `space-12` |
| `space-16` | 64px | `space-16` |

(Tailwind's default spacing scale already provides these; explicit tokens not needed in config unless customizing beyond defaults.)

**Radius scale:**

| Token | Value | Use |
|---|---|---|
| `none` | 0 | Sharp edges (Direction A "Calm Floor") |
| `sm` | 4px | Small chips/tags |
| `full` | 9999px | Pills, circular avatars |

(Remove shadcn's `lg`, `md` radius defaults — UX spec uses only none/sm/full.)

### Technical Guardrails

From **Architecture § Implementation Patterns & Consistency Rules — Enforcement Guidelines**:

> **All AI implementation agents MUST:**
> 2. **Reference design tokens from `tailwind.config.ts`** — never raw color, spacing, or font-size values in component code.
> 7. **Add a Storybook story for every new custom component** — required for axe-core CI; failures block merge.
> 9. **Honor `prefers-reduced-motion`** — every animation, transition, or streaming visualization checks the media query.

**Pattern to enforce from this story forward:**

✅ **Good:**
```tsx
<button className="bg-accent text-text-primary hover:bg-accent-hover">
  Add to cart
</button>
```

❌ **Anti-pattern:**
```tsx
<button className="bg-[#F03A3A] text-white hover:bg-[#FF5252]">
  Add to cart
</button>
```

### Testing Requirements

- **Storybook stories:** one per shadcn component with all variants (default, hover, disabled, etc.)
- **axe-core CI:** `test-storybook` runs against all stories; any CRITICAL or SERIOUS violation blocks merge
- **Visual regression (optional Phase 1):** Chromatic or Playwright screenshots can be added in Story 1.18 if time allows
- **Touch-target enforcement:** manual PR review for Story 1.3; automated lint rule in Story 1.18 if feasible

### File Structure Requirements

**Expected new/modified files:**

- `skate-assistant-frontend/tailwind.config.ts` — semantic tokens replace shadcn defaults
- `skate-assistant-frontend/src/app/globals.css` — CSS variables for dark/light themes + type scale utilities
- `skate-assistant-frontend/src/app/layout.tsx` — Geist fonts loaded via `next/font/google`
- `skate-assistant-frontend/src/components/ui/*.tsx` — full shadcn starter set (input, dialog, sheet, toast, tabs, tooltip, popover, accordion, skeleton, scroll-area, avatar, badge, card, switch, select, separator, dropdown-menu)
- `skate-assistant-frontend/src/components/ui/*.stories.tsx` — Storybook stories for each component
- `skate-assistant-frontend/.storybook/main.ts` — Storybook config with Next.js preset + a11y addon
- `skate-assistant-frontend/.storybook/preview.tsx` — dark theme wrapper
- `skate-assistant-frontend/package.json` — Storybook deps added
- `.github/workflows/frontend-ci.yml` — Storybook CI job added
- `docs/design-system.md` (new) — design system documentation

### Existing Behavior To Preserve

- Button component already exists and works from Story 1.1 — update it to use semantic tokens, don't break it
- Build/lint/typecheck/test pipeline from Story 1.1 must stay green
- No backend changes in this story (stays on Story 1.2 baseline)

### Latest Technical Information (Web Research Snapshot)

- **Storybook 8.x** (latest stable as of 2026) with Next.js framework preset is the current best practice
- **`@storybook/addon-a11y`** uses axe-core under the hood; no separate axe install needed
- **Geist Sans + Geist Mono** are available via `next/font/google` as of Next.js 13+ (confirmed working in 15.x)
- **Tailwind v4** (if using the v4 beta) or Tailwind 3.4.x (current stable) — check `package.json` from Story 1.1; likely 3.4.x. Token structure is the same.
- **shadcn/ui** components are stable as of 2026; `pnpm dlx shadcn@latest add` is the current installation method

### Project Structure Notes

Continue using the monorepo structure from Story 1.1:
- Frontend at `skate-assistant-frontend/`
- Backend at `skate-assistant-backend/` (unchanged in this story)
- Infra at `infra/` (unchanged)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` § Story 1.3 — Acceptance Criteria]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` § Design System Foundation — semantic palette, typography, accessibility]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Starter Template Evaluation — Tailwind + shadcn/ui + Radix]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Implementation Patterns & Consistency Rules — token-first enforcement]
- [Source: `_bmad-output/implementation-artifacts/1-1-project-foundation-and-gcp-infrastructure.md` — prior frontend patterns]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

(to be filled by dev agent)

### Completion Notes List

(to be filled by dev agent)

### File List

(to be filled by dev agent)

## Change Log

| Date       | Change                                                                 |
|------------|------------------------------------------------------------------------|
| 2026-05-07 | Story created via `bmad-create-story` — ready for `dev-story` execution |
