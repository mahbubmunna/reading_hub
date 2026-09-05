# Running This Course For Free

You do not need the Anthropic API. Every lesson in this course works against free providers, because the concepts are about agents, not about one vendor. This file replaces the Anthropic parts of `02-setup.md`.

## First, what your Claude Pro subscription does and does not cover

**Covers:** Claude Code as your coding assistant. The terminal tool you are using right now, for writing and debugging the course code, is included in Pro. Use it freely within your Pro limits.

**Does not cover:** programmatic API access for the agent you are building. Your agent calling a model in a loop is API usage, billed separately. That is what we are replacing with free providers.

So: Claude Code stays as your pair programmer. Something else powers your agent.

## Your setup

| | MacBook Air | Linux box |
|---|---|---|
| Chip | Apple M1 | RTX 5060 Ti, 16 GB VRAM |
| Memory | 8 GB unified | serving with vLLM |
| Job | Writing code, FastAPI, the RAG index, the browser | Running the models |

Plus Groq and Cerebras keys already set up, and 40 USD of Anthropic credit.

This is a better setup than most people doing this course have, including people paying for it. Three things fall out of it.

**vLLM gives you real prefix caching.** Day 2 was the one lesson that free tiers could not teach properly. vLLM has automatic prefix caching with hit rate metrics you can read, so you will measure cache hits on your own hardware instead of reading about them. That section is rewritten below.

**vLLM gives you real structured output.** Grammar constrained decoding means the JSON is valid by construction, not by hoping. That is stronger than most hosted free tiers.

**Local is unlimited, so you can measure things paid teams skip.** Three baseline runs to establish a noise floor. A full model comparison across four tiers. Both are in the day deltas below.

## Serving with vLLM

### Models that fit 16 GB

vLLM preallocates VRAM, so unlike Ollama you must size the model and the context window together. Budget roughly: weights, plus KV cache, plus about 1 GB of overhead.

| Model | Weights | Good for | Context to ask for |
|---|---|---|---|
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | about 5.5 GB | Your daily driver. Known-good tool calling with `hermes` | 32k |
| `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ` | about 5.5 GB | Week 1 coding agent | 32k |
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | about 9 GB | More reasoning, if day 6 shows the 7B is the limit | 16k |
| `Qwen/Qwen2.5-3B-Instruct` | about 2 GB | The deliberately weak one for day 13 | 8k |
| `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` | already on disk | Zero download. Use `llama3_json` parser | 16k |

Start with Qwen2.5-7B-Instruct-AWQ. If you want to prove the pipeline before downloading anything, start with the Llama you already have cached from voice-rag, switch the parser to `llama3_json`, and confirm the day 3 curl returns `tool_calls`. Then download Qwen and switch.

Repo ids on Hugging Face move. If one 404s, search the model name plus AWQ and take a current quant; the parser depends on the model family, not on who quantised it.

### Run it in Docker, alongside your existing stack

You already have vLLM in Docker for the voice-rag project, and that compose mounts `~/.cache/huggingface` into the container. That mount is doing the work: weights land in your host cache and are shared between projects. **Do not install vLLM or `huggingface_hub` natively.** There is nothing to gain and two toolchains to keep in sync.

Use `infra/docker-compose.course.yml` from this course folder. It is a second service, on host port 8000, with the flags the course needs. Your voice-rag file stays untouched.

The command it runs:

```
--model Qwen/Qwen2.5-7B-Instruct-AWQ
--served-model-name local
--quantization awq
--max-model-len 32768
--gpu-memory-utilization 0.90
--enable-prefix-caching
--enable-auto-tool-choice
--tool-call-parser hermes
--kv-cache-dtype fp8
```

Four of those decide whether the course works at all.

**`--enable-auto-tool-choice` and `--tool-call-parser`.** Both, or the endpoint never emits `tool_calls`. The model describes the tool call in prose, your loop sees nothing, and it looks exactly like your day 4 code is broken. Your current voice-rag service has neither, which is correct for voice-rag and fatal here. Parser by family: `hermes` for Qwen2.5 and Qwen3, `llama3_json` for Llama 3.x, `mistral` for Mistral.

**`--reasoning-parser`**, only if your model emits reasoning. Qwen2.5 does not, so it is absent above. If you switch to Qwen3 or an R1 distill, add `--reasoning-parser qwen3` or the `<think>` blocks land in `message.content` and quietly corrupt every summary and every eval score.

**`--enable-prefix-caching`.** Default on in current vLLM, passed explicitly so day 2 is unambiguous.

**`--max-model-len 32768`.** Your voice-rag value of 8192 is fine for voice turns. Week 2 agent history goes past it, and vLLM rejects over-length requests rather than truncating, so a small value shows up as errors in the middle of an eval run.

**`--served-model-name local`** means your Python always says `model="local"`. Day 13 swaps four models by editing one compose line and restarting. Zero code changes.

### VRAM: run one stack at a time

16 GB does not fit both stacks at 90 percent. Two aliases solve it:

```bash
alias course-up='docker compose -f ~/voice-rag/docker-compose.yml stop vllm voice-rag-backend && \
                 docker compose -f ~/agent-course/infra/docker-compose.course.yml up -d'
alias voice-up='docker compose -f ~/agent-course/infra/docker-compose.course.yml stop && \
                docker compose -f ~/voice-rag/docker-compose.yml up -d'
```

Both at once is possible at `--gpu-memory-utilization 0.35` and `--max-model-len 8192` each, but week 2 evals get cramped. Prefer switching.

### From the MacBook

```bash
# on the Linux box
ip addr show | grep "inet "
# from the Mac
curl -H "Authorization: Bearer local-dev-key" http://192.168.1.106:8000/v1/models
```

Home network only. Do not expose port 8000 to the internet.

### The metrics endpoint, which you will use on day 2

```bash
curl -s http://192.168.1.106:8000/metrics | grep -E "prefix_cache|num_requests"
```

You get counters including `vllm:prefix_cache_queries_total` and `vllm:prefix_cache_hits_total`. Hit rate is the ratio. This is the number day 2 is about.

## The provider table

Local first, hosted for the jobs where independence or uptime matters. All of these speak the OpenAI Chat Completions format, so one code path handles every one of them.

| Provider | Cost | Role in your setup |
|---|---|---|
| **vLLM on your Linux box** | Free, unlimited | **Default.** Building, evals, caching lessons, structured output |
| **Cerebras** | Free tier, already set up | Fastest hosted. Long eval runs when the GPU is busy or you are away from home |
| **Groq** | Free tier, already set up | Second hosted opinion, and your failover target |
| **Anthropic** | 40 USD credit | The eval judge, the capability ceiling, the deployed demo. See the budget below |
| **Google AI Studio** | Free tier | Optional fourth opinion. Only if you want a fifth row in the day 13 table |

### Spending the 40 USD of Anthropic credit

Credit is finite, so spend it where a frontier model is genuinely irreplaceable rather than on daily building. Four places qualify.

| Use | Model | Budget | Why it must be paid |
|---|---|---|---|
| Week 2 eval judge, whole month | `claude-haiku-4-5` | 8 USD | The judge must be independent of the model under test and consistent across runs. A local judge grading a local agent is the classic mistake |
| Day 2, prompt caching taught properly | `claude-opus-5` | 2 USD | The API reports `cache_read_input_tokens` per call, so you see caching as a billing line, not just a hit rate. Pair it with the vLLM version below and you understand both |
| Day 13 capability ceiling, 10 task subset | `claude-opus-5` | 15 USD | The top row of your comparison table. Without it you do not know how far from the ceiling your local model is |
| Week 4 deployed demo | `claude-haiku-4-5` | 10 USD | A recruiter opening your URL should not depend on your home GPU being awake |
| Reserve | | 5 USD | Something will surprise you |

Set a 40 USD hard spend cap in the Anthropic console today, before writing any code. Then check the console once a week. If the judge line is growing faster than the table above predicts, your rubric is too long or you are rerunning evals more than planned. Both are worth knowing.

Do not build daily on the credit. It will be gone in week 2 and you will lose the thing that makes your setup good, which is unlimited local iteration.

## Which provider for which job

| Job | Use | Why |
|---|---|---|
| Daily building, days 1 to 10 | vLLM, `local` | Unlimited iterations |
| Week 1 coding agent | vLLM, Qwen2.5-Coder-14B-AWQ | Code tuned, well defined task |
| Day 2 caching, part one | vLLM metrics | See the hit rate change on your own hardware |
| Day 2 caching, part two | Anthropic, `claude-opus-5` | See it as tokens billed at a tenth of the price |
| Week 2 eval runs | vLLM | Several hundred calls per run. Run the baseline three times |
| Week 2 judge | **Anthropic, `claude-haiku-4-5`** | Independent of the agent, consistent across the month |
| Week 2 summarizer | vLLM, a 3B model | Cheap job, cheap model. The real world lesson survives |
| Week 3 embeddings and reranking | sentence-transformers on the GPU | Free and fast |
| Day 13 capability table | 3B local, 8B local, Cerebras, Anthropic | Four points on a curve, on your own tasks |
| Week 4 live demo | Anthropic, `claude-haiku-4-5` | Uptime a stranger can rely on |
| Failover target | Cerebras, then Groq | Already configured, nothing to build |

## Install

```bash
cd ~/agent-course
uv add openai pydantic rich python-dotenv pytest "fastapi[standard]" uvicorn
```

One package, `openai`, talks to every provider above. You are not using OpenAI. You are using their request format, which the whole industry adopted.

`.env`:

```bash
LLM_PROVIDER=local
VLLM_HOST=http://192.168.1.106:8000        # your Linux box; omit if running on it
VLLM_API_KEY=local-dev-key                # matches vllm serve --api-key
ANTHROPIC_API_KEY=...                     # the judge, and day 2 part two
CEREBRAS_API_KEY=...
GROQ_API_KEY=...
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
    "local": {   # vLLM on the Linux box
        "base_url": os.getenv("VLLM_HOST", "http://localhost:8000").rstrip("/") + "/v1",
        "key_env": "VLLM_API_KEY",
        "model": "local",        # matches --served-model-name
        "big": "local",
        "small": "local",
    },
    "anthropic": {   # OpenAI-compatible endpoint; spend the credit deliberately
        "base_url": "https://api.anthropic.com/v1/",
        "key_env": "ANTHROPIC_API_KEY",
        "model": "claude-haiku-4-5",
        "big": "claude-opus-5",
        "small": "claude-haiku-4-5",
    },
}

PROVIDER = os.getenv("LLM_PROVIDER", "local")
_cfg = PROVIDERS[PROVIDER]
MODEL = os.getenv("LLM_MODEL", _cfg["model"])

client = OpenAI(
    base_url=_cfg["base_url"],
    api_key=os.getenv(_cfg["key_env"], "x") if _cfg["key_env"] else "none",
)


def client_for(provider: str) -> tuple[OpenAI, dict]:
    """A second client, for the judge or the summarizer. Keeps them independent."""
    c = PROVIDERS[provider]
    return OpenAI(base_url=c["base_url"],
                  api_key=os.getenv(c["key_env"], "x") if c["key_env"] else "none"), c


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
LLM_PROVIDER=local uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}])))
print(spend.report())"

LLM_PROVIDER=cerebras uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}])))
print(spend.report())"
```

Both should print "Ready." That is the whole point: one file, two providers, no code change.

If the local one returns a 404 on the model, your `--served-model-name` does not say `local`. If it hangs, vLLM is still loading weights, which takes a minute on first start.

## What changes in the course, day by day

Most days change nothing. Here is every difference.

### Day 1: first call

Use the client above instead of the Anthropic one. Two conceptual differences to write in your notes:

- **Content is a string, not a list of blocks.** The OpenAI format puts text in `message.content` and tool calls in `message.tool_calls`, as separate fields. The Anthropic format puts both in one `content` list of typed blocks. Neither is wrong. Knowing both is worth an interview point.
- **The system prompt is a message** with `role: "system"`, first in the list. In the Anthropic API it is a separate top level field.

The "break it on purpose" exercises still work. Statelessness, `finish_reason`, and history growth are identical.

### Day 2: structured output and caching

Both halves of this day get **better** on your setup than in the paid version. Do not skip it.

#### Structured output, grammar constrained

vLLM constrains decoding to your schema, so invalid JSON is impossible rather than unlikely:

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

vLLM also accepts `extra_body={"guided_json": CaseEntry.model_json_schema()}`, and `guided_choice` for a fixed set of options, and `guided_regex`. Try `guided_choice` on a classification: it is the cleanest way to force one of five labels and it is faster than asking for JSON.

Then do the experiment that teaches the concept. Run the same extraction **without** the response format, twenty times, on the 3B model. Count how many produce valid parseable JSON. Then run it twenty times with the schema. The second number is twenty. Write both in your log. That gap is why constrained decoding exists, and you just measured it rather than read it.

Add the repair loop anyway, because hosted providers do not all guarantee this:

```python
try:
    entry = CaseEntry.model_validate_json(msg.content)
except ValidationError as e:
    msg = ask(messages + [
        {"role": "assistant", "content": msg.content},
        {"role": "user", "content": f"That did not validate: {e}. Return only valid JSON."},
    ])
    entry = CaseEntry.model_validate_json(msg.content)
```

#### Prompt caching, measured twice

**Part one, on your own GPU.** Build the long stable system prompt from the day 2 file. Before the first call, read the counters:

```bash
curl -s $VLLM_HOST/metrics | grep -E "vllm:prefix_cache_(queries|hits)_total"
```

Send three different questions against the same system prompt. Read the counters again. Hits divided by queries is your prefix cache hit rate, and it should be high after the first call.

Now do the destructive experiment. Put the current time at the top of the system prompt:

```python
system = f"Time: {datetime.datetime.now()}\n" + rules
```

Send three more questions. Read the counters again. The hit rate collapses, because the prefix changed on every request. That is the single most common caching bug in real codebases, and you just caused it on purpose and watched the number move.

Also watch latency. Time to first token drops noticeably on a cache hit with a long prefix. Record both numbers, hit rate and time to first token, before and after.

**Part two, on Anthropic, about 2 USD.** vLLM shows you caching as a hit rate. Anthropic shows it as money. Run the same three questions with `LLM_PROVIDER=anthropic` and a `cache_control` breakpoint on the system block, then read `usage.cache_read_input_tokens` and `usage.cache_creation_input_tokens`.

```python
resp = client.messages.create(
    model="claude-opus-5", max_tokens=200,
    system=[{"type": "text", "text": rules, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": q}],
)
print(resp.usage.cache_creation_input_tokens, resp.usage.cache_read_input_tokens)
```

Call one writes the cache. Calls two and three read it, at roughly a tenth of the input price.

You now have both views of one mechanism: hit rate on hardware you control, and a billing line on a hosted API. Write the four sentence explanation covering both. Almost nobody can do that, because most people have only ever seen one side.

#### The design rule, which is what actually matters

Order the prefix stable to volatile: tools, then system prompt, then old history, then the new question. Never put a timestamp, a request id, an unsorted dict, or a per user greeting at the top. Note in your log that vLLM caches automatically by prefix while Anthropic needs an explicit breakpoint, but the rule that makes both work is identical.

### Day 3: the first tool

**Do this before anything else today.** Confirm vLLM is actually emitting tool calls:

```bash
curl -s $VLLM_HOST/v1/chat/completions \
  -H "Authorization: Bearer $VLLM_API_KEY" -H 'content-type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"What is 15% of 12450?"}],
       "tools":[{"type":"function","function":{"name":"calculator",
       "description":"Evaluate an arithmetic expression exactly.",
       "parameters":{"type":"object","properties":{"expression":{"type":"string"}},
       "required":["expression"]}}}],"tool_choice":"auto"}' | python3 -m json.tool
```

You must see a `tool_calls` array in the response. If instead you see prose describing the calculation, vLLM is missing `--enable-auto-tool-choice --tool-call-parser hermes`, or the parser is wrong for your model family. Fix the server now. Debugging this on day 4, inside a loop you just wrote, costs an evening.

While you are here, confirm `content` has no `<think>` blocks in it. If it does, add `--reasoning-parser qwen3` and restart.

The concept is identical to the Anthropic version. The wire format differs, and you should write both shapes in your notes.

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

Run it on Qwen2.5-Coder-14B-AWQ locally. This is a well defined task with clear feedback, which is what code tuned models are good at.

If it fails repeatedly, before blaming your loop, run the same task once on `claude-opus-5`, which costs a few cents. If Opus succeeds and local does not, the model is the limit and your loop is fine. Write down which steps the local model got wrong. That comparison is a genuine finding, and it is the first data point for the capability table on day 13.

### Days 8 to 10: memory

No changes except `estimate_tokens`, which the client above provides. There is no `count_tokens` endpoint on free providers, so the four-characters-per-token estimate is what you have. Note in your log that this estimate is wrong by ten to twenty percent and that your budget should have headroom because of it. That is a real engineering judgement.

### Days 11 to 14: evals

This is where free tiers shine and where the design gets better than the paid version.

- **Agent under test:** vLLM on your GPU. A 30 task run at 15 steps each is several hundred calls. On a free hosted tier that is an afternoon of rate limit backoff. On your own GPU it is a coffee break, and you can run it five times to measure variance instead of once. This is the single biggest advantage your setup has over a paid one.
- **Judge:** Anthropic `claude-haiku-4-5`, using `client_for("anthropic")`. Independent of the agent on purpose, and about 35 calls per run, roughly 15 cents. Never judge with the model under test. It grades its own style favourably.
- **Cost column:** report shadow cost, and also the resource that is actually scarce for you: **wall clock seconds, calls per task, and tokens per second**. Measuring the constraint you actually have is the skill. On a paid setup it is dollars. On yours it is GPU time.

Because runs are free, do what paid teams cannot afford: run the baseline three times before changing anything. The spread across those three runs is your noise floor, measured properly rather than guessed. Any improvement smaller than it is not real. Most people skip this step because it triples their bill. Yours is zero.

Add rate limit handling anyway, for the judge calls to Anthropic:

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

- **Deploy against a hosted provider, not your GPU.** A recruiter opening your URL at midnight should not depend on your home machine being awake. Set `LLM_PROVIDER=anthropic` with `claude-haiku-4-5` in the deployed environment and keep `local` as your default everywhere else. This is exactly why the provider lives in one environment variable, and it is worth one sentence in your README.
- **The cost cap becomes a call cap and a rate cap.** Instead of stopping at 25 cents per request, stop at 40 model calls per request and 500 per user per day. Keep the shadow cost column so the dashboard still shows what it would cost on a paid model. Say this in the demo. It shows you understand the difference between a limit and a budget.
- **Skip the refusal fallback note** from day 1. Instead, implement provider fallback: if your GPU is down or overloaded, retry on Cerebras, then Groq. That is the same lesson, and it is a better one. Twenty lines in `llm.py`:

```python
FALLBACK_ORDER = ["local", "cerebras", "groq"]

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

> Built provider-agnostic against the OpenAI-compatible Chat Completions interface. Runs on self-hosted vLLM, Cerebras, Groq, and Anthropic with a one line change, with automatic failover between providers. Evaluated across four model tiers on the same task set and judge.

That is a stronger sentence than naming a vendor. It says you understand the abstraction, you handled rate limits and failover, and you can run anywhere. Several teams will read that as the most practical thing in your repo.

## The capability experiment, day 13

You have four model tiers available and three of them are free. Nobody else doing this course has that. Use it.

Run your 30 task eval set on:

1. `Qwen2.5-3B-Instruct` locally, the weak one
2. `Qwen3-8B-AWQ` locally, your daily driver
3. Cerebras, a large hosted open model
4. `claude-opus-5`, on a 10 task subset to protect the credit

Same tasks, same prompt, same harness, same judge. Fill in the table.

| Model | Pass rate | Mean steps | Tokens per second | Cost per task | Dominant failure |
|---|---|---|---|---|---|

Read the 3B failures line by line. You will see exactly where small models break: a required argument omitted, a tool called with the previous call's arguments, an answer given without calling the tool, the same edit repeated three times until the step limit. The 8B run fixes most of those and reveals a subtler set. Cerebras shows what scale buys. Opus shows the ceiling.

Then write the paragraph: **"here is what model capability actually buys, measured on my own tasks, with the failure mode at each tier and the cost of closing each gap."**

That sentence, backed by your own table, is the strongest thing you will produce this month. Most candidates have opinions about model choice. You will have data.

One methodological note to include: the judge is the same across all four rows and is independent of every model under test. Say so explicitly. An interviewer who knows evals will check for exactly that.

## vLLM operations

```bash
nvidia-smi -l 1                                  # VRAM while an agent run happens
curl -s $VLLM_HOST/metrics | grep vllm:          # cache, throughput, queue depth
curl -s $VLLM_HOST/v1/models                     # confirm the served name
journalctl -u vllm -f                            # or wherever your logs go
```

Five things that will bite you, roughly in the order they will happen.

**Tool calls silently become prose.** Missing `--enable-auto-tool-choice` or the wrong `--tool-call-parser`. Covered on day 3. This is the number one cause of "my agent loop does not work".

**Reasoning tags pollute your output.** Qwen3 emits `<think>` blocks. Without `--reasoning-parser`, they end up in `message.content`, then in your summaries, then in your eval scoring, and every number you produce is wrong in a way that is hard to see. Check `content` once on day 1 and you will never be caught by it.

**Context is a hard wall, not a soft one.** vLLM refuses requests longer than `--max-model-len` with an error rather than truncating quietly. That is better than silent truncation, but week 2's growing history will hit it. Your trimming code from day 8 is what prevents it. Catch the error and treat it as a signal your budget is too high.

**VRAM is preallocated.** `--gpu-memory-utilization 0.90` claims that fraction at startup regardless of the model size. If you cannot load a bigger model, lower `--max-model-len` before lowering the utilization, since KV cache is usually what does not fit.

**Throughput is much better batched than serial.** Your day 12 eval runner calls tasks one at a time, which leaves the GPU mostly idle. Running five tasks concurrently with a thread pool can cut a 30 task run several fold, because vLLM batches continuously. That is a genuinely good day 12 exercise, and it is a real production insight: the bottleneck was never the GPU, it was your runner.



## The one thing to watch

Free tiers change without notice. Limits get cut, models get retired, endpoints move. Before day 1, spend ten minutes on the Cerebras and Groq documentation confirming the current model names and free limits, and put today's date next to what you find in your notes. When something breaks in week 3, the first thing to check is whether the model id still exists.

This is also why the provider table lives in one dictionary in one file. When a provider changes, you edit five lines, not fifty.

Two more, specific to you. vLLM's flag names move between releases, so pin the version you got working and write it in your notes. And check the Anthropic console spend page every Sunday during the weekly review, so the credit lasts the whole month.
