# COPPER — Live App (Backend + Brain UI)

A working backend and a "highly futuristic, minimal" frontend for COPPER:
a chat surface backed by a 30-agent + orchestrator routing system, with a
neural-network visualization of the agents that lights up as they work, and
a memory layer that makes COPPER (and each agent) actually get to know you
over time — preferences, projects, habits, and inside jokes that only show
up once you've earned them.

This is a real, running full-stack app — not a mockup. Both halves are
tested end-to-end (see "What's verified" below).

---

## Design pass — three directions considered

1. **3D WebGL brain/globe.** Visually flashy, but heavy to ship reliably
   and hard to verify without a live browser in the loop — rejected.
2. **Force-directed physics graph.** Organic, but non-deterministic layout
   risks nodes overlapping in ways I can't catch ahead of time — rejected.
3. **Fixed radial "ganglia" map, pure SVG.** Deterministic node positions
   (computed once, verified with a standalone script — 30 nodes, zero
   overlap, minimum 49px spacing), no WebGL dependency, cheap to animate.
   **Chosen.**

**The signature idea:** the product is literally named COPPER, so the
visual language leans into that instead of the generic near-black+acid-green
AI-dashboard look. Dormant agents are dim bronze filaments; the instant a
request routes through one, the pathway flares molten white-hot / electric
blue — like current through hot copper wire. A node's *resting* glow
brightness is tied to familiarity: a stranger-tier agent is barely-lit
metal, an Inner-Circle agent glows warm even at rest. Familiarity and
"synapse strength" are the same visual variable — memory made literally
visible in the wiring, not a separate stat panel bolted on.

---

## What's here

```
backend/
  app/
    data/agents.py            30 agents + COPPER: tiers, colors, personas, routing keywords
    memory/db.py               SQLite: user_profile, agent_memory, interactions (job log per node)
    memory/learner.py          fact extraction + familiarity tiers + callback/inside-joke logic
    routing/router.py          keyword-based agent routing
    services/orchestrator.py   the pipeline: route → animate → respond → remember
    api/routes/                chat (REST + WebSocket), agents, memory
    main.py                    FastAPI app
  requirements.txt

frontend/
  src/
    components/brain/NeuralBrain.tsx   the neural map — SVG, deterministic layout
    components/chat/ChatDock.tsx        minimal glass chat dock
    components/profile/SideDrawer.tsx   "what COPPER knows about you" + per-agent job log
    components/layout/TopBar.tsx        wordmark + relationship tier badge
    lib/layout.ts                       radial layout engine (tested standalone, see below)
    lib/useBrainSocket.ts                WebSocket → animation state machine
    lib/api.ts                          REST client
    data/agents.ts                       static agent metadata (mirrors backend)
  tailwind.config.js                    molten-copper design tokens
```

---

## How the memory / "getting to know you" system works

Every message goes through `orchestrator.py`:

1. **Route** — keyword match picks an agent, or COPPER answers directly.
2. **Animate** — a sequence of WebSocket events fires so the brain map can
   show the thought traveling from the COPPER core out to that agent's
   node in real time (`copper_thinking` → `route_decision` → `edge_pulse`
   → `agent_active` → `agent_speaking` → `memory_update` → `done`).
3. **Respond** — a persona line + a plain-language acknowledgement of the
   request, with an occasional memory callback layered in (see below).
4. **Remember** — three things happen in SQLite:
   - the agent's `familiarity_score` goes up (drives node glow + unlocks
     an "Acquaintance → Regular → Trusted → Inner Circle" tier for *that*
     agent specifically)
   - the interaction is appended to that agent's job log (`interactions`
     table) — this is "storing each instance and job in each node": click
     any node in the brain map to see its actual history
   - `learner.py` runs cheap regex/heuristic extraction over the message
     ("I'm working on X", "I prefer X over Y", late-night activity
     patterns, etc.) and upserts facts into `user_profile`, with a
     confidence score that grows the more a fact gets reinforced

The overall relationship tier (Just Met → Getting Acquainted → Regular
Collaborator → Trusted Partner → Inner Circle) is based on total
interactions across *all* agents, and gates how often — and how personal —
callback lines get. Early on COPPER says nothing personal; by "Regular
Collaborator" it starts referencing stored facts ("Still deep in {project}?
On it."); by "Trusted Partner"+ the frequency goes up. This was a deliberate
choice — it should feel earned, not random from message one.

**Honesty about what this is:** response generation is template-based
(persona line + heuristic topic summary + optional callback), not an LLM
call — this keeps the whole system runnable with zero API keys and fully
inspectable. `generate_reply()` in `orchestrator.py` is the single swap
point if you want to wire in a real model later; routing, memory, and the
brain animation don't need to change at all.

---

## Running it

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

SQLite file is created automatically at `app/data/copper_memory.db` on
first run — delete it any time to fully reset (or use the "Forget
everything" button in the UI, which does the same thing via `/api/memory/reset`).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env      # defaults to http://localhost:8000
npm run dev
```

Open the printed local URL. Backend must be running first (CORS is
pre-configured for `localhost:5173` and `localhost:3000`).

### Production build

```bash
cd frontend && npm run build   # outputs to dist/
```

---

## What's verified

Since I can't visually preview a browser from here, I leaned on tests that
don't require one:

- Backend: imported the app, listed all routes, ran the full request
  pipeline live (`uvicorn` + `curl`), confirmed routing/replies/familiarity
  growth/fact extraction/callback jokes all fire correctly, and watched the
  raw WebSocket event sequence end-to-end.
- Frontend: `tsc --noEmit` clean, `npm run build` clean, `oxlint` clean
  (0 warnings/errors), and the radial layout math verified standalone — 30
  nodes, zero NaN, minimum 49px pairwise spacing (comfortably more than
  2× node radius, so nothing overlaps).
- CORS preflight confirmed working against the real Vite dev origin.

What I couldn't verify directly: actual pixel-level rendering and animation
feel in a real browser. The code is written carefully and the underlying
math/logic is tested, but give the UI a look once it's running and flag
anything that reads off — spacing, motion timing, and color balance are the
things most likely to need a second pass with real eyes on it.
