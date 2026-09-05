# Day 0: Setup

About 90 minutes across both machines. Do it before day 1.

Your setup has two machines with different jobs:

| | MacBook Air (M1, 8 GB) | Linux box (RTX 5060 Ti, 16 GB) |
|---|---|---|
| Runs | Your code, FastAPI, the RAG index, Claude Code | vLLM serving the models |

Read `FREE-PROVIDER-GUIDE.md` alongside this. It carries the provider table, the credit budget, and every place a day file differs from the Anthropic version.

---

## Part A: the Linux box (30 minutes)

### A1. Confirm the GPU

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

You want 16 GB and a driver new enough for Blackwell, which needs CUDA 12.8 or newer.

### A2. Pull a model

Start with an 8B at 4-bit. It leaves room for a 32k context, which week 2 needs.

```bash
pip install -U vllm huggingface_hub
hf download Qwen/Qwen3-8B-AWQ
```

Also pull the small one now, for the day 13 capability table:

```bash
hf download Qwen/Qwen2.5-3B-Instruct
```

### A3. Serve it

```bash
vllm serve Qwen/Qwen3-8B-AWQ \
  --served-model-name local \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --reasoning-parser qwen3 \
  --kv-cache-dtype fp8 \
  --host 0.0.0.0 --port 8000 \
  --api-key local-dev-key
```

Four of those flags decide whether this course works. `--enable-auto-tool-choice` and `--tool-call-parser` make tool calling emit `tool_calls` instead of prose. `--reasoning-parser` keeps `<think>` blocks out of your content. `--enable-prefix-caching` is what day 2 measures. Full explanation in the guide.

Write the working command into a shell script and commit it. You will restart this server often, and on day 13 you will swap the model by changing one line.

### A4. Verify tool calling now, not on day 4

```bash
curl -s localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer local-dev-key" -H 'content-type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"What is 15% of 12450?"}],
       "tools":[{"type":"function","function":{"name":"calculator",
       "description":"Evaluate an arithmetic expression exactly.",
       "parameters":{"type":"object","properties":{"expression":{"type":"string"}},
       "required":["expression"]}}}],"tool_choice":"auto"}' | python3 -m json.tool
```

You must see a `tool_calls` array. Prose instead means the parser flags are wrong. Fix it today. Finding this on day 4 inside a loop you just wrote costs an evening.

Check two more things in that response: `content` has no `<think>` tags, and `usage` is present.

### A5. Open it to your LAN

```bash
ip addr show | grep "inet "     # note the 192.168.x.x
```

Home network only. Never expose port 8000 to the internet, even with the API key.

---

## Part B: the MacBook (30 minutes)

### B1. Python and uv

```bash
brew install uv
uv --version
```

### B2. The project

```bash
mkdir -p ~/agent-course && cd ~/agent-course
git init
uv init --python 3.12
uv add openai pydantic rich python-dotenv pytest "fastapi[standard]" uvicorn
```

One client package, `openai`, talks to vLLM, Cerebras, Groq, and Anthropic. You are not using OpenAI. You are using the request format the industry standardised on.

Folder shape you grow over the month:

```
agent-course/
  .env                 <- keys, never committed
  llm.py               <- day 1: the provider-agnostic client
  tools/               <- day 3 onward
  agent.py             <- day 4: the loop
  memory/              <- week 2
  evals/               <- week 2
  rag/                 <- week 3
  mcp_server/          <- week 3
  app/                 <- week 4: FastAPI service wrapping agent.py
  notes/               <- your daily logs
```

```bash
cat > .gitignore <<'G'
.env
.venv/
__pycache__/
*.db
.pytest_cache/
traces.jsonl
G
```

### B3. Keys

```bash
cat > .env <<'E'
LLM_PROVIDER=local
VLLM_HOST=http://192.168.1.50:8000
VLLM_API_KEY=local-dev-key
ANTHROPIC_API_KEY=sk-ant-...
CEREBRAS_API_KEY=...
GROQ_API_KEY=...
E
```

Replace the IP with your Linux box.

### B4. Cap the Anthropic credit

In the Anthropic console, set a hard spend limit of 40 USD today, before writing code. The credit has four jobs this month and daily building is not one of them:

| Use | Budget |
|---|---|
| Week 2 eval judge, all month | 8 USD |
| Day 2, caching as a billing line | 2 USD |
| Day 13 capability ceiling, 10 tasks | 15 USD |
| Week 4 deployed demo | 10 USD |
| Reserve | 5 USD |

Check the console every Sunday during the weekly review.

### B5. The client

Copy the provider-agnostic `llm.py` from `FREE-PROVIDER-GUIDE.md` into the project. Then smoke test three providers:

```bash
LLM_PROVIDER=local uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}]))); print(spend.report())"

LLM_PROVIDER=cerebras uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}]))); print(spend.report())"

LLM_PROVIDER=anthropic uv run python -c "
from llm import ask, text_of, spend
print(text_of(ask([{'role':'user','content':'Say ready.'}]))); print(spend.report())"
```

All three print "Ready." One file, three providers, no code change. That is the architecture the whole month rests on.

A 404 on the model means `--served-model-name` does not say `local`. A hang on the first local call is weights loading.

---

## Part C: the rest (30 minutes)

### C1. Block the cheap dopamine

Install Cold Turkey Blocker or Freedom on the Mac. Block feeds and porn. Give the password to your wife. Block at the router too if you can, since that covers both machines and your phone.

This is not optional and it is not a side note. It is the change most likely to give you back the depth you had at 23.

### C2. Paper and voice

- A paper notebook for the 20 minutes before every build session.
- Voice Memos on the phone for the daily two minute recap.

### C3. Templates

```bash
mkdir -p ~/agent-course/notes
cp ~/mahbub_space/agent-builder-30-days/templates/*.md ~/agent-course/notes/
```

### C4. Read once

`README.md`, `00-the-plan.md`, `01-imagination-practice.md`, and the day deltas in `FREE-PROVIDER-GUIDE.md`. Do not read the week folders ahead.

---

## Done when

- [ ] `nvidia-smi` shows 16 GB and a Blackwell capable driver
- [ ] vLLM serves as `local` and the launch command is saved in a script
- [ ] The curl test returns a real `tool_calls` array
- [ ] `content` has no `<think>` tags
- [ ] The Mac reaches the Linux box over the LAN
- [ ] All three providers print "Ready."
- [ ] Anthropic spend cap set to 40 USD
- [ ] Blocker on, password held by someone else
- [ ] Notebook and Voice Memos ready
- [ ] Notes folder has the templates
- [ ] Tomorrow's sticky note written: **"What is the smallest thing an agent needs to be an agent?"**
