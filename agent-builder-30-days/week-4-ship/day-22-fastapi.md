# Day 22: The Agent Behind FastAPI

**Goal:** a web service that wraps `agent.py`. Streaming, sessions, clean separation between the web layer and the agent.

## Paper first (20 minutes)

Draw the request path: browser, FastAPI, agent loop, Anthropic API, tools, database. Mark where the request blocks and where events flow back. Then write what the web layer needs to know about the agent. It should be: a function to call and a stream of events. Nothing else.

## Concepts

**Separate layers.** `agent.py` knows nothing about HTTP. `app/` knows nothing about tool internals. The interface between them is a generator of events. This lets you test the agent without a server and swap the server without touching the agent.

**Streaming over HTTP** is done with server sent events. One long response, lines of `data: {...}`. The client reads them as they arrive. Text tokens, tool calls, tool results, and a final done event.

**Sessions are the store from week 2.** The service is stateless between requests. All state lives in SQLite now and in a real database later.

**Async matters here.** FastAPI is async. The Anthropic client has an async version. Blocking calls inside async handlers freeze every other request.

## Step 1: make the agent emit events

Add a generator method to `Agent` in `agent.py`. It yields dicts instead of printing:

```python
    def run_events(self, task: str, messages: list | None = None):
        """Same loop as run(), but yields events instead of logging."""
        messages = messages or []
        messages.append({"role": "user", "content": task})
        consecutive_errors = 0
        for step in range(1, self.max_steps + 1):
            messages[:] = shrink_old_tool_results(messages)
            messages[:], self.summary = fold_history(messages, self.budget_tokens, previous=self.summary)
            msg = ask(messages, system=self.system, tools=self.definitions, model=self.model)
            messages.append({"role": "assistant", "content": msg.content})
            for b in msg.content:
                if b.type == "text" and b.text.strip():
                    yield {"type": "text", "step": step, "text": b.text}
            if msg.stop_reason == "max_tokens":
                yield {"type": "done", "reason": "max_tokens"}; return
            tool_blocks = [b for b in msg.content if b.type == "tool_use"]
            if not tool_blocks:
                yield {"type": "done", "reason": "end_turn"}; return
            results = []
            for b in tool_blocks:
                yield {"type": "tool_call", "step": step, "name": b.name, "input": b.input}
                r = self._run_tool(b)
                yield {"type": "tool_result", "step": step, "name": b.name,
                       "error": bool(r.get("is_error")), "content": str(r["content"])[:500]}
                results.append(r)
            consecutive_errors = consecutive_errors + 1 if all(r.get("is_error") for r in results) else 0
            messages.append({"role": "user", "content": results})
            if consecutive_errors >= self.max_consecutive_errors:
                yield {"type": "done", "reason": "error_budget"}; return
        yield {"type": "done", "reason": "max_steps"}
```

Token level streaming inside a step is an upgrade for later. Step level streaming is enough to make the UI feel alive.

## Step 2: the service

Create `app/__init__.py` (empty) and `app/main.py`:

```python
from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import Agent, Tool
from memory.store import MemoryStore
from tools.memory_tools import make_memory_tools
from app.clinic_tools import clinic_tools   # wraps the MCP server functions as Tool objects
from llm import spend

app = FastAPI(title="Clinic Receptionist Agent")
store = MemoryStore("app.db")

SYSTEM = """You are the receptionist for a small clinic. Be warm and brief.
Use search_knowledge for any factual question. Use check_availability before booking.
Always confirm doctor, time, name, and phone with the patient before calling book_appointment."""


class ChatIn(BaseModel):
    user_id: str
    session_id: str | None = None
    message: str


def build_agent(user_id: str) -> Agent:
    tools = [Tool(d, f) for d, f in make_memory_tools(store, user_id)] + clinic_tools()
    return Agent(system=SYSTEM, tools=tools, max_steps=10, budget_tokens=20_000, verbose=False)


@app.get("/health")
def health():
    return {"ok": True, "spend": spend.report()}


@app.post("/chat")
async def chat(body: ChatIn):
    session_id = body.session_id or str(uuid.uuid4())
    saved = store.load_session(session_id)
    messages = saved[0] if saved else []
    agent = build_agent(body.user_id)

    def gen():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        for ev in agent.run_events(body.message, messages):
            yield f"data: {json.dumps(ev)}\n\n"
        store.save_session(session_id, body.user_id, messages,
                           agent.summary.render() if agent.summary else None)

    async def agen():
        # run the sync generator in a thread so the event loop stays free
        loop = asyncio.get_running_loop()
        it = iter(gen())
        while True:
            chunk = await loop.run_in_executor(None, lambda: next(it, None))
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(agen(), media_type="text/event-stream")
```

Create `app/clinic_tools.py` that imports the three functions from `mcp_server/server.py` and wraps them as `Tool(definition, fn)` with the same descriptions. Yes, this duplicates the schema by hand. Tomorrow you will see why keeping the MCP server as the source of truth is nicer. For today, get it working.

## Step 3: run and call it

```bash
uv run fastapi dev app/main.py
```

```bash
curl -N localhost:8000/chat -H 'content-type: application/json' \
  -d '{"user_id":"mahbub","message":"Is Dr Rahman free on 2026-09-07 at 11:00?"}'
```

Watch the events stream. Take the session id from the first event and send a second message with it. Confirm the agent remembers.

## Step 4: a tiny frontend

A single `app/static/index.html` with a text box and a div that appends events from `EventSource`, or a `fetch` reader on the POST stream. Twenty lines of JavaScript. Serve it with `StaticFiles`. This is your demo surface for day 27.

## Step 5: test the service

Create `app/test_api.py` with `TestClient`. Test that `/health` returns ok, that `/chat` returns a session event first, and that a second call with the session id works. Mock `ask` so tests do not hit the API.

## Exercise, without AI

Explain why `run_in_executor` is there, and what would happen without it under ten concurrent users.

## Check yourself

1. What does the web layer know about the agent?
2. Why server sent events rather than a websocket for this?
3. Where does session state live?
4. What happens if the client disconnects mid stream?

## Common mistakes

- Calling the sync Anthropic client directly inside an async handler.
- Keeping sessions in a Python dict. Gone on restart, wrong with two workers.
- Sending the whole history back to the client on every event.

## Done when

- Streaming works from curl and from the page.
- Sessions resume.
- API tests pass without network.
- Sticky note: "If a user complains, what do I need to see?"
