# Mama Voice Sprint — August 2026

**Goal in one line:** In 4 weeks, turn your vibe-coded voice RAG into *Mama Voice —
the first AI employee* (demoable product), and turn yourself into someone who can
answer any multi-agent orchestration interview question from lived experience.

**Assets you start with:** working realtime voice RAG (Nora AI), Llama 3.1 8B local,
Kokoro TTS, RTX 5060 Ti 16GB, RAG fundamentals (chunking/embeddings/vector search),
9 years of shipping, EzyGlobal production RAG experience.

---

## Truth mode — the calls this plan makes (read this first)

**1. You will not "learn LangChain + AutoGen + CrewAI + LlamaIndex" in a month.
Nobody does, and interviewers don't expect it.** These frameworks are thin wrappers
around the same five concepts: the agent loop, tools/function calling, state,
memory, and orchestration. Learn the concepts once, deeply, in ONE framework —
then each additional framework is a one-day translation exercise. The plan:

- **LangGraph** (LangChain's agent runtime) = your primary. It's what serious teams
  and interviews assume in 2026. Mama's brain gets built in it.
- **CrewAI** = 1 day. Rebuild one Mama skill as a crew. Now "I've used CrewAI" is true.
- **AutoGen** = 1 day. Same exercise, two-agent version.
- **LlamaIndex** = used for what it's actually best at: the RAG/data layer.
  You'll swap it in as Mama's retriever and compare against your hand-rolled one.

After this you can say, honestly: *"I built a production voice agent on LangGraph,
and I've implemented the same orchestration pattern in CrewAI and AutoGen —
here's my comparison of when I'd pick each."* That sentence wins interviews.
"I did the tutorials of four frameworks" does not.

**2. No telephony this month.** Twilio/SIP integration, real-call barge-in, and
production Bangla ASR is a quarter of work by itself. Month-1 Mama Voice is
**browser-based (mic in the browser, WebRTC/websocket to your machine)**. That is
fully demoable — to an employer on a screen-share, and to a clinic owner sitting
at their desk. Phone calls are Month 2. Don't let the roadmap eat the sprint.

**3. "I vibe coded it" is a liability in interviews — this sprint fixes that.**
The rule for the month: every component you vibe-coded gets re-read line by line,
and at least one layer (the agent loop itself) gets **rewritten by hand, from
scratch, no AI assist**, so you can whiteboard it. You keep using Claude Code /
Antigravity for everything else — that's your normal workflow and it's a selling
point — but the core loop must live in your head.

**4. Park Mama OS.** The 2027–2030 roadmap, the "Powered by MAMA" reveal, Mama
Flow/Code/Search — that's positioning, and your positioning instinct is genuinely
good ("The First AI Employee," not "AI receptionist" — correct call, it makes the
product a platform-in-waiting without saying so). But it's marketing copy, and it's
already 80% written in your own words. Budget it **one afternoon** (Day 26). The
engineering month goes to latency, booking, and reliability — the things that make
a clinic owner trust it. A vision without a <2s response time is a landing page.

**5. Bangla is the moat AND the hard part — sequence it honestly.** Whisper's
Bangla is mediocre; fine-tuned Bengali models exist but need evaluation on real
audio. Demo in English first (works for interviews + upmarket BD customers), and
spend one dedicated day (Day 25) evaluating Bangla ASR options with a real test
set of 30 recorded phrases. Also truth: BD SMEs live on **phone calls and Facebook
Pages/WhatsApp** — a Messenger text-agent may be a faster first sale than voice
telephony. Note it, don't build it this month.

**6. What "done" means on Aug 28** — the checklist at the bottom. If the month
gets hard, cut scope from the edges (CrewAI/AutoGen days, Bangla day), never from
the core: LangGraph brain + voice loop + booking + evals.

---

## The four weeks

### Week 1 (Aug 1–7): The brain, text-only — `01` + `03`
Build **Mama Brain** in LangGraph: supervisor + tools, no voice yet.
- Study: agent loop, ReAct, planning, function calling, state (file `01`).
- Build: text chat agent with 3 tools — `search_knowledge` (your existing RAG),
  `book_appointment` (stub writing to SQLite), `get_business_info` (structured FAQ).
- Hand-rewrite exercise: the raw agent loop in plain Python + Ollama, no framework
  (file `01`, section 5). ~80 lines. This is your whiteboard insurance.
- **Deliverable:** terminal chat with Mama that answers from docs and books a slot.

### Week 2 (Aug 8–14): Multi-agent orchestration + framework breadth — `02` + `03`
- Refactor Mama Brain into **supervisor + specialist agents**: Reception (routing,
  chit-chat), Knowledge (RAG + citations), Scheduler (calendar tools). Shared state,
  handoffs, context compression when history grows.
- Build the **eval harness**: 12 golden conversations, scripted, run on every change.
- Day 12: rebuild Scheduler as a **CrewAI** crew. Day 13: **AutoGen** two-agent
  version. Day 14: swap retriever for **LlamaIndex**, compare quality on your evals.
- **Deliverable:** multi-agent Mama passing 12/12 evals + a written framework
  comparison (this doc becomes an interview answer AND a blog post).

### Week 3 (Aug 15–21): Voice — `04`
- Wire Mama Brain into a streaming voice pipeline: browser mic → VAD →
  faster-whisper (streaming) → LangGraph brain (token streaming) → Kokoro
  (sentence-chunked) → browser. Use **Pipecat** for the plumbing (or upgrade your
  existing pipeline if it's close — decision guide in `04`).
- Barge-in (user interrupts, Mama stops talking), latency instrumentation.
- Real Google Calendar booking replaces the SQLite stub.
- **Deliverable:** talk to Mama in the browser, voice-to-voice p50 under 2s,
  interrupt her mid-sentence, book a real calendar slot.

### Week 4 (Aug 22–28): Product + interview readiness — `05` + `06`
- Day 22–23: hardening — error paths (ASR garbage, tool failure, silence), call
  summary generation, session persistence.
- Day 24: **2-minute demo video** (clinic scenario, script in `05`) + repo README
  with architecture diagram.
- Day 25: Bangla ASR evaluation day (protocol in `04`).
- Day 26 (afternoon): landing copy — "Meet your first AI employee." Your draft,
  tightened. One page.
- Day 27–28: interview drill (file `06`), update AI resume with Mama bullets,
  2 mock interviews (ask Claude Code to grill you from file `06`).

---

## Done = all of these exist on Aug 28

- [ ] Repo: Mama Voice — LangGraph brain, supervisor + 3 agents, voice loop, evals
- [ ] Voice demo working locally, p50 voice-to-voice < 2s, barge-in works
- [ ] Real Google Calendar booking via voice
- [ ] 12-conversation eval suite, passing, run via one command
- [ ] CrewAI + AutoGen ports of one skill + written comparison
- [ ] LlamaIndex retriever comparison note
- [ ] Hand-written agent loop (no framework, no AI assist) you can explain cold
- [ ] 2-min demo video + README with architecture diagram
- [ ] Bangla ASR evaluation note (what works, what doesn't, what you'd do)
- [ ] Landing page copy (one page)
- [ ] Resume updated: "Built Mama Voice, a multi-agent voice AI employee..."
- [ ] File `06` internalized — mock interview passed

## Files in this folder

| File | What it is |
|---|---|
| `01-agent-core.md` | Agent loop, ReAct, planning, function calling, memory, context compression — plus LangGraph crash course and the hand-rewrite exercise |
| `02-frameworks-map.md` | LangChain/LangGraph vs CrewAI vs AutoGen vs LlamaIndex (+ Pydantic AI): honest one-paragraph verdicts, minimal code in each, the 1-day translation exercises, interview one-liners |
| `03-multi-agent-patterns.md` | Supervisor, hierarchical, handoffs, shared state, planner-executor, critic loops — and the failure modes interviewers love to probe |
| `04-voice-pipeline.md` | Streaming voice architecture, latency budget on your 5060 Ti, VAD/barge-in, Pipecat, Bangla ASR truth |
| `05-build-plan.md` | Mama Voice build spec: skills architecture, day-by-day tasks, acceptance criteria, demo script |
| `06-interview-drill.md` | The questions you'll get on autonomous agents & multi-agent orchestration, with answers grounded in what you built |
