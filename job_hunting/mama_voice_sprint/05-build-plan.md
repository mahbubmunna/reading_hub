# 05 — Mama Voice: Build Spec & Week 4 Plan

The product definition for month 1, the skills architecture that makes
"AI employee, not receptionist" real in code, and the demo that sells it.

---

## 1. Positioning (settled — stop re-deciding it)

**Mama Voice — the first AI employee your business can hire.**
Receptionist is the first *job* it does, not what it *is*. Your instinct here is
right and the architecture below makes it true rather than just copy: skills are
plug-in modules on one employee, so "today receptionist, tomorrow sales rep" is
a config change, not a rebuild. One page of landing copy on Day 26, from your
own draft — it's already written, it needs cutting, not expanding.

What you do NOT say publicly this year: "OS", "platform", "multi-agent
architecture". (Engineers and investors get the architecture diagram; customers
get "it answers every call and never sleeps.") "Powered by MAMA" as a quiet
footer: fine, costs nothing.

## 2. Month-1 scope (the contract with yourself)

**IN:** browser voice demo · clinic persona ("Dhaka Dental Care" or similar,
fictional) · supervisor + 3 skills · RAG over the clinic's docs (services,
prices, policies — you write ~10 plausible pages) · real Google Calendar
booking · call summaries · barge-in · <2s p50 · eval suite · demo video.

**OUT (Month 2+, write them down so they stop tempting you):** telephony
(Twilio/SIP) · Bangla voice in production (evaluation only) · WhatsApp/Messenger
transport · CRM integration · payments · multi-tenant dashboard · Mama Flow/
anything OS.

## 3. Skills architecture (the "AI employee" made concrete)

A **skill** = specialist agent + its tools + its prompt + its evals, registered
on the employee:

```
mama/
  brain/
    supervisor.py      # routing graph (LangGraph StateGraph)
    state.py           # CallState: caller, intent, pending_booking, summary
    compression.py     # context compression node
  skills/
    reception/         # persona, greeting, routing fallback, out-of-scope refusals
    knowledge/         # RAG + mandatory citations   (agent.py, tools.py, evals/)
    scheduler/         # calendar tools + deterministic booking validator
  voice/
    pipeline.py        # transport, VAD, STT, TTS (Pipecat or yours)
    seam.py            # async def mama_respond(session_id, transcript) -> tokens
  evals/
    golden/            # 12 conversations, runnable: `make evals`
  server.py            # FastAPI: websocket audio + REST for summaries
```

Adding a future skill (lead qualification, FAQ for a law firm) = new folder in
`skills/` + one line in the supervisor's routing enum. **Demo this in the video:
it's the "hire one employee, teach it new jobs" pitch, in code.** This structure
is also your interview architecture diagram — draw it from memory.

## 4. The demo scenario (Day 24 — script it, don't improvise)

2-minute video, screen + your voice, one take is fine:

1. (0:00) One sentence: "This is Mama Voice, an AI employee, running entirely on
   my desk — no cloud APIs. I'm calling a dental clinic it works for."
2. (0:15) *"Hi, are you open Friday evening?"* → instant answer from business
   info. Point at the latency number on screen.
3. (0:35) *"How much is a root canal, and do you take Metlife insurance?"* → RAG
   answer **with the source document cited on screen**.
4. (1:00) *"Book me something Tuesday afternoon… actually make it Wednesday."*
   → Mama asks for name and phone, handles the change of mind, books — cut to
   **the real Google Calendar event appearing**.
5. (1:30) Interrupt her mid-sentence → she stops and handles it. (Barge-in is
   the moment technical viewers rewind.)
6. (1:45) Show the call summary that was auto-written. Close: "One employee,
   many skills. Receptionist is just its first job."

Post: GitHub README (top of repo), LinkedIn, and attach to applications. This
video does more for interviews than any certificate you could earn in the same
month.

## 5. Week 4 day-by-day

- **Day 22 — hardening:** the demo's failure paths. ASR garbage in → "sorry,
  the line's noisy, could you repeat?" (confidence threshold). Tool exception →
  spoken apology + logged. 20s silence → gentle prompt, then polite hangup +
  summary anyway. Kill the server mid-call, restart → session resumes
  (checkpointer earns its keep).
- **Day 23 — polish:** clinic doc set finalized, persona prompt pass (warm,
  brief, never robotic-verbose — voice replies must be *short*, this is a prompt
  discipline), full eval run green.
- **Day 24 — demo video + README:** script above; README = architecture diagram
  (the folder tree + the voice pipeline), latency table, eval results, "how to
  run". Pin the repo on GitHub.
- **Day 25 — Bangla ASR evaluation** (protocol in `04` §6) → `bangla-asr-notes.md`.
- **Day 26 — landing copy** (afternoon only): your "Meet your first AI employee"
  draft, one page, cut hard. Plus resume update — see §6.
- **Day 27–28 — interview drill:** file `06`. Have Claude Code mock-interview
  you twice: once on agent fundamentals, once on "walk me through Mama's
  architecture and defend every decision."

## 6. Resume bullets this month buys you (draft — final wording on Day 26)

For the AI resume:
- "Built **Mama Voice**, a local-first multi-agent voice AI employee: LangGraph
  supervisor orchestrating reception, RAG-knowledge, and scheduling agents, with
  streaming STT/TTS, barge-in, and sub-2s voice-to-voice latency on consumer GPU
  (Llama 3.1 8B, faster-whisper, Kokoro)."
- "Designed a plug-in skills architecture with typed shared state and
  deterministic action validation; 12-scenario golden eval suite gating every
  prompt and routing change."
- "Benchmarked hand-rolled retrieval vs LlamaIndex on a golden set; ported the
  scheduling skill to CrewAI and AutoGen to evaluate orchestration trade-offs."

Every clause above is only true if the checklist in README.md is done. That's
the deal.
