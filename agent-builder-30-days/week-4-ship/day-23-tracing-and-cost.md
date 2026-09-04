# Day 23: Tracing and Cost Control

**Goal:** you can answer "what happened in request X" in under a minute, and the agent cannot spend more than you allow.

## Paper first (20 minutes)

A user says "it booked the wrong doctor". What do you need to see? The message, every model call with its inputs and outputs, every tool call with its arguments and results, timing, cost, the session. Now design the record that holds that.

## Concepts

**A trace is a tree.** One trace per request. Spans inside: one per model call, one per tool call. Each span has start, end, inputs, outputs, and metadata like tokens and cost.

**Build the simplest version yourself first**, a JSONL file, so you understand what a tracing tool stores. Then plug in Langfuse or OpenTelemetry, which give you search and a UI. The skill you are learning is what to record, not which vendor to use.

**Cost caps are safety.** A bug that loops costs real money at 3am. Per request cap, per user daily cap, and a global daily cap. When hit, stop cleanly with a message the user understands.

## Step 1: a tracer

Create `app/trace.py`:

```python
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

TRACE_FILE = Path("traces.jsonl")


class Tracer:
    def __init__(self, trace_id: str | None = None, **meta) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex[:12]
        self.meta = meta
        self.spans: list[dict] = []

    @contextmanager
    def span(self, kind: str, name: str, **inputs):
        sid = uuid.uuid4().hex[:8]
        rec = {"trace_id": self.trace_id, "span_id": sid, "kind": kind, "name": name,
               "inputs": inputs, "start": time.time()}
        try:
            yield rec
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            raise
        finally:
            rec["end"] = time.time()
            rec["ms"] = int((rec["end"] - rec["start"]) * 1000)
            self.spans.append(rec)
            with TRACE_FILE.open("a") as f:
                f.write(json.dumps({**rec, **self.meta}, default=str) + "\n")

    def summary(self) -> dict:
        llm = [s for s in self.spans if s["kind"] == "llm"]
        return {"trace_id": self.trace_id, "spans": len(self.spans), "llm_calls": len(llm),
                "cost": round(sum(s.get("cost", 0) for s in llm), 4),
                "ms": sum(s["ms"] for s in self.spans)}
```

## Step 2: instrument the agent

Give `Agent` an optional `tracer`. Around the `ask` call:

```python
with self.tracer.span("llm", "messages.create", step=step, n_messages=len(messages)) as s:
    msg = ask(...)
    s["output"] = text_of(msg)[:500]
    s["stop_reason"] = msg.stop_reason
    s["tokens"] = {"in": msg.usage.input_tokens, "out": msg.usage.output_tokens,
                   "cache_read": getattr(msg.usage, "cache_read_input_tokens", 0) or 0}
    s["cost"] = cost_of(msg.usage, self.model)   # add cost_of to llm.py from the Spend logic
```

Around each tool call:

```python
with self.tracer.span("tool", b.name, **b.input) as s:
    r = self._run_tool(b)
    s["output"] = str(r["content"])[:500]
    s["error"] = bool(r.get("is_error"))
```

In `app/main.py`, create a `Tracer(user_id=..., session_id=...)` per request, pass it in, and emit `trace_id` in the first event. Return `agent.tracer.summary()` in the final done event.

## Step 3: a query tool

Create `app/trace_query.py`:

```bash
uv run python app/trace_query.py <trace_id>
```

It prints the spans in order, indented, with ms and cost. This is the "under a minute" tool. Then a second mode, `--today`, that prints cost per user for today. That is the dashboard, in text.

## Step 4: cost caps

Create `app/budget.py`:

```python
import json, time
from pathlib import Path

LIMITS = {"per_request": 0.25, "per_user_day": 2.00, "global_day": 10.00}


def spent_today(user_id: str | None = None) -> float:
    day = time.strftime("%Y-%m-%d")
    total = 0.0
    for line in Path("traces.jsonl").read_text().splitlines() if Path("traces.jsonl").exists() else []:
        r = json.loads(line)
        if r["kind"] != "llm" or time.strftime("%Y-%m-%d", time.localtime(r["start"])) != day:
            continue
        if user_id is None or r.get("user_id") == user_id:
            total += r.get("cost", 0)
    return total


class BudgetExceeded(Exception):
    pass


def check_before_request(user_id: str) -> None:
    if spent_today(user_id) > LIMITS["per_user_day"]:
        raise BudgetExceeded("daily limit for this user reached")
    if spent_today() > LIMITS["global_day"]:
        raise BudgetExceeded("service daily limit reached")
```

In the agent loop, after each model call, sum this trace's cost and stop with reason `budget` if it passes `per_request`. In the handler, call `check_before_request` and return a clean event `{"type": "done", "reason": "budget", "message": "..."}` when it raises.

Reading a JSONL file on every request is fine for the course. Note in your log what you would replace it with in production: a counter in Redis or a database table.

## Step 5: Langfuse, optionally

Sign up for the free tier, install the SDK, and follow their current quickstart to send your spans. Do not rewrite your tracer. Add a second sink. Look at your traces in their UI. Decide whether the UI is worth it. Either answer is fine, and either is a good interview story.

## Exercise, without AI

Write the incident note for "agent looped 40 times at 3am and spent 14 USD". What did the trace show? Which cap should have caught it? What did you change?

## Check yourself

1. What is in a span?
2. Why record cost on the span and not in a separate table?
3. Which cap fires first in a runaway loop?
4. What does a tracing vendor give you that your JSONL does not?

## Common mistakes

- Logging full prompts with patient data to a third party without thinking about it. Decide what is safe to send.
- Caps that raise an exception the user sees as a 500.
- Tracing only the model calls and not the tools.

## Done when

- A trace id is returned for every request and the query tool prints it.
- The per request cap stops a deliberately looping prompt.
- Cost per user today is printable.
- Sticky note: "How would I attack my own agent?"
