# 02 — The Frameworks Map (truth-mode verdicts)

One paragraph of truth per framework, minimal code, and the 1-day translation
exercises that make "I've worked with X" an honest sentence. Interviewers ask
"which framework would you choose and why" constantly — this file is that answer.

---

## The one-table summary

| Framework | What it really is | Use when | Mama's use |
|---|---|---|---|
| **LangChain** | Ecosystem of integrations (model wrappers, loaders, retrievers). The "chains" part is legacy. | You need its integrations | Model/retriever glue under LangGraph |
| **LangGraph** | State-machine agent runtime (graphs, cycles, checkpoints). The serious part of the LangChain world | Production agents, complex control flow, persistence | **Primary — Mama's brain** |
| **CrewAI** | Role-based multi-agent ("agents are coworkers with roles/goals/backstories"), sequential or hierarchical process | Quick multi-agent prototypes; role metaphor fits the task | 1-day port of Scheduler (Day 12) |
| **AutoGen** (Microsoft) | Conversation-based multi-agent — agents talk to each other in group chats; strong on code-execution agents | Research-y multi-agent, agents-writing-code loops | 1-day port (Day 13) |
| **LlamaIndex** | Data framework: ingestion, indexing, retrieval done properly; has agents but that's not its center | The RAG layer of any agent | Retriever comparison (Day 14) |
| **Pydantic AI** | Type-safe single-agent framework: validated structured outputs, tools, deps injection | You want FastAPI-feeling agent code | You have notes on it from earlier prep; keep it as a talking point |

**The interview one-liner:** *"They all wrap the same loop. LangGraph gives me
explicit control flow and persistence, which production needs; CrewAI gets a
multi-agent prototype running in an afternoon; AutoGen shines when agents need to
converse or execute code; LlamaIndex is what I use for the data layer regardless
of which agent framework sits on top. For Mama Voice I chose LangGraph because a
voice agent needs deterministic routing, streaming, and resumable state — and I
ported one skill to CrewAI and AutoGen to check I wasn't missing anything."*

---

## LangChain vs LangGraph (people conflate them — don't)

LangChain (2022–23) = chains: linear pipelines, plus a huge integration library.
Agents in old LangChain (`AgentExecutor`) were a black-box while-loop — hard to
control, debug, or persist. LangGraph (2024+) is the successor for agents:
explicit graph, cycles allowed, state checkpointed. In 2026, "we use LangChain"
at a serious shop almost always means "LangGraph + LangChain integrations."
Saying this distinction out loud in an interview instantly separates you from
tutorial-level candidates.

## CrewAI — Day 12 exercise

Mental model: define **Agents** (role, goal, backstory, tools), **Tasks**
(description, expected output, assigned agent), a **Crew** (agents + tasks +
process). `Process.sequential` runs tasks in order; `Process.hierarchical` adds a
manager LLM that delegates.

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

@tool("check_availability")
def check_availability(date: str) -> str:
    """List free appointment slots for a date (YYYY-MM-DD)."""
    return slots_from_sqlite(date)

scheduler = Agent(
    role="Appointment Scheduler",
    goal="Find a slot matching the caller's preference and book it",
    backstory="Careful scheduler for a busy clinic; never double-books.",
    tools=[check_availability, book_slot],
    llm="ollama/llama3.1:8b",
)
task = Task(
    description="Caller wants: {request}. Find and book a suitable slot.",
    expected_output="Confirmation with date, time, and caller name",
    agent=scheduler,
)
crew = Crew(agents=[scheduler], tasks=[task], process=Process.sequential)
result = crew.kickoff(inputs={"request": "any afternoon next Tuesday, name Rahim"})
```

**Day 12 deliverable:** Scheduler skill working as a crew + 5 written sentences:
what was faster than LangGraph (setup, the role prompting you get for free), what
you lost (fine-grained control flow, streaming granularity, state persistence),
when you'd pick it (prototypes, content pipelines, demos). Those sentences ARE
the interview answer.

## AutoGen — Day 13 exercise

Mental model: agents are **conversable** — everything is agents exchanging
messages until termination. Classic pattern: `AssistantAgent` (LLM) +
`UserProxyAgent` (can execute code / represent the human); multi-agent =
`GroupChat` with a manager choosing the next speaker. Known honestly for: code
execution loops and research prototypes; also for API churn (the 0.2 → 0.4
event-driven rewrite; the community AG2 fork) — knowing that churn story is
itself a credible interview detail.

Day 13: two agents — "Receptionist" (talks to user) and "Scheduler" (has the
booking tools) — conversing to complete a booking. Same 5-sentence writeup:
you'll likely find the conversation paradigm is elegant for agent-to-agent
negotiation but harder to make deterministic than a LangGraph edge — say exactly
that in interviews.

## LlamaIndex — Day 14 exercise

Don't relearn RAG — you know RAG. Learn what LlamaIndex automates:
ingestion pipelines (`SimpleDirectoryReader` and 300+ loaders), node parsing
(sentence/semantic splitters), `VectorStoreIndex` over your existing vector DB,
retrievers (hybrid, auto-merging, rerankers), query engines, and evaluation
helpers.

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama

docs = SimpleDirectoryReader("clinic_docs/").load_data()
index = VectorStoreIndex.from_documents(docs)          # or over chroma/pgvector
qe = index.as_query_engine(llm=Ollama(model="llama3.1:8b"), similarity_top_k=4)
```

**Day 14 deliverable:** run your 12 golden eval questions against (a) your
hand-rolled retriever and (b) LlamaIndex's (try auto-merging or sentence-window
retrieval). Record which answered better and why. Whichever wins, the comparison
note is the deliverable — *"I benchmarked my hand-rolled retriever against
LlamaIndex sentence-window retrieval on a golden set"* is a sentence that gets
follow-up questions you want.

## Pydantic AI (carry-over from your earlier prep)

You studied it for the Pydantic-AI-requiring job. Keep the one-liner ready:
type-safe agents, tools via decorators, validated structured output
(`output_type=SomeModel`), dependency injection via `RunContext`. If asked to
compare: "Pydantic AI is what I'd pick for a single well-typed agent inside a
FastAPI service; LangGraph when I need multi-agent control flow and checkpointed
state — Mama needed the latter."

---

## Red flags to avoid in interviews

- Don't say "I know LangChain" and then describe only `load_qa_chain` tutorials.
- Don't claim all four equally. Claim depth in one + informed comparison — it
  reads as senior; a flat four-way claim reads as resume keyword stuffing.
- Never trash a framework the company uses. The comparison framing above lets you
  praise whatever they run while showing judgment.
