---
name: i18n
description: "Skill for the I18n area of Semantic-Reasoning-Agent. 3 symbols across 2 files."
---

# I18n

3 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `apps/`
- Understanding how AppLayout, normalizeLanguage, getBrowserLanguage work
- Modifying i18n-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/src/shared/i18n/locale.ts` | normalizeLanguage, getBrowserLanguage |
| `apps/frontend/src/app/layout.tsx` | AppLayout |

## Entry Points

Start here when exploring this area:

- **`AppLayout`** (Function) — `apps/frontend/src/app/layout.tsx:25`
- **`normalizeLanguage`** (Function) — `apps/frontend/src/shared/i18n/locale.ts:5`
- **`getBrowserLanguage`** (Function) — `apps/frontend/src/shared/i18n/locale.ts:9`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `AppLayout` | Function | `apps/frontend/src/app/layout.tsx` | 25 |
| `normalizeLanguage` | Function | `apps/frontend/src/shared/i18n/locale.ts` | 5 |
| `getBrowserLanguage` | Function | `apps/frontend/src/shared/i18n/locale.ts` | 9 |

## How to Explore

1. `gitnexus_context({name: "AppLayout"})` — see callers and callees
2. `gitnexus_query({query: "i18n"})` — find related execution flows
3. Read key files listed above for implementation details
