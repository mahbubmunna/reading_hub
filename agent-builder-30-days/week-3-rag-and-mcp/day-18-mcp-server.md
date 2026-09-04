# Day 18: An MCP Server

**Goal:** expose three capabilities of your project as tools over the Model Context Protocol, so Claude Code, your own loop, and any other MCP client can use them.

## Paper first (20 minutes)

List every action your project can do. Circle the three that an agent would most plausibly need and that are safe to expose. For each: inputs, output, what could go wrong. For the clinic: `search_knowledge`, `check_availability`, `book_appointment`. For the causelist: `search_causelist`, `get_case_status`, `todays_matters`.

## Concepts

**MCP is a standard way for a model host to discover and call tools.** A server declares tools with names, descriptions, and input schemas. A client, like Claude Code or your loop, lists them and calls them. Same idea as your week 1 tool definitions, now over a protocol instead of inside one process.

**Transport.** Stdio for local use, where the client launches the server as a subprocess. Streamable HTTP for remote use. Start with stdio.

**The server is a boundary.** Validation, permissions, and rate limits live here, because you do not control which agent calls you.

**A tool is not an API endpoint.** An endpoint is for programmers. A tool is for a model. Coarser, fewer parameters, descriptions that say when to use it, results that read well as text.

## Step 1: install and scaffold

```bash
uv add "mcp[cli]"
mkdir -p mcp_server
```

Create `mcp_server/server.py`:

```python
"""MCP server for the clinic. Three tools, stdio transport."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from rag.index import Index
from rag.hybrid import retrieve

mcp = FastMCP("clinic")
DB = Path("mcp_server/clinic.db")


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY, doctor TEXT, slot TEXT UNIQUE, patient TEXT, phone TEXT, created TEXT)""")
    return c


_idx: Index | None = None


def _index() -> Index:
    global _idx
    if _idx is None:
        _idx = Index()
    return _idx


@mcp.tool()
def search_knowledge(question: str, k: int = 5) -> str:
    """Search the clinic's knowledge base: services, hours, doctors, prices, policies.

    Use this before answering any factual question about the clinic. Returns the top
    matching passages with their ids so you can cite them. Does not book anything.
    """
    hits = retrieve(_index(), question, k)
    return "\n\n".join(f"[{cid}]\n{_index().get(cid).text}" for cid, _ in hits) or "no results"


@mcp.tool()
def check_availability(doctor: str, day: str) -> str:
    """List free 30 minute slots for a doctor on a given day (YYYY-MM-DD).

    Use this when a patient asks when they can see a doctor, and always before booking.
    Doctors: Rahman, Akter, Chowdhury. Clinic hours 10:00 to 17:00, closed Friday.
    """
    d = datetime.strptime(day, "%Y-%m-%d").date()
    if d.weekday() == 4:
        return f"Clinic is closed on Friday {day}."
    if doctor.title() not in {"Rahman", "Akter", "Chowdhury"}:
        return f"Unknown doctor '{doctor}'. Known: Rahman, Akter, Chowdhury."
    taken = {r[0] for r in _conn().execute("SELECT slot FROM appointments WHERE doctor=?", (doctor.title(),))}
    slots = []
    t = datetime.combine(d, datetime.min.time()).replace(hour=10)
    while t.hour < 17:
        s = t.strftime("%Y-%m-%d %H:%M")
        if s not in taken:
            slots.append(s)
        t += timedelta(minutes=30)
    return "Free slots for Dr " + doctor.title() + ":\n" + "\n".join(slots[:12])


@mcp.tool()
def book_appointment(doctor: str, slot: str, patient_name: str, phone: str) -> str:
    """Book a slot for a patient. slot format 'YYYY-MM-DD HH:MM' exactly as returned by check_availability.

    Only call this after the patient has confirmed the doctor, the time, their name, and phone.
    Returns a confirmation id. Fails if the slot is already taken.
    """
    if not phone.strip() or not patient_name.strip():
        return "Cannot book: name and phone are required."
    c = _conn()
    try:
        cur = c.execute("INSERT INTO appointments(doctor, slot, patient, phone, created) VALUES (?,?,?,?,?)",
                        (doctor.title(), slot, patient_name.strip(), phone.strip(), datetime.now().isoformat()))
        c.commit()
    except sqlite3.IntegrityError:
        return f"Slot {slot} with Dr {doctor.title()} is already taken. Call check_availability again."
    return json.dumps({"confirmation_id": f"CL{cur.lastrowid:05d}", "doctor": doctor.title(),
                       "slot": slot, "patient": patient_name})


if __name__ == "__main__":
    mcp.run()  # stdio
```

The docstring is the tool description. Read each one again: what it does, when to call it, what it needs, what it will not do.

## Step 2: run it and inspect

```bash
uv run mcp dev mcp_server/server.py
```

This opens the MCP Inspector in the browser. List tools. Call `check_availability` with a Friday and a weekday. Call `book_appointment` twice on the same slot. Read the exact text the model would see. If a result would confuse you, it will confuse the model.

## Step 3: idempotency and safety

`book_appointment` is a write. Ask yourself:

- What if the agent calls it twice with the same arguments? The unique slot constraint makes the second call fail cleanly. That is idempotency by design.
- What if the agent invents a phone number? Add validation. A tool should refuse bad input with a clear message.
- What should never be exposed? Cancelling other people's appointments, listing all patients. Leave them out. Absence is the strongest permission control.

## Exercise, without AI

Rewrite the three docstrings from memory. Compare. Which "when to use" sentence did you forget?

## Check yourself

1. What is the difference between a tool and an endpoint?
2. Why is the docstring the most important part of the tool?
3. How did you make booking safe to retry?
4. What did you decide not to expose, and why?

## Common mistakes

- Ten parameters on one tool. Split it or use sensible defaults.
- Returning raw JSON dumps of database rows. Return text a person would understand.
- Doing expensive setup, like loading the index, at import time. Load lazily.

## Done when

- Server runs under the inspector, three tools callable.
- Double booking fails cleanly.
- Notes: "MCP server".
- Sticky note: "What should a tool say when it fails?"
