# Dashboard Layout Polish

## Problem

The Next.js frontend shell looked unfinished:

- Sidebar was plain white with no icons, no active-state, and no working navigation links (nav items were `<div>` elements)
- Topbar was a static text block with no contextual information
- `frontend/dashboard.html` was a standalone static prototype that couldn't be served by Next.js (it was not in `public/`) and was superseded by the live app

## Changes

### Sidebar (`frontend/src/components/layout/Sidebar.tsx`)

Converted to a Client Component to support `usePathname()` for active-link detection.

- Dark background (`bg-slate-900`) with a branded header and version footer
- Nav items are now `<Link>` components with real hrefs
- Active item highlighted via `bg-slate-700 text-white`; inactive items use `text-slate-400` with hover states
- Emoji icons per nav item (no new dependency)

Nav items:
| Label | href | Icon |
|---|---|---|
| Dashboard | `/` | ⊞ |
| Dwell | `/dwell` | ⏱ |
| Trucks | `#` (placeholder) | 🚛 |
| Alerts | `#` (placeholder) | 🔔 |

Active-link logic: exact match for `/`, prefix match for all other routes.

### Topbar (`frontend/src/components/layout/Topbar.tsx`)

Converted to a Client Component to support `usePathname()`.

- Page title derived from current route (`/` → "Dashboard", `/dwell` → "Dwell Analytics")
- Green pulsing "Live" badge (`animate-pulse`) to indicate real-time data
- Current date displayed in `"Tue, May 12, 2026"` format via `Intl` API

### Deleted

`frontend/dashboard.html` — static HTML/CSS prototype, now redundant.

## Files Changed

| File | Change |
|---|---|
| `frontend/src/components/layout/Sidebar.tsx` | Rewrite — dark theme, icons, routing, active state |
| `frontend/src/components/layout/Topbar.tsx` | Rewrite — dynamic title, live badge, date |
| `frontend/dashboard.html` | Deleted |

## Files Not Changed

All page and widget components are unchanged: `layout.tsx`, `page.tsx`, `dwell/page.tsx`, `KpiGrid`, `AlertList`, `TruckTable`, charts, `api.ts`, `types/`, `hooks/`.
