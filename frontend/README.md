# frontend/

React + TypeScript + Vite + Tailwind app for Archero 2 Optimizer, built in **Module 4**.
See `docs/installation.md` ("Frontend setup") for how to run it, and
`docs/architecture.md` ("Frontend architecture") for design notes.

## Status

- **My Account** and **Build Optimizer** are fully functional against the real backend
  API — no mock data. My Account can create/switch accounts and manage every ownership
  type (heroes, weapons, armor, rings, amulets, pets, runes, skills) plus chapter
  progress; Build Optimizer calls the Skill Advisor (`POST /optimizer/skills/advise`)
  for a real, build-dependent recommendation.
- **Dashboard**, **Upgrade Advisor**, and **Settings** are honest placeholders — they
  say why they're not built yet (the backend advisors/endpoints they'd need don't exist
  yet) rather than faking data or a working feature.

## Scripts

```bash
npm run dev        # start the Vite dev server (http://localhost:5173)
npm run build       # type-check (tsc -b) + production build
npm run lint         # oxlint
npm run typecheck    # tsc -b --noEmit
npm run test         # vitest run
```

Requires the backend running separately (`cd ../backend && uvicorn app.main:app --reload`)
— see `VITE_API_BASE_URL` in `.env.example`.
