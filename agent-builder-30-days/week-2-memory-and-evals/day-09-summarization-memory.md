# Day 9: Summarization Memory

**Goal:** instead of dropping old turns, compress them into a running summary that stays in context. This is what "memory" means in most agent products.

## Paper first (20 minutes)

Take yesterday's trimmed history. For the parts you dropped, write a three line summary by hand. Now ask: which facts in those lines would a test need? Which are noise?

## Concepts

**A summary is lossy on purpose.** The skill is deciding what to keep. For a task agent: the goal, decisions made, files changed, facts learned, open questions. For a receptionist: the caller's name, what they wanted, what was promised.

**Structured summaries beat prose.** A fixed set of headings means the summarizer cannot forget a category. It also makes the summary diffable across turns.

**Summarize with a cheaper model.** Summaries are a good place for a smaller model. Measure whether quality drops before deciding.

**Where it lives.** Put the summary in the first user message as a block labelled "Summary of earlier conversation". Never in the system prompt, because that breaks the cache.

## Step 1: the summarizer

Create `memory/summary.py`:

```python
from __future__ import annotations

from pydantic import BaseModel
from llm import client, spend

SUMMARY_MODEL = "claude-haiku-4-5"  # cheap and fast; measure before trusting


class Summary(BaseModel):
    goal: str
    decisions: list[str]
    facts_learned: list[str]
    files_or_records_changed: list[str]
    open_questions: list[str]

    def render(self) -> str:
        def bl(xs): return "\n".join(f"- {x}" for x in xs) or "- none"
        return (
            f"Goal: {self.goal}\n"
            f"Decisions:\n{bl(self.decisions)}\n"
            f"Facts learned:\n{bl(self.facts_learned)}\n"
            f"Changed:\n{bl(self.files_or_records_changed)}\n"
            f"Open questions:\n{bl(self.open_questions)}"
        )


def _to_text(messages: list[dict]) -> str:
    out = []
    for m in messages:
        c = m["content"]
        if isinstance(c, str):
            out.append(f"{m['role']}: {c}")
            continue
        for b in c:
            d = b if isinstance(b, dict) else b.model_dump()
            t = d.get("type")
            if t == "text":
                out.append(f"{m['role']}: {d['text']}")
            elif t == "tool_use":
                out.append(f"{m['role']} called {d['name']}({d['input']})")
            elif t == "tool_result":
                out.append(f"tool result: {str(d.get('content'))[:500]}")
    return "\n".join(out)


def summarize(messages: list[dict], previous: Summary | None = None) -> Summary:
    prior = f"Previous summary:\n{previous.render()}\n\n" if previous else ""
    resp = client.messages.parse(
        model=SUMMARY_MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": (
                "Update the summary of this conversation. Keep every concrete fact, "
                "decision, and changed file. Drop chit chat.\n\n"
                f"{prior}Conversation:\n{_to_text(messages)}"
            ),
        }],
        output_format=Summary,
    )
    spend.add(resp.usage, SUMMARY_MODEL)
    return resp.parsed_output
```

## Step 2: fold it into the history

Create `memory/fold.py`:

```python
from __future__ import annotations

from llm import estimate_tokens
from memory.summary import Summary, summarize
from memory.trim import _exchanges

SUMMARY_TAG = "[Summary of earlier conversation]"


def fold_history(messages: list[dict], budget_tokens: int, keep_recent: int = 4,
                 previous: Summary | None = None) -> tuple[list[dict], Summary | None]:
    """When over budget, summarize everything except the last `keep_recent`
    exchanges and put the summary into the first user message."""
    if estimate_tokens(messages) <= budget_tokens:
        return messages, previous

    groups = _exchanges(messages)
    if len(groups) <= keep_recent + 1:
        return messages, previous

    first_user = groups[0][0]
    old = [m for g in groups[1:-keep_recent] for m in g]
    recent = [m for g in groups[-keep_recent:] for m in g]

    summary = summarize(old, previous)
    original = first_user["content"] if isinstance(first_user["content"], str) else ""
    original = original.split(SUMMARY_TAG)[0].strip()
    new_first = {"role": "user", "content": f"{original}\n\n{SUMMARY_TAG}\n{summary.render()}"}

    out = [new_first] + recent
    while len(out) > 1 and out[1]["role"] != "user":
        out.pop(1)
    return out, summary
```

## Step 3: wire it in

In `agent.py`, add `self.summary = None` in `__init__`, and replace yesterday's trim line with:

```python
            messages[:], self.summary = fold_history(messages, self.budget_tokens, previous=self.summary)
```

Keep `shrink_old_tool_results` before it.

## Step 4: test that facts survive

Create `day09.py`. Have a 12 turn chat where turn 2 states a fact ("the hearing is in Court 7 on 12 September") and turn 12 asks for it, with `budget_tokens` small enough to force folding. Check the answer. Then run it five times. How often does the fact survive? That number goes in your log.

Then switch `SUMMARY_MODEL` to `claude-opus-5` and run five more. Compare survival and cost. Now you have data on whether the cheap model is good enough. That is the kind of sentence that gets you hired.

## Step 5: compare with server side compaction

Read the compaction docs from block 3. Note: it summarizes server side and returns a compaction block you must pass back. Write down the two situations where you would prefer it, and the one where you would prefer your own.

## Exercise, without AI

Write the five headings you would use for the clinic receptionist summary. They are different from the coding agent's.

## Check yourself

1. Why does the summary go in the first user message and not the system prompt?
2. What is the danger of summarizing a summary many times?
3. Why keep the last few exchanges verbatim?
4. How did you measure whether the cheap summarizer was good enough?

## Common mistakes

- Prose summaries that forget categories.
- Re summarizing the whole history every turn instead of the old part only.
- Losing the original task text when replacing the first message.

## Done when

- Facts survive folding at least four out of five runs with your chosen model.
- You have the cheap versus expensive summarizer numbers.
- Notes: "Summarization memory".
- Sticky note: "What should an agent remember about a person across weeks?"
