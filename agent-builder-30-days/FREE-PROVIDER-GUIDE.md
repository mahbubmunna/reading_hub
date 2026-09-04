# Running This Course For Free

You do not need the Anthropic API. Every lesson in this course works against free providers, because the concepts are about agents, not about one vendor. This file replaces the Anthropic parts of `02-setup.md`.

## First, what your Claude Pro subscription does and does not cover

**Covers:** Claude Code as your coding assistant. The terminal tool you are using right now, for writing and debugging the course code, is included in Pro. Use it freely within your Pro limits.

**Does not cover:** programmatic API access for the agent you are building. Your agent calling a model in a loop is API usage, billed separately. That is what we are replacing with free providers.

So: Claude Code stays as your pair programmer. Something else powers your agent.

## Your hardware

You have two machines, and they have different jobs.

| | MacBook Air | Linux box |
|---|---|---|
| Chip | Apple M1 | RTX 5060 Ti |
| Memory | 8 GB unified | VRAM: check below |
| Free disk | about 16 GB | check |
| Job | Writing code, running the service, the browser | Running the models |

**Check the GPU first.** On the Linux box:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
ollama --version
```

The 5060 Ti ships in 8 GB and 16 GB variants, and what you can run differs a lot between them.

| VRAM | What runs well | Your daily model |
|---|---|---|
| 16 GB | 14B at 4-bit (about 9 GB), `gpt-oss:20b` (about 13 GB), 8B at 8-bit | `qwen3:14b` or `gpt-oss:20b` |
| 8 GB | 8B at 4-bit (about 5 GB), 4B comfortably | `qwen3:8b` |

Either way this is a real local setup, and it changes the plan. **Local models become your default engine, not your fallback.** Unlimited calls, no rate limits, no quota anxiety, and week 2 evals can run hundreds of times without you thinking about it. That is worth more for learning than a slightly smarter hosted model.

Two notes specific to your card. The 5060 Ti is Blackwell, so it needs a recent driver and a recent Ollama build. If `ollama run` falls back to CPU, that is almost always the cause: update the driver and Ollama before debugging anything else. And 16 GB VRAM does not mean 16 GB of model. Leave one to two GB of headroom for context. A long agent conversation grows the KV cache, and running out mid task looks like a mysterious slowdown as it spills to system RAM.

**The MacBook Air stays your workstation.** 8 GB is too small to run useful models locally, but it is fine for writing code, running FastAPI, the RAG index, and the browser. Point it at the Linux box over your network, which is the next section.

## Serving the GPU box to the MacBook

Run models on the Linux machine, write code on the Air. On the Linux box:

```bash
# listen on the LAN, not just localhost
sudo systemctl edit ollama
# add:
#   [Service]
#   Environment="OLLAMA_HOST=0.0.0.0:11434"
#   Environment="OLLAMA_KEEP_ALIVE=30m"
sudo systemctl restart ollama
ip addr show | grep "inet "        # note the 192.168.x.x address
```

From the Mac:

```bash
curl http://192.168.1.50:11434/api/tags     # your Linux box IP
```

Then in `.env` on the Mac:

```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://192.168.1.50:11434/v1
```

Only do this on your home network. Ollama has no authentication, so anyone on the network can use your GPU. Never expose port 11434 to the internet.

`OLLAMA_KEEP_ALIVE=30m` matters more than it looks. By default Ollama unloads the model after five minutes, and reloading a 14B model takes several seconds. During a 30 task eval run with pauses, that reload cost dominates. Set it once and forget it.

## The provider table

Local first, hosted as backup. All of these speak the OpenAI Chat Completions format, so one code path handles every one of them. Hosted free-tier limits change often, so check each site rather than trusting numbers written here.

| Provider | Cost | Tool calling | Role in your setup |
|---|---|---|---|
| **Ollama on your Linux box** | Free, unlimited, offline | Yes, on the models below | **Your default.** No quota, no rate limit, no network round trip |
| **Google AI Studio (Gemini)** | Free tier, no card | Yes | The strong model when local is not enough. Also your eval judge. aistudio.google.com |
| **Groq** | Free tier, no card | Yes | Very fast hosted, good when you want speed and your GPU is busy. console.groq.com |
| **Cerebras** | Free tier | Yes | Backup when Groq rate limits. cloud.cerebras.ai |
| **OpenRouter** | Free models exist | Varies | One key, many models. Useful for the model comparison in week 2 |

Get the Gemini key today. It takes five minutes, needs no card, and you need a second independent model for the eval judge in week 2. Groq is worth ten more minutes as a backup. Everything else is optional.

### Models to pull

On the Linux box, for 16 GB VRAM:

```bash
ollama pull qwen3:14b            # about 9 GB. Strong tool calling. Your daily driver
ollama pull gpt-oss:20b          # about 13 GB. Better reasoning, slower. Try both
ollama pull qwen2.5-coder:14b    # about 9 GB. For the week 1 coding agent
ollama pull llama3.2:3b          # about 2 GB. The deliberately weak one, see below
ollama pull nomic-embed-text     # about 275 MB. Optional GPU embeddings for week 3
```

For 8 GB VRAM, swap the first three for `qwen3:8b` and `qwen2.5-coder:7b`.

Benchmark them on your own machine before choosing:

```bash
for m in qwen3:14b gpt-oss:20b; do
  echo "== $m"
  ollama run $m --verbose "Write a Python function that merges two sorted lists." 2>&1 | tail -5
done
```

Look at eval rate in tokens per second. Under about 15 tokens per second, a 15 step agent run becomes painful. Pick the largest model that stays above that.

## Which provider for which job

| Job | Use | Why |
|---|---|---|
| The agent itself, daily building | Ollama, `qwen3:14b` | Unlimited iterations. This is the whole advantage |
| Week 1 coding agent | Ollama, `qwen2.5-coder:14b` | Code tuned, and the task is well defined |
| Week 2 eval runs | Ollama | Hundreds of calls per run. Unlimited matters more than smart |
| Week 2 LLM judge | **Gemini** | The judge must be independent of the agent. Never judge with the model under test |
| Week 2 summarizer | Ollama, a small model | Cheap job, cheap model. Same lesson as the paid version |
| Week 3 embeddings and reranking | Local sentence-transformers, on the GPU | Free, fast, already in the plan |
| Week 4 live demo | Gemini or Groq | A recruiter clicking your URL should not depend on your home GPU being on |
| The "how much does capability buy" experiment | Ollama 3B vs 14B vs Gemini | Three points on a curve, measured on your own tasks |

That last row is worth noticing. On a paid setup you would compare two models once and stop, because each comparison costs money. With a local GPU you can compare freely, which means you can actually learn what model capability buys on your specific tasks. Most people applying for these jobs have never measured that.

## Install

```bash
cd ~/agent-course
uv add openai pydantic rich python-dotenv pytest "fastapi[standard]" uvicorn
```

One package, `openai`, talks to every provider above. You are not using OpenAI. You are using their request format, which the whole industry adopted.

`.env`:

```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://192.168.1.50:11434     # your Linux box; omit if running on it
GEMINI_API_KEY=...                        # needed for the eval judge in week 2
GROQ_API_KEY=...                          # backup
# optional
CEREBRAS_API_KEY=...
OPENROUTER_API_KEY=...
```

## The provider-agnostic client

This replaces `llm.py` from day 1. Everything else in the course, the loop, tools, memory, evals, RAG, MCP, FastAPI, sits on top of this and never changes when you swap providers.

```python
"""Provider-agnostic LLM client. One interface, many free backends.

Every provider here speaks the OpenAI Chat Completions format, so swapping
providers is a base_url and a model name. Nothing downstream changes."""
from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from openai import OpenAI, APIStatusError, APIConnectionError, RateLimitError

load_dotenv()

PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model": "gemini-2.5-flash",
        "big": "gemini-2.5-pro",
        "small": "gemini-2.5-flash-lite",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
        "big": "llama-3.3-70b-versatile",
        "small": "llama-3.1-8b-instant",
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "key_env": "CEREBRAS_API_KEY",
        "model": "llama-3.3-70b",
        "big": "llama-3.3-70b",
        "small": "llama3.1-8b",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "big": "meta-llama/llama-3.3-70b-instruct:free",
        "small": "meta-llama/llama-3.2-3b-instruct:free",
    },
    "ollama": {
        # OLLAMA_HOST lets the MacBook point at the Linux box over the LAN
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434") .rstrip("/") + "/v1",
        "key_env": None,
        "model": "qwen3:14b",
        "big": "gpt-oss:20b",
        "small": "llama3.2:3b",
    },
}

PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
_cfg = PROVIDERS[PROVIDER]
MODEL = os.getenv("LLM_MODEL", _cfg["model"])

client = OpenAI(
    base_url=_cfg["base_url"],
    api_key=os.getenv(_cfg["key_env"], "x") if _cfg["key_env"] else "ollama",
)


def client_for(provider: str) -> tuple[OpenAI, dict]:
    """A second client, for the judge or the summarizer. Keeps them independent."""
    c = PROVIDERS[provider]
    return OpenAI(base_url=c["base_url"],
                  api_key=os.getenv(c["key_env"], "x") if c["key_env"] else "ollama"), c


# Shadow pricing: these calls are free, but we still track what they WOULD cost
# on a paid frontier model. Cost discipline is the skill; the bill is not the point.
SHADOW_PRICE = {"in": 5.00, "out": 25.00}  # USD per million tokens


class Spend:
    def __init__(self) -> None:
        self.input = self.output = self.calls = 0

    def add(self, usage) -> float:
        if usage is None:
            return 0.0
        self.calls += 1
        pt = getattr(usage, "prompt_tokens", 0) or 0
        ct = getattr(usage, "completion_tokens", 0) or 0
        self.input += pt
        self.output += ct
        shadow = (pt * SHADOW_PRICE["in"] + ct * SHADOW_PRICE["out"]) / 1_000_000
        print(f"[usage] in={pt} out={ct} shadow_cost=${shadow:.4f} (actual $0.00)")
        return shadow

    def total_shadow(self) -> float:
        return (self.input * SHADOW_PRICE["in"] + self.output * SHADOW_PRICE["out"]) / 1_000_000

    def report(self) -> str:
        return (f"provider={PROVIDER} model={MODEL} calls={self.calls} "
                f"in={self.input} out={self.output} shadow=${self.total_shadow():.4f}")


spend = Spend()


def ask(
    messages: list[dict],
    system: str | None = None,
    tools: list[dict] | None = None,
    max_tokens: int = 4096,
    model: str | None = None,
    stream_text: bool = False,
    response_format: dict | None = None,
    temperature: float = 0.0,
):
    """One chat completion. Returns the message object from choices[0].

    `messages` uses the OpenAI shape:
      {"role": "user"|"assistant"|"system"|"tool", "content": str, ...}
    Assistant tool calls live in message.tool_calls.
    Tool results are {"role": "tool", "tool_call_id": ..., "content": ...}
    """
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    kwargs: dict = dict(model=model or MODEL, messages=msgs, max_tokens=max_tokens,
                        temperature=temperature)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if response_format:
        kwargs["response_format"] = response_format

    try:
        if stream_text:
            kwargs["stream"] = True
            kwargs["stream_options"] = {"include_usage": True}
            content, tool_calls, usage = "", {}, None
            for chunk in client.chat.completions.create(**kwargs):
                if chunk.usage:
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                d = chunk.choices[0].delta
                if d.content:
                    content += d.content
                    print(d.content, end="", flush=True)
                for tc in (d.tool_calls or []):
                    slot = tool_calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function and tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        slot["args"] += tc.function.arguments
            print()
            spend.add(usage)
            return _fake_message(content, tool_calls)

        resp = client.chat.completions.create(**kwargs)
    except RateLimitError as e:
        raise RuntimeError(f"rate limited on {PROVIDER}: switch provider or wait") from e
    except APIStatusError as e:
        raise RuntimeError(f"api error {e.status_code} on {PROVIDER}: {e.message}") from e
    except APIConnectionError as e:
        raise RuntimeError(f"network error to {PROVIDER}") from e

    spend.add(resp.usage)
    return resp.choices[0].message


class _FakeCall:
    def __init__(self, id, name, args):
        self.id = id
        self.function = type("F", (), {"name": name, "arguments": args})()


def _fake_message(content: str, tool_calls: dict):
    """Rebuild a message object from streamed deltas so callers see one shape."""
    calls = [_FakeCall(v["id"], v["name"], v["args"]) for v in tool_calls.values()] or None
    return type("M", (), {"content": content or "", "tool_calls": calls, "role": "assistant"})()


def text_of(message) -> str:
    return message.content or ""


def estimate_tokens(messages: list[dict]) -> int:
    """No count_tokens endpoint on most free providers. 4 chars per token."""
    return len(json.dumps(messages, default=str)) // 4
```

Test it:

```bash
LLM_PROVIDER=ollama uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}])))
print(spend.report())"

LLM_PROVIDER=gemini uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}])))
print(spend.report())"
```

Both should print "Ready." That is the whole point: one file, two providers, no code change. If the Ollama one hangs, the model is loading for the first time. If it is slow every time, check `nvidia-smi` while it runs. If the GPU is idle, Ollama is on the CPU and your driver or Ollama version is too old for Blackwell.

## What changes in the course, day by day

Most days change nothing. Here is every difference.

### Day 1: first call

Use the client above instead of the Anthropic one. Two conceptual differences to write in your notes:

- **Content is a string, not a list of blocks.** The OpenAI format puts text in `message.content` and tool calls in `message.tool_calls`, as separate fields. The Anthropic format puts both in one `content` list of typed blocks. Neither is wrong. Knowing both is worth an interview point.
- **The system prompt is a message** with `role: "system"`, first in the list. In the Anthropic API it is a separate top level field.

The "break it on purpose" exercises still work. Statelessness, `finish_reason`, and history growth are identical.

### Day 2: structured output and caching

**Structured output** works. Replace `client.messages.parse` with a JSON schema response format:

```python
from pydantic import BaseModel

class CaseEntry(BaseModel):
    case_number: str
    court: str
    urgent: bool

msg = ask(
    [{"role": "user", "content": f"Extract the case entry:\n{raw}"}],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "case_entry", "strict": True,
                        "schema": CaseEntry.model_json_schema()},
    },
)
entry = CaseEntry.model_validate_json(msg.content)
```

Some free models ignore `strict` and return slightly off JSON. That is a lesson, not a defeat: wrap the parse in a try, and on failure send the validation error back to the model and ask it to fix its own output. Write that retry. Real systems have it.

**Prompt caching** is mostly not available on free tiers. Do this instead:

1. Read the caching section as theory. You still need to answer caching questions in interviews.
2. Do the practical half: build the long stable system prompt, measure `prompt_tokens` across three questions, and confirm the number is large and repeated every time. That repeated number is exactly what caching would have eliminated.
3. Write the paragraph: "on a provider with prefix caching, calls 2 and 3 would read N tokens from cache at roughly a tenth of the price, and this timestamp at the top of my prompt would have destroyed that."

You learn the design rule, which is prefix stability, without paying for it. Keep volatile content at the end of your prompts anyway. It costs nothing and it is the right habit.

### Day 3: the first tool

The concept is identical. The wire format differs, and you should write both shapes in your notes.

Tool definition:

```python
DEFINITION = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate an arithmetic expression exactly. Use this whenever the user asks "
            "for a calculation, a total, or a percentage. Do not do arithmetic yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string",
                "description": "A single arithmetic expression, e.g. (1200*0.15)+40"}},
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
}
```

The round trip:

```python
import json
from llm import ask, text_of
from tools.calc import calculator, DEFINITION

messages = [{"role": "user", "content": "A court fee is 15% of 12450 plus 300. Total?"}]
msg = ask(messages, tools=[DEFINITION], system="Use the calculator for all arithmetic.")

# the assistant message goes back verbatim, including its tool_calls
messages.append({"role": "assistant", "content": msg.content or "",
                 "tool_calls": [{"id": c.id, "type": "function",
                                 "function": {"name": c.function.name,
                                              "arguments": c.function.arguments}}
                                for c in (msg.tool_calls or [])]})

for call in (msg.tool_calls or []):
    args = json.loads(call.function.arguments)   # always parse, never string match
    try:
        out = calculator(**args)
    except Exception as e:
        out = f"error: {e}"
    # ONE tool message PER call, not one message with all results
    messages.append({"role": "tool", "tool_call_id": call.id, "content": str(out)})

msg = ask(messages, tools=[DEFINITION], system="Use the calculator for all arithmetic.")
print(text_of(msg))
```

**The difference worth understanding.** Anthropic returns tool results as content blocks inside a single user message. OpenAI style returns one message per tool call with `role: "tool"`. Same idea, different packaging: the model asked, your code answered, the answer is now part of the history. Write both shapes on paper. An interviewer will be pleased that you know there are two.

There is no `is_error` flag in this format. Convention is to put the error text in the content and let the model read it. Prefix it with `ERROR:` so it is unmistakable.

### Day 4: the loop

Change three lines in `agent.py`:

- `msg.stop_reason == "end_turn"` becomes: no `msg.tool_calls`.
- `tool_blocks = [b for b in msg.content if b.type == "tool_use"]` becomes `msg.tool_calls or []`.
- Appending results: append one `role: "tool"` message per call, in a list, instead of one user message with all blocks.

Everything else, the four stop conditions, the error budget, the truncation, is unchanged. The loop is the loop.

### Day 5: five tools

No changes. Tools are your own Python. Wrap each definition in the `{"type": "function", "function": {...}}` envelope.

### Day 6: the coding agent

Run it on `qwen2.5-coder:14b` locally. This is a well defined task with clear feedback, which is what code tuned models are good at.

If it fails repeatedly, before blaming your loop, run the same task once on Gemini. If Gemini succeeds and local does not, the model is the limit and your loop is fine. Write down which steps the local model got wrong. That comparison is a genuine finding, and it is the first data point for the capability experiment on day 13.

### Days 8 to 10: memory

No changes except `estimate_tokens`, which the client above provides. There is no `count_tokens` endpoint on free providers, so the four-characters-per-token estimate is what you have. Note in your log that this estimate is wrong by ten to twenty percent and that your budget should have headroom because of it. That is a real engineering judgement.

### Days 11 to 14: evals

This is where free tiers shine and where the design gets better than the paid version.

- **Agent under test:** Ollama on your GPU. A 30 task run at 15 steps each is several hundred calls. On a free hosted tier that is an afternoon of rate limit backoff. On your own GPU it is a coffee break, and you can run it five times to measure variance instead of once. This is the single biggest advantage your setup has over a paid one.
- **Judge:** Gemini, using `client_for("gemini")`. Independent of the agent on purpose, and only about 35 calls per run, which fits any free tier comfortably. Never judge with the model under test. It grades its own style favourably.
- **Cost column:** report shadow cost, and also the resource that is actually scarce for you: **wall clock seconds, calls per task, and tokens per second**. Measuring the constraint you actually have is the skill. On a paid setup it is dollars. On yours it is GPU time.

Because runs are free, do what paid teams cannot afford: run the baseline three times before changing anything. The spread across those three runs is your noise floor, measured properly rather than guessed. Any improvement smaller than it is not real. Most people skip this step because it triples their bill. Yours is zero.

Add rate limit handling anyway, for the judge calls to Gemini:

```python
import time
from openai import RateLimitError

def with_retry(fn, tries=5):
    for i in range(tries):
        try:
            return fn()
        except (RateLimitError, RuntimeError) as e:
            if "rate limit" not in str(e).lower() or i == tries - 1:
                raise
            wait = 2 ** i
            print(f"rate limited, sleeping {wait}s")
            time.sleep(wait)
```

Exponential backoff is a production skill you would have skipped on a paid tier. You are getting it for free, literally.

### Days 15 to 17: RAG

**No changes to the code.** Embeddings and reranking were already local and free.

Where to run them is a choice worth making deliberately. On the MacBook, MiniLM at about 90 MB and the cross encoder at about 80 MB run fine on CPU, and indexing 50 documents takes under a minute. On the Linux box with CUDA they are near instant, and reranking 20 candidates stops being a latency cost worth thinking about.

Do the index build wherever the corpus lives. If you keep the FastAPI service on the Mac, keep the index there too, so a query does not cross the network twice.

One disk warning for the Mac: installing `sentence-transformers` pulls PyTorch, roughly 3 GB. With 16 GB free that is fine, but check again before Docker in week 4. On the Linux box, install the CUDA build of PyTorch, not the default CPU one, or the GPU sits idle and you will not notice.

The answering step uses your provider client. The LLM reranker on day 16 is a good job for the small local model.

### Days 18 to 21: MCP

**No changes.** MCP is a protocol, not a vendor. Your server is pure Python. Claude Code connects to it exactly as written, and Claude Code is covered by your Pro subscription.

This week is a good argument for your portfolio: the MCP server works with any client and any model.

### Days 22 to 25: FastAPI, tracing, deploy

**No changes** to FastAPI, tracing, guards, Docker, or deployment. Two adjustments:

- **Deploy against a hosted provider, not your GPU.** A recruiter opening your URL at midnight should not depend on your home machine being awake. Set `LLM_PROVIDER=gemini` in the deployed environment and keep `ollama` as your local default. This is exactly why the provider lives in one environment variable, and it is worth one sentence in your README.
- **The cost cap becomes a call cap and a rate cap.** Instead of stopping at 25 cents per request, stop at 40 model calls per request and 500 per user per day. Keep the shadow cost column so the dashboard still shows what it would cost on a paid model. Say this in the demo. It shows you understand the difference between a limit and a budget.
- **Skip the refusal fallback note** from day 1. Instead, implement provider fallback: if Gemini rate limits, retry on Groq. That is the same lesson, and it is a better one. Twenty lines in `llm.py`:

```python
FALLBACK_ORDER = ["gemini", "groq", "cerebras"]

def ask_with_fallback(messages, **kw):
    last = None
    for name in FALLBACK_ORDER:
        if PROVIDERS[name]["key_env"] and not os.getenv(PROVIDERS[name]["key_env"]):
            continue
        try:
            c, cfg = client_for(name)
            global client, MODEL
            client, MODEL = c, cfg["model"]
            return ask(messages, **kw)
        except RuntimeError as e:
            last = e
            print(f"[fallback] {name} failed: {e}")
    raise last
```

Clean it up so it does not mutate globals. Making it thread safe is a good exercise.

### Days 26 to 30: portfolio

Change one line in your README. Instead of hiding that you used free providers, lead with it:

> Built provider-agnostic against the OpenAI-compatible Chat Completions interface. Runs on Gemini, Groq, Cerebras, OpenRouter, and local Ollama with a one line change, with automatic failover between providers.

That is a stronger sentence than naming a vendor. It says you understand the abstraction, you handled rate limits and failover, and you can run anywhere. Several teams will read that as the most practical thing in your repo.

## The capability experiment, day 13

You have something most learners do not: three model tiers at zero marginal cost. Use them.

Run your 30 task eval set three times, on:

1. `llama3.2:3b` locally
2. `qwen3:14b` locally
3. Gemini

Same tasks, same prompt, same harness. Then fill in the table.

| Model | Pass rate | Mean steps | Tokens per second | Failure pattern |
|---|---|---|---|---|

Read the 3B failures carefully. You will see exactly where small models break: a required argument omitted, a tool called with the previous call's arguments, an answer given without calling the tool at all, the same edit repeated three times. The 14B run fixes most of those and shows you a different, subtler set. Gemini shows you what is left.

Then write the paragraph: **"here is what model capability actually buys, measured on my own tasks, with the failure modes at each tier."** Almost nobody applying for these jobs can say that from their own data. It costs you one afternoon and no money, and it is the strongest single item in your week 2 writeup.

## Ollama operations

```bash
ollama list                      # what you have
ollama ps                        # what is loaded in VRAM right now
ollama rm <model>                # reclaim disk
nvidia-smi -l 1                  # watch VRAM while an agent run happens
journalctl -u ollama -f          # server logs when something is wrong
```

Four things that will bite you, in the order they will happen:

**The context window silently truncates.** Ollama defaults to a small context, often 4096 tokens, regardless of what the model supports. Your week 2 agent history will exceed that and the oldest messages will vanish without an error, which looks exactly like your memory code being broken. Set it explicitly:

```bash
ollama run qwen3:14b
>>> /set parameter num_ctx 16384
>>> /save qwen3-agent
```

Then use `qwen3-agent` as your model name. Check this on day 8, before you spend an evening debugging trimming code that works.

**Tool calling quality varies by model, not just by size.** If a model ignores your tools entirely, try another before rewriting your descriptions. Confirm with a one tool test from day 3 first, so you know whether you are debugging the model or the prompt.

**VRAM fills with context.** A long agent conversation grows the KV cache. If step 12 is suddenly ten times slower than step 3, you have spilled out of VRAM. Watch `nvidia-smi` during a run once so you recognise it.

**Model reloads dominate short runs.** Set `OLLAMA_KEEP_ALIVE=30m` as in the setup section, or every pause in your eval run costs a reload.

## The one thing to watch

Free tiers change without notice. Limits get cut, models get retired, endpoints move. Before day 1, spend ten minutes on the Gemini and Groq documentation confirming the current model names and free limits, and put today's date next to what you find in your notes. When something breaks in week 3, the first thing to check is whether the model id still exists.

This is also why the provider table lives in one dictionary in one file. When a provider changes, you edit five lines, not fifty.
