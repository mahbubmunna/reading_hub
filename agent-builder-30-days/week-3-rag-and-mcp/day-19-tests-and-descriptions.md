# Day 19: Tests and Description Design

**Goal:** tests for each tool, and a deliberate pass on descriptions and error messages, because those two things determine whether agents use your tools correctly.

## Paper first (20 minutes)

For each tool write the happy path test and one failure test. Then write the worst error message you have ever seen from an API. Then rewrite it as you would want a model to read it.

## Concepts

**Test the function, then test through the protocol.** Unit tests on the Python functions are fast. One integration test that starts the server and lists tools proves the protocol layer works.

**Error messages are instructions.** "Slot taken. Call check_availability again." tells the model what to do next. "IntegrityError" does not. Every error your tool returns should say what went wrong and what to try.

**Descriptions get tested too.** Not with pytest. With the model. Give it ten user requests and check which tool it picks. Wrong picks mean the description is wrong, not the model.

## Step 1: unit tests

Create `mcp_server/test_server.py`:

```python
import sqlite3
from pathlib import Path

import pytest

from mcp_server import server


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "DB", tmp_path / "t.db")


def test_availability_weekday_has_slots():
    out = server.check_availability("Rahman", "2026-09-07")  # Monday
    assert "10:00" in out and "16:30" in out


def test_availability_friday_closed():
    assert "closed" in server.check_availability("Rahman", "2026-09-11").lower()


def test_unknown_doctor_lists_known():
    out = server.check_availability("Nobody", "2026-09-07")
    assert "Unknown doctor" in out and "Rahman" in out


def test_book_then_slot_disappears():
    server.book_appointment("Rahman", "2026-09-07 10:00", "Test Patient", "017")
    assert "2026-09-07 10:00" not in server.check_availability("Rahman", "2026-09-07")


def test_double_booking_fails_with_instruction():
    server.book_appointment("Rahman", "2026-09-07 10:00", "A", "1")
    out = server.book_appointment("Rahman", "2026-09-07 10:00", "B", "2")
    assert "already taken" in out and "check_availability" in out


def test_booking_requires_phone():
    assert "required" in server.book_appointment("Rahman", "2026-09-07 10:00", "A", "  ")


def test_search_returns_ids(monkeypatch):
    class FakeIdx:
        def get(self, cid):
            class C: text = "Document: Hours\nSection: Friday\n\nClosed on Friday."
            return C()
    monkeypatch.setattr(server, "_index", lambda: FakeIdx())
    monkeypatch.setattr(server, "retrieve", lambda idx, q, k: [("hours::Friday::0", 1.0)])
    out = server.search_knowledge("friday hours")
    assert "[hours::Friday::0]" in out
```

```bash
uv run pytest mcp_server -q
```

## Step 2: protocol integration test

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_lists_three_tools():
    async def go():
        params = StdioServerParameters(command="uv", args=["run", "python", "mcp_server/server.py"])
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = await s.list_tools()
                return sorted(t.name for t in tools.tools)
    assert asyncio.run(go()) == ["book_appointment", "check_availability", "search_knowledge"]
```

## Step 3: the description test, with the model

Create `mcp_server/test_descriptions.py` as a script, not a pytest:

```python
"""Does the model pick the right tool for each request? Run manually; costs a few cents."""
from llm import ask
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CASES = [
    ("Is the clinic open on Friday?", "search_knowledge"),
    ("When can I see Dr Akter next Tuesday?", "check_availability"),
    ("Book me with Dr Rahman on 2026-09-07 at 10:30, I am Karim, 01711", "book_appointment"),
    ("How much is a consultation?", "search_knowledge"),
    ("Can I cancel my appointment?", None),  # no tool fits; should say so
    ("What is the weather?", None),
]


async def tool_defs():
    params = StdioServerParameters(command="uv", args=["run", "python", "mcp_server/server.py"])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return [{"name": t.name, "description": t.description, "input_schema": t.inputSchema}
                    for t in (await s.list_tools()).tools]


defs = asyncio.run(tool_defs())
score = 0
for text, expected in CASES:
    msg = ask([{"role": "user", "content": text}], tools=defs,
              system="You are the clinic receptionist. Use tools when they fit; otherwise answer directly.")
    picked = next((b.name for b in msg.content if b.type == "tool_use"), None)
    ok = picked == expected
    score += ok
    print(f"{'ok ' if ok else 'BAD'} {text[:45]:45s} expected={expected} got={picked}")
print(f"{score}/{len(CASES)}")
```

Run it. Fix descriptions until six of six. Typical fixes: adding "Do not use for cancellations" to booking, or "Use for any factual question, including prices" to search.

## Step 4: error message pass

Read every `return` in `server.py` that is an error. Rewrite each to the shape: what happened, what to do next. Rerun the tests.

## Exercise, without AI

Write the description for a fourth tool you decided not to build, `cancel_appointment`, including why it needs a confirmation step.

## Check yourself

1. Why test descriptions with the model rather than asserting on strings?
2. What are the two parts of a good tool error?
3. Why patch the database path in tests?
4. Which description did you change, and what request was it failing?

## Common mistakes

- Tests that hit the real database.
- Description tests that only cover happy requests. The "no tool fits" cases matter most.
- Errors that leak stack traces to the model.

## Done when

- All tests pass.
- Description test at six of six.
- Errors rewritten.
- Sticky note: "What is the difference between a tool and an API?"
