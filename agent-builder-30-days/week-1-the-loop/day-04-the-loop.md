# Day 4: The Loop

**Goal:** turn yesterday's two calls into a loop. This is the whole thing. Every agent framework on earth is this loop with decorations.

## Paper first (20 minutes)

Write the loop in pseudocode on paper before you look at any code below. Include:

- when it continues
- when it stops normally
- when it stops abnormally
- what it returns

Then compare with the version below. Note every difference.

## Concepts

**The loop:**

```
while True:
    response = model(messages, tools)
    if response has no tool calls: return the text
    run each tool call
    append results
```

**Stop conditions, all four are needed:**

1. `end_turn`: the model is done. Normal.
2. `max_steps`: you set a ceiling. Agents loop forever without one.
3. `max_tokens`: the response was cut. Either raise the limit or stop.
4. Error budget: after N tool errors in a row, stop and report.

**Every step costs the whole history.** Ten steps with a growing history means the tenth call is far bigger than the first. Print usage per step and watch it grow. Week 2 fixes this.

## Step 1: the loop

Create `agent.py`:

```python
"""The agent loop. No framework. Read every line."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from llm import ask, text_of, spend, MODEL


@dataclass
class Tool:
    definition: dict
    fn: Callable[..., str]

    @property
    def name(self) -> str:
        return self.definition["name"]


@dataclass
class AgentResult:
    text: str
    steps: int
    stopped_because: str
    messages: list = field(default_factory=list)


class Agent:
    def __init__(
        self,
        system: str,
        tools: list[Tool],
        max_steps: int = 15,
        max_consecutive_errors: int = 3,
        model: str = MODEL,
        verbose: bool = True,
    ) -> None:
        self.system = system
        self.tools = {t.name: t for t in tools}
        self.definitions = [t.definition for t in tools]
        self.max_steps = max_steps
        self.max_consecutive_errors = max_consecutive_errors
        self.model = model
        self.verbose = verbose

    def _log(self, *a) -> None:
        if self.verbose:
            print(*a)

    def _run_tool(self, block) -> dict:
        tool = self.tools.get(block.name)
        if tool is None:
            return {"type": "tool_result", "tool_use_id": block.id,
                    "content": f"unknown tool {block.name}", "is_error": True}
        try:
            out = tool.fn(**block.input)
            if len(out) > 20_000:
                out = out[:20_000] + "\n...[truncated]"
            return {"type": "tool_result", "tool_use_id": block.id, "content": out}
        except Exception as e:  # tool errors are results, not crashes
            return {"type": "tool_result", "tool_use_id": block.id,
                    "content": f"{type(e).__name__}: {e}", "is_error": True}

    def run(self, task: str, messages: list | None = None) -> AgentResult:
        messages = messages or []
        messages.append({"role": "user", "content": task})
        consecutive_errors = 0

        for step in range(1, self.max_steps + 1):
            self._log(f"\n--- step {step} ---")
            msg = ask(messages, system=self.system, tools=self.definitions, model=self.model)
            messages.append({"role": "assistant", "content": msg.content})

            if msg.stop_reason == "max_tokens":
                return AgentResult(text_of(msg), step, "max_tokens", messages)

            tool_blocks = [b for b in msg.content if b.type == "tool_use"]
            if not tool_blocks:
                return AgentResult(text_of(msg), step, "end_turn", messages)

            for t in text_of(msg).splitlines():
                if t.strip():
                    self._log("  model:", t)

            results = []
            for b in tool_blocks:
                self._log(f"  tool: {b.name}({json.dumps(b.input)[:120]})")
                r = self._run_tool(b)
                self._log(f"  -> {'ERROR ' if r.get('is_error') else ''}{str(r['content'])[:200]}")
                results.append(r)

            if all(r.get("is_error") for r in results):
                consecutive_errors += 1
            else:
                consecutive_errors = 0
            messages.append({"role": "user", "content": results})

            if consecutive_errors >= self.max_consecutive_errors:
                return AgentResult("stopped: too many tool errors", step, "error_budget", messages)

        return AgentResult("stopped: max steps", self.max_steps, "max_steps", messages)
```

## Step 2: run it with one tool

Create `day04.py`:

```python
from agent import Agent, Tool
from tools.calc import calculator, DEFINITION
from llm import spend

agent = Agent(
    system="You are a precise assistant. Use the calculator for every calculation, one at a time.",
    tools=[Tool(DEFINITION, calculator)],
    max_steps=8,
)
res = agent.run(
    "Three cases have fees of 12450, 8900 and 15200 taka. Fee is 15% each plus 300 fixed per case. "
    "Give me each fee and the grand total."
)
print("\nRESULT:", res.text)
print("stopped:", res.stopped_because, "steps:", res.steps)
print(spend.report())
```

Watch the steps. The model may call the calculator three or four times, possibly several in one step. Note how input tokens climb every step.

## Step 3: hit every stop condition on purpose

1. Set `max_steps=2`. See `max_steps`.
2. Make the calculator always raise. See `error_budget` after three steps.
3. In `llm.ask`, temporarily pass `max_tokens=30`. See `max_tokens`.
4. Ask a question that needs no tool. See `end_turn` at step 1.

Write in your log which one you forgot on your paper version.

## Step 4: parallel tool calls

Ask: "Compute 15% of 12450, 15% of 8900, and 15% of 15200." Look at step 1. Did the model put three `tool_use` blocks in one message? If so, your loop handled it, because all results went back in one user message. That is why the loop is written that way.

## Exercise, without AI

Close the file. Rewrite the loop from memory in 25 lines or fewer. Diff it against `agent.py`. Whatever you forgot, that is your note for today.

## Check yourself

1. Why do we append `msg.content` and not `text_of(msg)`?
2. What would happen without `max_steps`?
3. Why count consecutive errors rather than total errors?
4. Why truncate tool output?

## Common mistakes

- Returning after the first tool call instead of looping.
- Building `messages` fresh each step. The history must accumulate.
- Catching exceptions in the loop and printing them instead of sending them to the model.

## Done when

- `day04.py` runs and gives a correct grand total.
- You triggered all four stop conditions and can name them.
- The from memory rewrite exists in your notes folder.
- Notes: "The agent loop" written in your own words.
- Tomorrow's sticky note: "What is the worst thing a shell tool could do?"
