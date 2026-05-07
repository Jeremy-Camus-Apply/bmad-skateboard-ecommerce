# Design System Foundation

**Version:** 1.0  
**Last Updated:** 2026-05-07  
**Story:** 1.3 - Design System Foundation

## Overview

This document describes the Skate Assistant design system, including semantic color tokens, typography scales, spacing conventions, accessibility requirements, and implementation guidelines for all UI components.

## Semantic Color Palette

### Design Philosophy

The design system uses **semantic color tokens** instead of raw color values. This approach:
- Enables consistent theming across dark and light modes
- Makes intent explicit (e.g., `accent` vs `error`)
- Simplifies component code
- Ensures WCAG 2.2 AA contrast compliance

### Color Tokens

| Token | Purpose | Dark Theme | Light Theme |
|-------|---------|------------|-------------|
| `surface` | Base background | `#000000` | `#FFFFFF` |
| `surface-elevated` | Cards, panels | `#0A0A0A` | `#F5F5F5` |
| `surface-overlay` | Modals, tooltips | `#141414` | `#E5E5E5` |
| `text-primary` | Headings, body | `#FFFFFF` | `#000000` |
| `text-secondary` | Secondary copy | `#A3A3A3` | `#525252` |
| `text-muted` | Placeholders, disabled | `#737373` | `#A3A3A3` |
| `border` | Default borders | `#262626` | `#E5E5E5` |
| `border-subtle` | Subtle dividers | `#1A1A1A` | `#F5F5F5` |
| `accent` | **Signal Red** - CTAs, active states | `#F03A3A` | `#F03A3A` |
| `grounded` | Compatibility-validated states | `#22C55E` | Adjusted for contrast |
| `uncertain` | Confidence boundaries | `#F59E0B` | Adjusted for contrast |
| `error` | System errors | `#EF4444` | Adjusted for contrast |

### Usage Rules

✅ **Correct:**
```tsx
<button className="bg-accent text-text-primary hover:bg-accent/90">
  Add to cart
</button>
```

❌ **Incorrect:**
```tsx
<button className="bg-[#F03A3A] text-white hover:bg-[#FF5252]">
  Add to cart
</button>
```

**Rule:** Never use raw color values in component code. Always reference semantic tokens from `tailwind.config.ts`.

## Typography

### Font Families

- **Geist Sans:** Display and body text (weights: 400, 500, 600, 700)
- **Geist Mono:** Numeric attributes, code (weights: 400, 500, 600)

Loaded via `next/font/google` with `display: swap` for optimal performance.

### Type Scale

| Token | Size / Line-height | Use Case | Tailwind Class |
|-------|-------------------|----------|----------------|
| `display-1` | 48px / 1.1 | Hero headings | `text-display-1` |
| `display-2` | 40px / 1.15 | Section headings | `text-display-2` |
| `headline-1` | 32px / 1.2 | Card titles | `text-headline-1` |
| `headline-2` | 24px / 1.25 | Product names | `text-headline-2` |
| `body-large` | 18px / 1.5 | Large body text | `text-body-large` |
| `body` | 16px / 1.5 | Default body | `text-body` |
| `caption` | 14px / 1.4 | Microcopy | `text-caption` |
| `tag` | 12px / 1.2 (uppercase, 0.1em tracking) | Sticker tags | `text-tag` |
| `mono-body` | 16px / 1.5 (Geist Mono) | Numeric attributes | `text-mono-body` |
| `mono-caption` | 14px / 1.4 (Geist Mono) | Small numeric | `text-mono-caption` |

**Rule:** Never use raw `font-size` or `font-family` values. Always use type scale utilities.

## Spacing & Layout

### Spacing Scale

Tailwind's default 4px-base spacing scale is used:
- `space-1` = 4px (`p-1`, `m-1`, `gap-1`)
- `space-2` = 8px (`p-2`, `m-2`, `gap-2`)
- `space-4` = 16px (`p-4`, `m-4`, `gap-4`)
- `space-6` = 24px
- `space-8` = 32px
- `space-12` = 48px
- `space-16` = 64px

**Rule:** Use Tailwind's spacing utilities. Avoid raw pixel values in margins, padding, or gaps.

### Border Radius

The design system defines three radius values (Direction A "Calm Floor"):
- `none` = 0 (sharp edges)
- `sm` = 4px (small chips, tags)
- `full` = 9999px (pills, circular avatars)

**Note:** shadcn's default `lg` and `md` radius values have been removed.

## Accessibility Requirements

### WCAG 2.2 AA Compliance

All UI components **must** meet WCAG 2.2 AA standards. This is enforced via:
- **axe-core CI gate:** All Storybook stories are tested with axe-core. Any CRITICAL or SERIOUS violation blocks merge.
- **Manual PR review:** Reviewers check for compliance during code review.

### Touch Targets (NFR30)

All interactive elements (buttons, links, Radix Primitives with click handlers) **must** meet a **44 × 44 pixel minimum touch target**.

**Enforcement:**
- Manual PR review (Story 1.3)
- Automated ESLint rule (Story 1.18)

**Common patterns:**
```tsx
// ✅ Adequate touch target
<button className="h-10 px-4 py-2">Click me</button> // h-10 = 40px, with py-2 = 44px+

// ❌ Insufficient touch target
<button className="h-6 px-2">Small</button> // Only 24px
```

### Focus Indicators

All interactive elements must have visible focus indicators for keyboard navigation:
```tsx
focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent
```

### Screen Reader Support

- Use semantic HTML (`<button>`, `<a>`, `<label>`)
- Add `aria-label` or `aria-labelledby` for icon-only buttons
- Use `<span className="sr-only">` for screen-reader-only text

## Component Library

### shadcn/ui Components

The design system uses **shadcn/ui components** (copied into the repo, not npm-installed). All components are accessible by default via Radix UI primitives.

**Installed components:**
- Button, Input, Dialog, Sheet, Toast
- Tabs, Tooltip, Popover, Accordion
- Skeleton, ScrollArea, Avatar, Badge, Card
- Switch, Select, Separator, DropdownMenu

### Storybook

Every component has Storybook stories for:
- Visual documentation
- Interactive testing
- Accessibility validation (axe-core runs on every story)

**Run Storybook locally:**
```bash
pnpm storybook
```

## Theme Support

### Dark Theme (Default)

The design system defaults to dark theme on first visit (matching `prefers-color-scheme: dark`). Users can manually override via theme toggle (to be implemented in Story 1.4+).

### Implementation

- CSS variables defined in `src/app/globals.css` (`:root` = light, `.dark` = dark)
- Theme persistence via `localStorage` using `useTheme` hook
- Components share code across themes via CSS variable references

## CI/CD Quality Gates

### Automated Checks

1. **ESLint:** Enforces code standards (including semantic token usage)
2. **TypeScript:** Strict type-checking
3. **Vitest:** Unit tests for business logic
4. **Playwright:** End-to-end tests for critical flows
5. **Storybook axe-core:** Accessibility checks on all component stories (blocking)

### Manual Checks

- Touch target compliance (PR review)
- Contrast ratio validation (design spec pre-verified, periodic manual audit)

## Migration Notes

### Updating Existing Components

When updating shadcn/ui components or creating new components:

1. **Use semantic tokens:**
   - `bg-surface` instead of `bg-background`
   - `text-text-primary` instead of `text-foreground`
   - `text-text-secondary` instead of `text-muted-foreground`

2. **Use type scale utilities:**
   - `text-body` instead of `text-sm`
   - `text-headline-2` instead of `text-xl`

3. **Use semantic radius:**
   - `rounded-sm` (4px) or `rounded-full`
   - Avoid `rounded-md` or `rounded-lg`

4. **Add Storybook story:**
   - Every new component requires a story
   - Story must pass axe-core checks

## Reference Files

- **Tailwind config:** `skate-assistant-frontend/tailwind.config.ts`
- **CSS variables:** `skate-assistant-frontend/src/app/globals.css`
- **Font loading:** `skate-assistant-frontend/src/app/layout.tsx`
- **Components:** `skate-assistant-frontend/src/components/ui/*.tsx`
- **Stories:** `skate-assistant-frontend/src/components/ui/*.stories.tsx`
- **Theme hook:** `skate-assistant-frontend/src/hooks/use-theme.ts`

## Future Enhancements

Deferred to Story 1.18 (Pre-launch Hardening):
- Automated touch-target ESLint rule
- Automated contrast-lint CI job
- Visual regression testing (Chromatic or Playwright screenshots)

---

**Questions?** Contact the design system team or refer to the UX Design Specification in `_bmad-output/planning-artifacts/ux-design-specification.md`.
