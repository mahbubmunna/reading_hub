# 04 — The Voice Pipeline

Week 3. You've already built a realtime voice RAG, so this is an upgrade pass,
not a first build: make it interruptible, make it fast, put the LangGraph brain
behind it, and measure everything.

---

## 1. Architecture

```
Browser mic ──▶ transport (WebRTC/websocket)
                    │
                    ▼
              VAD (silero) ──── detects speech start/stop, drives barge-in
                    │
                    ▼
              STT: faster-whisper (streaming, GPU)
                    │  partial + final transcripts
                    ▼
              MAMA BRAIN (LangGraph, token streaming)
                    │  tokens
                    ▼
              sentence chunker ── first full sentence → TTS immediately
                    │
                    ▼
              TTS: Kokoro (GPU) ──▶ audio frames back to browser
```

The principle that beats every clever trick: **stream at every stage, never wait
for anything to finish.** STT emits partials while the user speaks; the brain
starts on final transcript (not after silence padding); TTS starts on the first
completed *sentence*, not the full reply; audio plays while later sentences are
still generating.

## 2. Latency budget (your 5060 Ti 16GB — realistic numbers)

Voice-to-voice = user stops speaking → Mama's audio starts. Target **p50 < 2s**,
stretch 1.2–1.5s. Humans notice ~500ms; tolerate ~1s if the agent plays a subtle
acknowledgment. Above 3s they assume it's broken.

| Stage | Budget | Notes |
|---|---|---|
| End-of-speech detection (VAD) | 200–400ms | Silence threshold; too short = cuts users off, too long = dead air. Tune per use case. |
| STT final transcript | 100–300ms | faster-whisper `small`/`medium`, int8/fp16, streaming — final arrives almost at end-of-speech |
| Brain: time-to-first-*sentence* | 400–900ms | 8B Q4 on your GPU; the variable that context length inflates — compression is a latency feature |
| TTS first audio chunk | 100–200ms | Kokoro is fast; synthesize per sentence |
| Network/buffering | ~100ms | Local network, negligible |

**VRAM check (16GB):** Llama 3.1 8B Q4_K_M ≈ 5–6GB + faster-whisper medium ≈
1.5–2GB + Kokoro (small) + embedding model ≈ 1GB → roughly 9–10GB. Fits with
room. If tight: whisper `small` (barely worse for English) or Q4 the LLM harder.

**Tool-call turns are the latency trap:** transcript → model → tool → model →
speech is *two* LLM round-trips. Mitigation (interview-worthy): when the brain
emits a tool call, immediately speak a natural filler from a canned set — "Let me
check that for you" — synthesized *while* the tool runs. Receptionists do exactly
this; it converts dead air into naturalness. This one trick is the difference
between a demo that feels broken and one that feels alive.

## 3. Barge-in (the feature that separates toys from products)

User starts talking while Mama speaks → Mama shuts up and listens.
Mechanics: VAD runs *continuously*, including during TTS playback. On speech
detected mid-playback: (1) stop audio output immediately, (2) cancel pending TTS
synthesis and the LLM stream (asyncio task cancellation), (3) mark in state where
the reply was cut ("was answering about opening hours, got interrupted") so the
brain has context, (4) process the new utterance.
Gotcha: if mic picks up Mama's own speaker output, VAD self-triggers — use echo
cancellation (browser WebRTC gives you AEC free; another reason browser-first is
the right month-1 call) or headphones for the demo.

## 4. Pipecat vs upgrading your own pipeline

**Pipecat** (open-source, python) is the de-facto voice-agent plumbing framework:
frame-based pipeline (transport → VAD → STT → LLM → TTS), barge-in handling,
WebRTC + websocket + (later) Twilio transports, pluggable local services — it
supports exactly your stack (faster-whisper, Ollama-style LLM endpoints, local
TTS). LiveKit Agents is the other big name (heavier, tied to LiveKit infra).

Decision rule:
- If your current vibe-coded pipeline already streams and you understand it →
  **keep it**, add VAD/barge-in/metrics. You'll understand every line, which is
  the sprint's point.
- If it's request-response-ish (record → transcribe → generate → speak) or
  fragile → **rebuild on Pipecat** (~2 days) and port your components in.
  Knowing Pipecat is itself a resume keyword: "voice agent orchestration."

Either way, the LangGraph brain stays framework-agnostic behind one async
function: `async def mama_respond(session_id, transcript) -> AsyncIterator[str]`.
Voice layer and brain communicate only through that seam — clean architecture
you can diagram in interviews, and it means the same brain later serves phone,
WhatsApp, and web chat. **That seam is the "Mama is one employee with many
channels" architecture, realized.**

## 5. Instrumentation (Day 20 — do not skip)

Log per turn: end-of-speech ts, final-transcript ts, first-token ts,
first-sentence ts, first-audio ts, tool time, tokens in/out, calls per turn.
Print a per-call latency table at session end; keep p50/p95 across a 20-turn
test script. **"My p50 voice-to-voice is 1.4s, p95 is 2.6s — the p95 tail is
tool-call turns, here's the filler-phrase mitigation" is the single most
hireable sentence this sprint produces.** Nobody says numbers like that from
tutorials.

## 6. Bangla ASR — Day 25 evaluation protocol (truth included)

Truth: Whisper's Bangla is far below its English; accents and phone-quality audio
make it worse. This is also exactly why Mama-in-Bangla is a moat — if it were
easy, everyone would have it.

Protocol:
1. Record 30 test phrases: 10 clinic/booking phrases, 10 general questions,
   10 with names/numbers/dates (the killers) — your voice + 1–2 other speakers,
   phone-mic quality.
2. Run: whisper `large-v3` (rent an hour of cloud GPU if needed for the eval),
   whisper `medium`, at least one Bengali fine-tune from HuggingFace (search
   current leaderboard for bn ASR — e.g. tugstugi/bengaliai or newer), and
   Google Cloud STT bn-BD (paid API, quality ceiling reference).
3. Score word error rate, but *weight names/dates/numbers* — a receptionist that
   mishears the phone number is useless regardless of overall WER.
4. Write `bangla-asr-notes.md`: what's viable, what it costs, what you'd do
   (fine-tune? hybrid: Google STT for Bangla + local for English? English-first
   launch?). A written evaluation with numbers is a better artifact than a broken
   Bangla demo.

Also record the GTM truth for later: BD SMEs answer the world on phone calls and
Facebook Pages. A **Messenger/WhatsApp text version of the same brain** (that
seam in §4 makes it a transport, not a rewrite) may be a faster first paying
customer than voice telephony. Month 2 decision, not month 1.

## 7. Week 3 build order

- Day 15: decide keep-vs-Pipecat (§4). Get transcript→brain→speech running
  end-to-end, ugly.
- Day 16: streaming everywhere — partials, token stream, sentence-chunked TTS.
- Day 17: VAD tuning + barge-in.
- Day 18: tool-call filler phrases; Google Calendar API replaces SQLite stub
  (OAuth once, service account or your own calendar for demo).
- Day 19: session persistence (thread_id = session), call summary written to
  SQLite at session end — "call summaries" is a promised skill on your list,
  and here it costs one LLM call.
- Day 20: instrumentation + 20-turn latency run; tune whatever the numbers say.
- Day 21: buffer. Something above will have eaten a day. It's budgeted.
