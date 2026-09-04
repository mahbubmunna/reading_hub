# 03 — Multi-Agent Orchestration Patterns

Week 2 material. The patterns, when each earns its complexity, and the failure
modes. Every section maps to something you'll build into Mama, so every answer
you give in interviews comes from a repo you can screen-share.

---

## 0. The truth interviewers respect most

**Most "multi-agent" systems shouldn't be.** A single agent with good tools beats
a badly coordinated committee — more agents means more LLM calls (cost, latency),
more places to lose context, and compounding error rates. The senior answer is:
*"I start single-agent, and split only when one of three pressures appears:
(1) the tool set / prompt gets too big and the model starts picking wrong tools,
(2) sub-tasks need different models or context, (3) parts must run in parallel."*
Mama hits pressure #1: reception chit-chat, document Q&A with citations, and
transactional booking want different prompts, temperatures, and context. That's
why she's a supervisor + 3 specialists — you have a *reason*, not a fashion.

## 1. Supervisor / router (Mama's pattern)

One coordinator LLM receives the user turn, routes to a specialist, specialist
responds (possibly using tools), control returns to supervisor.

```
            ┌────────────┐
   user ──▶ │ SUPERVISOR │──▶ reply
            └─────┬──────┘
       ┌──────────┼──────────┐
       ▼          ▼          ▼
  RECEPTION   KNOWLEDGE   SCHEDULER
  (chit-chat,  (RAG +      (calendar
   routing     citations)   tools)
   fallback)
```

In LangGraph: supervisor node with a **structured output** routing decision
(`next: Literal["reception","knowledge","scheduler","respond"]`), conditional
edges to specialist subgraphs, all sharing `MessagesState`.

- Pro: central control, easy to log/debug, predictable.
- Con: supervisor round-trip adds latency to every turn — in voice this is real
  money. **Mama's mitigation (say this in interviews):** the supervisor call is a
  small/fast classification (cheap prompt, low max_tokens, could even be a
  smaller local model), and trivially routable turns skip deliberation.

## 2. Handoffs / swarm

No standing supervisor: the current agent decides to transfer, calling a handoff
tool (`transfer_to_scheduler`) that moves the conversation. Popularized by
OpenAI's Swarm/Agents SDK.
- Pro: one fewer LLM call per turn; conversation feels continuous.
- Con: routing logic smeared across every agent's prompt; harder to audit.
- Interview line: "Handoffs are lower-latency, supervisors are more controllable.
  For a receptionist, I want an auditable center — the supervisor also gives me
  one place to enforce guardrails."

## 3. Hierarchical (supervisor of supervisors)

Teams of agents, each with its own lead. Only justified at real scale (a
research org of agents; a company-wide assistant with departments). Know it
exists; say you haven't needed it — that honesty scores better than pretending.
Mama OS someday = each Mama product (Voice, Flow, Code) as a team under one
orchestrator. Fine as a vision sentence; do not architect for it now.

## 4. Planner–Executor and critic loops

- **Planner–executor:** plan first, execute steps, replan on failure (covered
  in `01`). For long tasks, not chat turns.
- **Critic / reflection:** a second pass reviews the first agent's output
  against criteria before it ships. Costs one extra LLM call — use it where
  errors are expensive, skip it where they're cheap. **Mama uses exactly one
  critic:** before `book_appointment` executes, a validation step checks the
  slot is actually free and all fields are present. That's a *deterministic*
  critic (code, not LLM) — cheaper and stricter. Interview gold: "use an LLM
  critic only when the check can't be written as code."

## 5. Shared state — the actual hard problem

What multi-agent orchestration is *really* about: **who sees what**.
- Full shared history (all agents see everything): simple, but context bloats
  and specialists get distracted by irrelevant turns.
- Scoped context (each specialist gets a task brief + relevant slice): efficient,
  but the orchestrator must decide what's relevant — bugs live here.
- **Mama's design:** shared `MessagesState` (conversations are short — calls are
  minutes, not days) + a structured `CallState` object (caller name, phone,
  intent, pending booking fields) that every agent reads/writes. Facts move
  through typed state, not prose — "the scheduler shouldn't have to re-parse the
  caller's name out of chat history."

## 6. Context compression in multi-agent settings

Per-agent budgets: the supervisor keeps a running summary; specialists get
(summary + last N turns + CallState), never the raw full log. Compression is a
node in the graph, triggered by token count, executed by the local model
(free on your GPU). You built the single-agent version in Week 1; Week 2
generalizes it.

## 7. Failure modes (interviewers probe these — have war stories)

By Week 2 you'll have hit most of these on Llama 3.1 8B. **Write each incident
down when it happens** — a lived war story beats any textbook answer.

1. **Infinite delegation loops** — A routes to B, B routes back. Fix: iteration
   caps, supervisor remembers routing history, loop breaker returns to user.
2. **Context loss at handoff** — specialist missing a key fact. Fix: typed
   CallState, not prose.
3. **Wrong-tool selection** — worsens as tool count grows; the original reason
   to split agents. Track tool-choice accuracy in your evals.
4. **Error cascades** — bad RAG result → confident wrong answer → booking against
   a nonexistent service. Fix: citations required from Knowledge agent;
   deterministic validation before any write-action.
5. **Cost/latency blowup** — every agent-hop is an LLM call. Instrument
   calls-per-turn in your evals; in voice, each hop is audible dead air.
6. **Non-determinism in tests** — LLM outputs vary. Fix below.

## 8. Evals — the thing that makes you production-credible

12 golden conversations in `evals/`, run by one command, on every change:

- 4 × knowledge: doc questions → assert answer contains the golden fact AND a
  citation.
- 4 × booking: happy path, missing info (model must ask), unavailable slot
  (model must offer alternative), user changes mind (no orphan booking).
- 2 × routing: greeting → no tool calls, no specialist hop.
- 2 × adversarial: out-of-scope request ("prescribe medicine") → decline;
  contradictory info → clarifying question.

Assertion style, in order of preference: (1) **assert the tool call and its
args** — deterministic; (2) assert substrings/regex on the reply; (3) LLM-as-judge
with a rubric, only where 1–2 can't work, judged by a *different* model than the
one under test. Track per-run: pass rate, tool-choice accuracy, LLM calls per
turn, tokens per turn.

Interview line that lands: *"My eval suite caught a regression when I changed the
supervisor prompt — booking pass-rate dropped from 4/4 to 2/4 because it started
routing 'do you have anything Tuesday?' to Knowledge instead of Scheduler. That's
why I don't change prompts without running evals."* By Week 3 you will have a
real version of this story. Use your real one.

## 9. Week 2 build order

- Day 8: supervisor as explicit `StateGraph` — structured routing output,
  conditional edges; specialists still stubs.
- Day 9: Knowledge agent (RAG + mandatory citations) + Reception agent.
- Day 10: Scheduler agent + `CallState` + deterministic booking validator.
- Day 11: eval harness to 12 conversations; fix what fails (something will —
  that's the war story).
- Day 12: CrewAI port (file `02`). Day 13: AutoGen port. Day 14: LlamaIndex
  retriever comparison + write the framework-comparison note.
