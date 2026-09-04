# Day 8: The Context Budget

**Goal:** the agent knows how many tokens it is about to send and never exceeds a budget. Trimming is the simplest memory strategy, and it is enough for many real apps.

## Paper first (20 minutes)

Take a ten turn conversation with tool calls. Which parts does the model need for turn eleven? Cross out what it does not. Notice what you crossed out first. Usually old tool results.

## Concepts

**Context is a budget, not a bucket.** The window is large, but every token costs money, adds latency, and dilutes attention. Well built agents send far less than the window allows.

**Count before you send.** The API has a `count_tokens` endpoint. Use it for the real number. For fast local estimates, four characters per token is close enough to make decisions.

**Trim the middle, keep the ends.** The system prompt and the most recent turns matter most. Old tool results matter least. Trimming must never split a tool use from its tool result, or the API rejects the request.

**Server side options exist.** Anthropic offers context editing, which clears old tool results, and compaction, which summarizes server side. Learn the manual version first so you understand what they are doing.

## Step 1: counting

Add to `llm.py`:

```python
def count_tokens(messages: list[dict], system=None, tools=None, model: str = MODEL) -> int:
    kwargs = dict(model=model, messages=messages)
    if system is not None:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
    return client.messages.count_tokens(**kwargs).input_tokens


def estimate_tokens(messages: list[dict]) -> int:
    """Fast local estimate. About 4 chars per token."""
    import json
    return len(json.dumps(messages, default=str)) // 4
```

Test both on your week 1 messages and compare. Write down how far off the estimate is.

## Step 2: a trimmer that respects tool pairs

Create `memory/__init__.py` (empty) and `memory/trim.py`:

```python
"""Trim conversation history to fit a token budget.

Keeps the first user message and the most recent turns. Removes whole
exchanges from the middle. Never splits a tool_use from its tool_result."""
from __future__ import annotations

from llm import estimate_tokens


def _is_tool_result_msg(m: dict) -> bool:
    c = m.get("content")
    return isinstance(c, list) and any(
        (getattr(b, "type", None) or b.get("type")) == "tool_result" for b in c
    )


def _exchanges(messages: list[dict]) -> list[list[dict]]:
    """Group messages into exchanges: an assistant message plus the tool_result
    user message that follows it stay together."""
    groups: list[list[dict]] = []
    i = 0
    while i < len(messages):
        m = messages[i]
        if m["role"] == "assistant" and i + 1 < len(messages) and _is_tool_result_msg(messages[i + 1]):
            groups.append([m, messages[i + 1]])
            i += 2
        else:
            groups.append([m])
            i += 1
    return groups


def trim_to_budget(messages: list[dict], budget_tokens: int, keep_first: int = 1) -> list[dict]:
    if estimate_tokens(messages) <= budget_tokens:
        return messages
    groups = _exchanges(messages)
    head = groups[:keep_first]
    tail = groups[keep_first:]
    # drop oldest exchanges from the tail until we fit
    while tail and estimate_tokens([m for g in head + tail for m in g]) > budget_tokens:
        tail.pop(0)
    out = [m for g in head + tail for m in g]
    # The message after the head must be a user message for the API
    while len(out) > keep_first and out[keep_first]["role"] != "user":
        out.pop(keep_first)
    return out
```

## Step 3: tool result shrinking

Old tool results are the fattest thing in history. Before trimming whole exchanges, shrink them. Add to `memory/trim.py`:

```python
def shrink_old_tool_results(messages: list[dict], keep_last: int = 2, max_chars: int = 300) -> list[dict]:
    """Replace old tool_result contents with a short stub. Keeps the last N intact."""
    idx = [i for i, m in enumerate(messages) if _is_tool_result_msg(m)]
    for i in idx[:-keep_last] if keep_last else idx:
        new_blocks = []
        for b in messages[i]["content"]:
            d = b if isinstance(b, dict) else b.model_dump()
            if d.get("type") == "tool_result" and isinstance(d.get("content"), str) and len(d["content"]) > max_chars:
                d = {**d, "content": d["content"][:max_chars] + " ...[older result shortened]"}
            new_blocks.append(d)
        messages[i] = {"role": "user", "content": new_blocks}
    return messages
```

## Step 4: wire into the loop

In `agent.py`, add a `budget_tokens: int = 30_000` argument and, at the top of each step before calling `ask`:

```python
from memory.trim import trim_to_budget, shrink_old_tool_results
...
            messages[:] = shrink_old_tool_results(messages)
            messages[:] = trim_to_budget(messages, self.budget_tokens)
```

Use `messages[:] =` so the caller's list is updated in place.

Run the coding agent from day 6 with `budget_tokens=8_000` and watch the usage lines. Input tokens should plateau instead of climbing. Then run with `budget_tokens=2_000` and watch it lose the plot. Write down at what budget it stops being able to fix the bug. That number is a real finding.

## Step 5: compare with server side context editing

Try the built in version once, so you know it exists:

```python
resp = client.beta.messages.create(
    model=MODEL, max_tokens=4096,
    betas=["context-management-2025-06-27"],
    context_management={"edits": [{"type": "clear_tool_uses_20250919"}]},
    tools=tools, messages=messages,
)
```

Note in your log what it does that yours does not, and the reverse.

## Exercise, without AI

Draw a 12 message history with three tool calls. Mark what your trimmer keeps at a budget that fits eight messages. Check that no tool use is orphaned.

## Check yourself

1. Why must a tool use and its result stay together?
2. Why keep the first user message?
3. Why shrink before trimming?
4. What breaks first when the budget is too small?

## Common mistakes

- Trimming by message count instead of tokens.
- Cutting the history to start with an assistant message.
- Estimating with `len(text)` and forgetting JSON overhead.

## Done when

- Usage lines plateau under a budget during a coding agent run.
- You know the budget at which the coding agent starts failing.
- Notes: "Context budget".
- Sticky note: "What gets lost in a summary, and does it matter?"
