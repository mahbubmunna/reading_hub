# Day 1: First Call, Streaming, Cost

**Goal:** a thin wrapper, `llm.py`, that every later day builds on. It streams, it prints token usage and cost, and it handles errors properly.

**Time:** Block 1 and Block 2. Block 3 is reading item 1.

## Paper first (20 minutes)

Before typing, draw on paper:

1. A box labelled "my code", a box labelled "Anthropic API". Draw the request going over. What is in it? Write the fields you think are needed.
2. What comes back? Write the fields you expect.
3. What could go wrong? List five things.

Keep the page. Compare with reality at the end of the day.

## Concepts

**The API is stateless.** Every request carries the full conversation. There is no session on the server. This is the single fact that makes everything else make sense. Memory, context budgets, caching, all exist because of this.

**A message is a list of content blocks.** Not a string. A response can contain text blocks, thinking blocks, and tool use blocks in one message. Always check `block.type`.

**Tokens are money and time.** Input tokens are what you send, output tokens are what comes back. Output is roughly five times the price of input. Printing usage on every call is not optional this month. You will make decisions based on it.

**Streaming** means the response arrives as events while it is being generated. Use it for anything longer than a sentence. It also avoids timeouts on long outputs.

## Step 1: the wrapper

Create `llm.py`:

```python
"""Thin wrapper around the Anthropic client.
Every call prints usage and cost so you always know what you are spending."""
from __future__ import annotations

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-5"

# USD per million tokens. Update if pricing changes.
PRICES = {
    "claude-opus-5": {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25},
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-haiku-4-5": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
}

client = anthropic.Anthropic()


class Spend:
    """Accumulates usage across calls."""

    def __init__(self) -> None:
        self.input = 0
        self.output = 0
        self.cache_read = 0
        self.cache_write = 0
        self.calls = 0

    def add(self, usage, model: str) -> float:
        self.calls += 1
        self.input += usage.input_tokens
        self.output += usage.output_tokens
        cr = getattr(usage, "cache_read_input_tokens", 0) or 0
        cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
        self.cache_read += cr
        self.cache_write += cw
        p = PRICES[model]
        cost = (
            usage.input_tokens * p["in"]
            + usage.output_tokens * p["out"]
            + cr * p["cache_read"]
            + cw * p["cache_write"]
        ) / 1_000_000
        print(
            f"[usage] in={usage.input_tokens} out={usage.output_tokens} "
            f"cache_read={cr} cache_write={cw} cost=${cost:.4f}"
        )
        return cost

    def total_cost(self, model: str) -> float:
        p = PRICES[model]
        return (
            self.input * p["in"]
            + self.output * p["out"]
            + self.cache_read * p["cache_read"]
            + self.cache_write * p["cache_write"]
        ) / 1_000_000

    def report(self, model: str = MODEL) -> str:
        return (
            f"calls={self.calls} in={self.input} out={self.output} "
            f"cache_read={self.cache_read} total=${self.total_cost(model):.4f}"
        )


spend = Spend()


def ask(
    messages: list[dict],
    system: str | list[dict] | None = None,
    tools: list[dict] | None = None,
    max_tokens: int = 4096,
    model: str = MODEL,
    stream_text: bool = False,
):
    """One call to the Messages API. Returns the full Message object.

    stream_text=True prints text as it arrives. Either way the full message is
    returned so callers can inspect content blocks and stop_reason.
    """
    kwargs = dict(model=model, max_tokens=max_tokens, messages=messages)
    if system is not None:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools

    try:
        with client.messages.stream(**kwargs) as stream:
            if stream_text:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                print()
            message = stream.get_final_message()
    except anthropic.RateLimitError as e:
        retry_after = e.response.headers.get("retry-after", "?")
        raise RuntimeError(f"rate limited, retry after {retry_after}s") from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"api error {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError("network error") from e

    spend.add(message.usage, model)
    return message


def text_of(message) -> str:
    """Concatenate all text blocks of a message."""
    return "".join(b.text for b in message.content if b.type == "text")
```

## Step 2: use it

Create `day01.py`:

```python
from llm import ask, text_of, spend

msg = ask(
    [{"role": "user", "content": "Explain in three sentences what an API is."}],
    system="You are a patient teacher. Plain words.",
    stream_text=True,
)
print("stop_reason:", msg.stop_reason)
print("blocks:", [b.type for b in msg.content])
print(spend.report())
```

```bash
uv run python day01.py
```

You should see text streaming, then a usage line, the stop reason `end_turn`, and a list like `['text']`.

## Step 3: a multi turn conversation

Add to `day01.py`:

```python
history = []

def chat(user_text: str) -> str:
    history.append({"role": "user", "content": user_text})
    msg = ask(history, system="Answer briefly.")
    reply = text_of(msg)
    history.append({"role": "assistant", "content": reply})
    return reply

print(chat("My name is Mahbub and I build agents."))
print(chat("What do I build?"))
print(spend.report())
```

Look at the second usage line. Input tokens went up, because you sent the whole history again. That is statelessness. Say it out loud.

## Step 4: break it on purpose

Do each of these and watch what happens. Write the error text in your log.

1. Set `max_tokens=20`. Look at `stop_reason`. It is `max_tokens`. The answer is cut. Your loop next week must handle this.
2. Put the assistant message first in `history`. Read the error.
3. Set `model="claude-opus-9"`. Read the error.
4. Unset the API key. Read the error.

## Production note: refusal fallbacks

On Claude Opus 5 a request can come back with `stop_reason == "refusal"` from a safety classifier. For a production app you would opt into server side fallbacks so such a request is retried on another model automatically. It is a beta and looks like this:

```python
message = client.beta.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    betas=["server-side-fallback-2026-07-01"],
    fallbacks="default",
    messages=messages,
)
```

We keep `llm.py` on the plain endpoint for clarity this month. Add this in week 4 when you ship. For now, always check `stop_reason` before you read `content`.

## Exercise, without AI

Write from memory, on paper, the JSON shape of a request and a response. Then check against the SDK docs. Fix your drawing.

## Check yourself

1. Why does the second turn cost more input tokens than the first?
2. What is the difference between `stop_reason` of `end_turn` and `max_tokens`?
3. Where does the system prompt go, and why is it not a message?
4. What is a content block?

If you cannot answer all four out loud, reread the concepts section.

## Common mistakes

- Reading `msg.content[0].text` without checking type. The first block can be a thinking block.
- Forgetting to append the assistant reply to history. The model then "forgets" its own answer.
- Hardcoding the API key in the file.

## Done when

- `day01.py` runs, streams, prints usage and a total.
- You wrote the four "break it" errors in your log.
- Your paper drawing is corrected.
- Notes: five lines in `notes/daily-log.md`.
- Tomorrow's sticky note: "Why would the same prompt cost less the second time?"
