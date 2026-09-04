# 06 — Interview Drill: Autonomous Agents & Multi-Agent Orchestration

Read after Week 2, drill in Week 4. Every answer below assumes you finished the
build — replace bracketed bits with YOUR real numbers and war stories. The
pattern for every answer: **concept in one sentence → how Mama does it → a real
number or war story.** That triple is what "production experience" sounds like.

---

## A. Fundamentals

**"How does an AI agent actually work?"**
An LLM in a loop with tools and state: model sees the conversation plus tool
schemas, either answers or emits a structured tool call; my code validates and
executes the call, appends the result, and loops. Everything else — ReAct,
planning, multi-agent — is elaboration on that loop. I've written the loop raw
in ~100 lines of Python against a local model, and in production I use LangGraph
for the state machine, persistence, and streaming. *(You can offer to whiteboard
it — you wrote it twice in Week 1.)*

**"ReAct vs plan-and-execute?"**
ReAct decides one step at a time — right when each step depends on the last
observation, like conversation. Plan-and-execute plans upfront and replans on
failure — right for long tasks where wandering is expensive. Mama Voice is
ReAct per user turn: a receptionist's plan is rarely more than three tool calls,
and in voice, every unnecessary planning call is audible dead air.

**"How do you handle unreliable function calling on smaller models?"**
On Llama 3.1 8B I see [your real %] malformed or wrong-tool calls. Mitigations:
Pydantic validation on every call with the validation error returned as the tool
result so the model self-corrects; one retry; iteration cap of 5; and tool-choice
accuracy tracked in my eval suite so prompt changes can't silently regress it.

**"How do you manage context/memory?"**
Three layers: working memory (the message history), compression (past a token
budget, a local-model call summarizes the older half into a system note — keeps
recency verbatim), and long-term memory (call summaries and caller profiles in
SQLite, retrieved by caller identity — RAG over your own history). In voice,
compression is a latency feature, not just a cost feature: time-to-first-token
scales with context, and dead air is the thing users punish.

## B. Multi-agent orchestration

**"When do you actually need multiple agents?"** *(trap question — they want
restraint)*
Usually you don't — a single agent with good tools beats a badly coordinated
committee, and every extra agent is another LLM call and another place to lose
context. I split when: the tool set grows past reliable selection, sub-tasks
want different prompts/models, or work must parallelize. Mama hit the first two:
chit-chat, cited document Q&A, and transactional booking want different
temperatures, prompts, and context — so: supervisor plus three specialists,
each with a reason to exist.

**"Walk me through your architecture."**
*(Draw it: supervisor → reception / knowledge / scheduler, shared MessagesState +
typed CallState, voice pipeline in front, one async seam between them.)* Key
decisions to defend: supervisor routing is a small structured-output
classification call to keep the hop cheap; facts cross agents through typed
CallState, not prose, because re-parsing names out of chat history is how
handoffs lose data; any write-action (booking) passes a deterministic validator
— an LLM critic only where the check can't be code.

**"How do agents share state without stepping on each other?"**
Full-shared-history is simple but bloats context and distracts specialists;
fully-scoped context is efficient but the orchestrator must guess relevance.
Mama: shared history (calls are minutes long) + structured CallState for the
facts that must never be lost. If sessions were long-lived I'd move to scoped
briefs per specialist.

**"What failure modes have you hit?"** *(use your real ones — you logged them)*
Delegation loops (fixed: routing history + caps); handoff context loss (fixed:
typed state); wrong-tool selection as tools grew (the original reason to split);
error cascades — [your real example, e.g. the supervisor prompt change that
broke booking routing, caught by evals]. That last pattern is why nothing merges
without the golden-suite run.

**"Compare the frameworks."** → deliver the one-liner from `02`, then your real
Day 12–14 findings. You have a written comparison; offer to share it.

**"How do you evaluate/test agents?"**
Golden conversations asserting tool calls and args (deterministic) first, string
assertions second, LLM-as-judge with a rubric last and judged by a different
model. 12 scenarios including adversarial ones; tracked metrics: pass rate,
tool-choice accuracy, LLM calls per turn, latency. [Your real regression story.]

## C. Voice (your differentiator — steer toward it)

**"What's hard about voice agents specifically?"**
Latency is the product: p50 voice-to-voice under 2s or it feels broken. That
means streaming at every stage — STT partials, token streaming, sentence-chunked
TTS — plus barge-in (continuous VAD, cancel synthesis and playback mid-stream),
echo cancellation so the agent doesn't hear itself, and covering tool-call turns
with natural filler speech because a tool round-trip is two LLM calls of dead
air. My numbers: [p50 X.Xs, p95 Y.Ys] on a single RTX 5060 Ti, fully local —
Whisper, Llama 3.1 8B, Kokoro, no cloud APIs.

**"Why local models?"** Privacy (clinic/law-firm conversations shouldn't transit
third-party APIs — same reason I self-hosted Llama at EzyGlobal), unit economics
at scale, and for Bangladesh, resilience and cost. Trade-off stated honestly:
frontier models call functions more reliably; I engineered around an 8B with
validation-and-retry loops and eval gating — which taught me more than a
reliable model would have.

## D. Curveballs

**"How would you scale this to 100 concurrent calls?"**
Honest framing: today it's single-tenant on one GPU. Path: the brain is stateless
between turns (checkpointer holds state), so it scales horizontally behind a
queue; LLM serving moves from Ollama to vLLM for batched throughput; STT/TTS
become pooled services; the bottleneck is GPU seconds per conversation-minute —
[you can estimate from your instrumentation]. I'd measure before adding boxes.

**"Security/safety of autonomous agents?"**
Least-privilege tools (the scheduler can write calendar events, nothing can
delete or email); deterministic validation before any state-changing action;
prompt-injection awareness — RAG documents are untrusted input, so the knowledge
agent cites sources and write-actions never trigger from retrieved text alone;
iteration caps; full audit log of every tool call. For an "AI employee," the
audit log is also the customer-trust feature.

**"What would you build next?"** Telephony transport (Twilio) since the brain is
transport-agnostic behind one seam; Bangla ASR per my evaluation notes [say the
actual conclusion]; then a Messenger/WhatsApp transport — for Bangladesh SMEs
that channel may beat voice to first revenue.

## E. Drill protocol (Day 27–28)

Have Claude Code run two 30-minute mocks: (1) sections A–B cold, no notes,
follow-ups allowed; (2) "screen-share Mama, walk me through it, defend every
decision" — practice *saying the numbers out loud*; candidates who know their
p50 sound like owners. Score yourself: any question where you reached for a
definition instead of a war story → reread that section, re-drill next day.
