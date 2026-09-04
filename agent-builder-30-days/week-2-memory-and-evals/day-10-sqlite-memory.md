# Day 10: Long Term Memory in SQLite

**Goal:** memory that survives the process ending. A user talks to the clinic receptionist on Monday and again on Friday, and the agent remembers.

## Paper first (20 minutes)

Two tables. What columns? Who is the owner of a memory: a user, a session, or the whole system? What should never be stored?

## Concepts

**Three scopes.** Session memory: this conversation. User memory: facts about this person across sessions. Global memory: facts about the world the agent learned, shared by everyone. Keep them in separate tables, because deletion rules differ.

**Memory is written by the agent, on purpose.** Give the agent a `remember` tool and a `recall` tool. Do not silently store everything. Explicit memory is auditable and it is what users expect.

**Recall goes in context, not in the system prompt.** Same cache reason as yesterday.

**SQLite is enough.** Vector stores come on day 15. For facts about a person, a text search over a few hundred rows is faster to build and easier to debug.

## Step 1: the store

Create `memory/store.py`:

```python
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str = "memory.db") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                scope TEXT NOT NULL,          -- 'user' | 'session' | 'global'
                owner TEXT NOT NULL,          -- user_id, session_id, or '*'
                content TEXT NOT NULL,
                created_at REAL NOT NULL
            )""")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                messages TEXT NOT NULL,       -- json
                summary TEXT,
                updated_at REAL NOT NULL
            )""")
        self.conn.commit()

    # --- explicit memories
    def remember(self, scope: str, owner: str, content: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO memories(scope, owner, content, created_at) VALUES (?,?,?,?)",
            (scope, owner, content, time.time()))
        self.conn.commit()
        return cur.lastrowid

    def recall(self, user_id: str, query: str | None = None, limit: int = 10) -> list[str]:
        sql = "SELECT content FROM memories WHERE (scope='user' AND owner=?) OR scope='global'"
        args: list = [user_id]
        if query:
            sql += " AND content LIKE ?"
            args.append(f"%{query}%")
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        return [r[0] for r in self.conn.execute(sql, args)]

    def forget(self, user_id: str) -> int:
        cur = self.conn.execute("DELETE FROM memories WHERE scope='user' AND owner=?", (user_id,))
        self.conn.commit()
        return cur.rowcount

    # --- session persistence
    def save_session(self, session_id: str, user_id: str, messages: list, summary: str | None) -> None:
        def default(o):
            return o.model_dump() if hasattr(o, "model_dump") else str(o)
        self.conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?)",
            (session_id, user_id, json.dumps(messages, default=default), summary, time.time()))
        self.conn.commit()

    def load_session(self, session_id: str) -> tuple[list, str | None] | None:
        row = self.conn.execute(
            "SELECT messages, summary FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if not row:
            return None
        return json.loads(row[0]), row[1]
```

## Step 2: memory tools

Create `tools/memory_tools.py`:

```python
from memory.store import MemoryStore


def make_memory_tools(store: MemoryStore, user_id: str):
    def remember(fact: str) -> str:
        store.remember("user", user_id, fact)
        return f"remembered: {fact}"

    def recall(query: str) -> str:
        found = store.recall(user_id, query or None)
        return "\n".join(f"- {f}" for f in found) or "nothing remembered"

    REMEMBER = {
        "name": "remember",
        "description": (
            "Store one durable fact about this user for future conversations. Use it when the user "
            "states a preference, a name, a recurring need, or a decision. One fact per call. "
            "Never store passwords, card numbers, or health details the user did not ask you to keep."
        ),
        "input_schema": {"type": "object", "properties": {"fact": {"type": "string"}},
                         "required": ["fact"], "additionalProperties": False},
        "strict": True,
    }
    RECALL = {
        "name": "recall",
        "description": (
            "Search facts stored about this user in past conversations. Call it at the start of a "
            "conversation and whenever the user refers to something from before. "
            "Pass an empty string to list recent facts."
        ),
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                         "required": ["query"], "additionalProperties": False},
        "strict": True,
    }
    return [(REMEMBER, remember), (RECALL, recall)]
```

## Step 3: session resume in the agent

Add to `Agent.run` an optional `messages` you already have. Now write `day10.py`:

```python
import sys
from agent import Agent, Tool
from memory.store import MemoryStore
from tools.memory_tools import make_memory_tools
from llm import spend

store = MemoryStore("memory.db")
user_id, session_id = "mahbub", sys.argv[1] if len(sys.argv) > 1 else "s1"

agent = Agent(
    system="You are a clinic receptionist. Be brief. Use recall at the start of every conversation.",
    tools=[Tool(d, f) for d, f in make_memory_tools(store, user_id)],
    max_steps=6, budget_tokens=12_000,
)

saved = store.load_session(session_id)
messages = saved[0] if saved else []

while True:
    line = input("you> ").strip()
    if line in {"q", "quit"}:
        break
    res = agent.run(line, messages=messages)
    print("agent>", res.text)
    store.save_session(session_id, user_id, messages,
                       agent.summary.render() if agent.summary else None)
print(spend.report())
```

Run it. Tell it "My son is nine months old and we usually come on Thursdays." Quit. Run again with a new session id. Ask "When do we usually come?" It should recall.

## Step 4: the deletion path

Add a `forget` tool or a CLI flag. Run it. Confirm recall returns nothing. In a real product, this is a legal requirement and an interview question.

## Step 5: what the agent chose to remember

Print the memories table after a few conversations. Did it store useful facts, or junk? Tighten the description until it stores what you would store.

## Exercise, without AI

Write the memory policy for the clinic in five lines: what is stored, for how long, who can delete it, what is never stored.

## Check yourself

1. Why explicit memory tools rather than storing everything?
2. Why separate scopes into separate rows or tables?
3. What happens to old session messages when the summary folds them? Is the original transcript lost?
4. Where does recalled memory enter the context?

## Common mistakes

- Storing the whole conversation as "memory". That is a transcript, not memory.
- Global scope by default. Leaks one user's facts to another.
- No deletion path.

## Done when

- A fact survives a process restart and a new session.
- `forget` works.
- You reviewed what the agent stored and tightened the description.
- Notes: memory scopes, in your own words.
- Sticky note: "What does correct mean for my agent?"
