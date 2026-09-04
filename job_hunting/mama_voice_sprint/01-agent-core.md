# 01 — Agent Core: Reasoning, Planning, Execution

Week 1 material. By Friday you should be able to explain every section out loud
without looking, and have Mama Brain (text-only) running.

---

## 1. What an "autonomous agent" actually is

Strip the hype: an agent is **an LLM in a loop with tools and state**.

```
while not done:
    response = llm(system_prompt + state.messages + tool_definitions)
    if response.has_tool_calls:
        results = execute(response.tool_calls)
        state.messages += [response, results]     # loop continues
    else:
        return response.text                       # done
```

Everything else — ReAct, planning, multi-agent, orchestration — is elaboration on
this loop. When an interviewer asks "how do agents work," start here, then add
layers. Interviewers distrust candidates who start at the framework layer.

**The three capabilities in the job-post language:**
- **Reasoning** = the model thinking about what to do next, visible in its output
  (chain-of-thought / the "Thought:" step in ReAct, or native extended thinking in
  modern models).
- **Planning** = decomposing a goal into steps *before* executing (explicit plan
  step, plan-and-execute pattern), vs. deciding one step at a time (ReAct).
- **Execution** = tool calls: the model emits structured JSON matching a tool
  schema, *your code* runs the tool, the result goes back into context. The model
  never executes anything itself — a point interviewers use to check if you've
  actually built one.

## 2. ReAct vs Plan-and-Execute (know when each wins)

**ReAct** (Reason + Act): think → act → observe → think → ... One step at a time.
- Wins when: the next step depends on what the last tool returned (most chat
  agents, Mama included — you can't plan a booking before knowing availability).
- Cost: more LLM round-trips, can wander on long tasks.

**Plan-and-Execute:** planner LLM writes a step list; executor runs steps; planner
revises on failure.
- Wins when: long multi-step tasks where wandering is expensive (research agents,
  code migration). The plan itself is checkpointable and inspectable.
- Cost: plans go stale; you need a replan trigger.

**Mama's answer:** ReAct at the conversation level (each user turn = short
reasoning cycle), because a receptionist's "plan" is at most 2–3 tool calls.
Say this in interviews — matching pattern to problem is the senior signal.

## 3. Function calling — the exact mechanics

You know this from your RAG work; make it precise enough to whiteboard:

1. You send `tools=[{name, description, input_schema (JSON Schema)}]` with the
   request.
2. Model returns `stop_reason: "tool_use"` + a block like
   `{name: "book_appointment", input: {"date": "2026-08-15", "time": "10:00"}}`.
3. You validate the input (Pydantic — never trust model output), run the function,
   append a `tool_result` message, call the model again.
4. Repeat until the model answers in text.

**Details that mark you as someone who has done it:**
- Tool descriptions are prompts. Bad description = tool never called or called
  wrong. Iterating on tool descriptions is real work.
- Parallel tool calls: models can emit several calls in one turn; run them
  concurrently, return all results together.
- Error results are context, not exceptions: return `"error: no slots on that
  date"` as the tool result and let the model recover conversationally.
- Max-iteration guard: cap the loop (Mama: 5) so a confused model can't burn
  tokens forever.

## 4. Memory & context compression

Three layers, name them in interviews:

1. **Working memory** = the message history in context. Grows every turn.
2. **Compression** = when history exceeds a budget (Mama: ~3000 tokens), summarize
   the older half with a cheap/local LLM call into one system note ("Caller is
   Rahim, asked about insurance coverage, prefers Tuesday appointments") and drop
   the raw turns. Keep the last N turns verbatim — recency matters most.
3. **Long-term memory** = store outside context, retrieve on demand: the caller
   profile in SQLite/Postgres, past-call summaries retrieved by phone number.
   This is just RAG over your own conversation history — you already know RAG.

For **voice** agents compression matters more: latency scales with context length,
so a bloated history literally makes Mama slower to speak. That linkage
(context length → time-to-first-token → dead air) is an answer nobody without
voice experience gives.

## 5. THE HAND-REWRITE EXERCISE (Day 5–6, no AI assist)

Write `mama_loop.py` from scratch: plain Python + `ollama` client, no framework.
Requirements — it must:
- hold a message list, send tools, parse tool calls, dispatch to real functions
  (`search_knowledge` calling your existing vector store, `book_appointment`
  writing SQLite), append results, loop, with a 5-iteration cap;
- compress history when it exceeds a token budget (rough count is fine);
- stream tokens to stdout as they arrive.

~80–120 lines. When it works, delete it and write it again the next day in half
the time. This is the single highest-leverage interview prep in the whole sprint:
"implement an agent loop without a framework" is a real interview task, and
having done it twice, you'll be calm.

## 6. LangGraph crash course (your primary framework)

LangGraph models an agent as a **state machine**: a typed state object + nodes
(functions that update state) + edges (routing, possibly conditional). It exists
because raw LangChain chains were linear, and agents need cycles.

Core vocabulary (interviewers expect these words):
- **StateGraph** — the graph; state schema usually extends `MessagesState`.
- **Nodes** — functions `(state) -> state update`. An LLM call is a node; a tool
  executor is a node.
- **Conditional edges** — routing functions: after the LLM node, route to tools
  if there are tool calls, else END.
- **Checkpointer** — persistence of state per `thread_id`; gives you resumable
  conversations, time-travel debugging, and human-in-the-loop interrupts for free.
  (Mama: checkpointer keyed by call/session id.)
- **`create_react_agent`** — prebuilt one-liner ReAct agent; fine for single
  agents, you'll outgrow it in Week 2 when the supervisor arrives.

Minimal Mama Brain v0 (Week 1 shape):

```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.1:8b", temperature=0.3)

def search_knowledge(query: str) -> str:
    """Search the business's documents for policies, services, and prices."""
    return my_existing_rag_search(query)          # you already have this

def book_appointment(date: str, time: str, name: str, phone: str) -> str:
    """Book an appointment slot. Dates as YYYY-MM-DD, time as HH:MM."""
    return book_into_sqlite(date, time, name, phone)

def get_business_info(field: str) -> str:
    """Get business facts: 'hours', 'address', 'services', 'phone'."""
    return BUSINESS_INFO.get(field, "unknown field")

agent = create_react_agent(
    llm,
    tools=[search_knowledge, book_appointment, get_business_info],
    prompt=MAMA_SYSTEM_PROMPT,
    checkpointer=SqliteSaver.from_conn_string("mama_state.db"),
)

# chat loop
cfg = {"configurable": {"thread_id": "session-1"}}
while True:
    user = input("You: ")
    for chunk in agent.stream({"messages": [("user", user)]}, cfg,
                              stream_mode="values"):
        ...  # print last message
```

Notes:
- Tool schemas are inferred from type hints + docstrings — which is why the
  docstrings above are written as prompts, not comments.
- Llama 3.1 8B does function calling, but less reliably than frontier models:
  expect occasional malformed calls. Your mitigations (validate with Pydantic,
  return the validation error as a tool result, retry once) are *exactly* the
  production war stories interviews want. Log every malformed call — that log
  is interview gold.
- In Week 2 you rebuild this as an explicit `StateGraph` with a supervisor —
  don't over-engineer Week 1.

## 7. Week 1 build order

- Day 1: read this file + LangGraph quickstart docs; run `create_react_agent`
  hello-world against Ollama.
- Day 2: wire `search_knowledge` to your real Nora AI vector store; Mama answers
  doc questions in the terminal.
- Day 3: `book_appointment` → SQLite + `get_business_info`; multi-turn booking
  dialogue works (Mama asks for missing name/phone — that's the model, free).
- Day 4: checkpointer + context compression node; conversation survives restart.
- Day 5–6: hand-rewrite exercise (§5). Twice.
- Day 7: write `evals/golden.py` v0 — 5 scripted conversations asserting the right
  tool got called with the right args. Buffer + rest.
