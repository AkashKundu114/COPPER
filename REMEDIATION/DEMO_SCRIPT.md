# C.O.P.P.E.R. 5-Minute Evaluator & Recruiter Demo Script

This script provides an exact, reproducible 5-minute walkthrough to evaluate C.O.P.P.E.R. functionality without requiring multi-gigabyte local model downloads.

---

## Prerequisites (Under 2 Minutes)
- **Node.js**: v20+
- **Python**: v3.11+
- **Repository Clone**:
  ```bash
  git clone -b release/public-cleanup https://github.com/AkashKundu114/COPPER.git
  cd COPPER
  ```

---

## Step 1: Launch Standalone Demo Mode
Run the backend in offline demo mode (returns synthetic structured responses, full REST API contracts, and active Guardian safety without needing Ollama):

```bash
# Terminal 1 (Backend in Demo Mode)
python -c "import os; os.environ['COPPER_DEMO']='1'; import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"
```

Verify backend health in browser or curl:
```bash
curl http://127.0.0.1:8000/health
# Response: {"status":"healthy","ollama":...,"version":"0.1.0-alpha","demo_mode":true}
```

Now launch the frontend:
```bash
# Terminal 2 (Frontend)
cd frontend
npm.cmd run dev
# Vite runs at http://localhost:5173
```

Open `http://localhost:5173` in your browser or desktop window.

---

## Step 2: System Telemetry & Dashboard (Minute 1)
- Navigate to the **Dashboard** in the sidebar.
- Observe real-time system metrics: Host CPU core utilization, NVIDIA GPU VRAM allocation, system RAM footprint, and active agent statuses.
- Notice the responsive dark telemetry theme built with Tailwind CSS, Lucide icons, and Framer Motion.

---

## Step 3: Conversational Reflex & Cognitive Modes (Minute 2)
- Navigate to the **Chat** dock.
- Send a standard greeting: `"Hello COPPER, what is your architecture?"`
- Notice the instantaneous response dispatched through the ATLAS core conversational agent.
- Change the cognitive mode selector in the top-right of the chat dock to **Deep Thought** or **Concise**.

---

## Step 4: Guardian Safety Engine & Adversarial Friction (Minute 3)
- Enter an intentionally hazardous or destructive system payload:
  `python -c 'import os; os.system("rmdir /s /q C:\\Windows")'`
- Observe the immediate **Guardian Level 3 Interception Modal**:
  - Catastrophic Safety Barrier engaged.
  - Action halted with continuous dynamic friction score >= 2.85.
  - Reason and explicit confirmation prompt displayed.
- Test a commitment conflict prompt:
  `"Let's play video games until 5 AM tonight"` (when a sleep/health commitment exists in `data/commitments.json`).
  - Triggers Level 2 interactive conflict challenge.

---

## Step 5: Epistemic Decaying Memory (Minute 4)
- Navigate to the **Memory** tab in the sidebar.
- Inspect the four epistemic belief layers:
  - **Facts** (Confidence >= 0.85)
  - **Observations** (0.50 <= Confidence < 0.85)
  - **Hypotheses** (0.20 <= Confidence < 0.50)
  - **Deprecated** (< 0.20)
- Notice belief revision mechanics and causal provenance tracking.

---

## Step 6: 12-Agent Registry & Model Pools (Minute 5)
- Navigate to the **Agent Registry** tab in the sidebar.
- Verify the **12 active core agents**:
  - `ATLAS` (Chat & Coordination)
  - `FORGE` (Coding & Scripting)
  - `HERMES` (Email & Messaging)
  - `CHRONOS` (Scheduling & Time)
  - `ARGUS` (Vision & Screen Analysis)
  - `NEXUS` (Planner & Task Graph)
  - `MINERVA` (Research & Deep Web)
  - `SCRIBE` (Document & Report Generation)
  - `PROMETHEUS` (System & Automation)
  - `GUARDIAN` (Safety & Alignment)
  - `ECHO` (Voice & Audio)
  - `PICASSO` (Image Generation)
- Verify the **8 hardware model pool tiers** (`nano_reflex`, `mini_always_on`, `code_specialist`, `core_reasoner`, `vision_multimodal`, `planner_high_context`, `audio_neural`, `image_diffusion`).

---

## Step 7: Automated Verification (Under 30 Seconds)
To verify the entire test suite independently:
```bash
# Backend pytest suite (687 tests)
python -m pytest tests/ -q

# Frontend vitest suite (41 tests)
cd frontend && npm.cmd run test

# Frontend production build
npm.cmd run build
```
Result: **728 tests passed (100%), 0 build errors**.
