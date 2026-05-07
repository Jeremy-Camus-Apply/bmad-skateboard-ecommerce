# skate-assistant-frontend

Next.js 15 (App Router) + Tailwind + shadcn/ui foundation for the Skate Assistant.

## Local development

```bash
pnpm install
pnpm dev          # http://localhost:3000

pnpm lint
pnpm typecheck
pnpm test:unit
pnpm build
```

The full local stack (`docker compose up`) at the repo root will mount this app and proxy to the backend. Standalone `pnpm dev` is fine for UI-only iteration.

## Project layout

```
src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx       # Minimal landing — verifies shadcn Button pipeline
│   └── globals.css
├── components/ui/     # shadcn primitives (Button — more added in Story 1.3+)
└── lib/utils.ts       # cn() helper
tests/
└── landing-page.test.tsx   # vitest + RTL smoke
```

Design tokens / Geist fonts / Storybook / axe-core land in **Story 1.3**.
