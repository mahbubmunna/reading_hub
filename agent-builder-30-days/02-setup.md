# Day 0: Setup

About 90 minutes across both machines. Do it before day 1.

Your setup has two machines with different jobs:

| | MacBook Air (M1, 8 GB) | Linux box (RTX 5060 Ti, 16 GB) |
|---|---|---|
| Runs | Your code, FastAPI, the RAG index, Claude Code | vLLM serving the models |

Read `FREE-PROVIDER-GUIDE.md` alongside this. It carries the provider table, the credit budget, and every place a day file differs from the Anthropic version.

---

## Part A: the Linux box (30 minutes)

You already run vLLM in Docker for the voice-rag project. **Keep doing that. Do not install vLLM or `huggingface_hub` natively.** Your compose already mounts `~/.cache/huggingface` into the container, which means the container downloads weights straight into your host cache. There is nothing to install and nothing to download by hand.

What you do need is a **second vLLM service for the course**, because the course needs different flags than voice-rag does, and because you will swap models on day 13. You do not want to restart a working project every time you do that.

### A1. Confirm the GPU

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

The second command proves Docker can see the GPU. The 5060 Ti is Blackwell, so you need a recent `vllm/vllm-openai` image built against CUDA 12.8 or newer. Your voice-rag stack works, so this is already fine.

### A2. Add the course service

Copy `infra/docker-compose.course.yml` from this course folder to your Linux box, into its own directory:

```bash
mkdir -p ~/agent-course/infra
# copy the file there, then
cd ~/agent-course/infra
echo "VLLM_API_KEY=local-dev-key" >> .env
echo "HF_TOKEN=${HF_TOKEN}" >> .env      # only needed for gated repos
docker compose -f docker-compose.course.yml up -d
docker compose -f docker-compose.course.yml logs -f
```

First start downloads about 5.5 GB of weights. Wait for the log line saying the server is running on port 8000.

**It listens on host port 8000. Your voice-rag vLLM is on 8080.** No conflict, but read the VRAM note below before running both at once.

### A3. Understand what your voice-rag config is missing

Your existing service is correct for voice-rag and wrong for this course, in four specific ways. Worth understanding rather than copying blindly:

| Your voice-rag setting | Problem for the course |
|---|---|
| No `--enable-auto-tool-choice`, no `--tool-call-parser` | **The blocker.** The endpoint never emits `tool_calls`. Your agent gets prose instead and the loop looks broken |
| `--max-model-len 8192` | Week 2 history exceeds it. vLLM rejects rather than truncates, so it appears as errors mid-eval |
| `--gpu-memory-utilization 0.5` | Correct when sharing with the voice backend, wasteful when the course runs alone |
| `--served-model-name meta-llama/...` | Fine, but the course uses `local` so model swaps need no code change |

The course compose fixes all four. Leave your voice-rag file alone.

### A3b. If it fails with CUDA out of memory

Common on a 16 GB card, and the compose file is already tuned to avoid it. If you still hit it:

```bash
nvidia-smi          # is the voice-rag stack still up? is a desktop session holding VRAM?
```

The error appears near the end of boot, during CUDA graph capture, saying it tried to allocate a couple of hundred MiB with almost nothing free. vLLM sizes its budget as a fraction of **total** GPU memory, fills the KV cache to that budget, then captures CUDA graphs, and it does not count the CUDA context or your display server, roughly 0.8 GiB on a desktop.

Turn these down in order, restarting each time, and stop when it boots:

1. `--gpu-memory-utilization` to `0.75`
2. `--max-model-len` to `8192`
3. Add `--enforce-eager`, which skips graph capture entirely and frees 1 to 2 GiB for perhaps 10 to 20 percent less throughput

If `--enforce-eager` alone fixes it, graphs were the cause and you can raise the other two back up.

### A4. Verify tool calling now, not on day 4

This is the single most important command in the setup.

```bash
curl -s localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer local-dev-key" -H 'content-type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"What is 15% of 12450?"}],
       "tools":[{"type":"function","function":{"name":"calculator",
       "description":"Evaluate an arithmetic expression exactly.",
       "parameters":{"type":"object","properties":{"expression":{"type":"string"}},
       "required":["expression"]}}}],"tool_choice":"auto"}' | python3 -m json.tool
```

You must see a `tool_calls` array with a `calculator` call in it. If you get prose describing the arithmetic instead, the parser flags are wrong. Fix it today.

Check two more things in that response: `content` has no `<think>` tags, and a `usage` object is present.

### A5. VRAM: run one stack at a time

You have 16 GB. The course service asks for 90 percent of it, which is right when it runs alone and will fail to allocate if voice-rag's vLLM is also up.

```bash
# switch to course work
docker compose -f ~/voice-rag/docker-compose.yml stop vllm voice-rag-backend
docker compose -f ~/agent-course/infra/docker-compose.course.yml up -d

# switch back
docker compose -f ~/agent-course/infra/docker-compose.course.yml stop
docker compose -f ~/voice-rag/docker-compose.yml up -d
```

Make two shell aliases for this on day 0. You will run them many times.

If you genuinely need both at once, drop both `--gpu-memory-utilization` values to 0.35 and both `--max-model-len` to 8192. Everything works, everything is slower, and week 2 evals get cramped. Prefer switching.

### A6. Open it to your LAN

```bash
ip addr show | grep "inet "     # note the 192.168.x.x
```

Your compose already binds `0.0.0.0`, so the Mac can reach it. Home network only. Never expose port 8000 to the internet, even with the API key.

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
VLLM_HOST=http://192.168.1.106:8000
VLLM_API_KEY=local-dev-key
ANTHROPIC_API_KEY=sk-ant-...
CEREBRAS_API_KEY=...
GROQ_API_KEY=...
E
```

That IP is the one in your voice-rag frontend config. Port 8000 is the course vLLM; 8080 is your voice-rag one.

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

- [ ] `docker run --gpus all ... nvidia-smi` sees the GPU
- [ ] `docker-compose.course.yml` is on the Linux box and the service is up on port 8000
- [ ] The service boots without CUDA OOM
- [ ] **The curl test returns a real `tool_calls` array.** Nothing else matters until this passes
- [ ] `content` has no `<think>` tags, and `usage` is present
- [ ] Shell aliases exist for switching between the course and voice-rag stacks
- [ ] The Mac reaches the Linux box over the LAN
- [ ] All three providers print "Ready."
- [ ] Anthropic spend cap set to 40 USD
- [ ] Blocker on, password held by someone else
- [ ] Notebook and Voice Memos ready
- [ ] Notes folder has the templates
- [ ] Tomorrow's sticky note written: **"What is the smallest thing an agent needs to be an agent?"**
