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

A pass is a `tool_calls` array containing a `calculator` call. Check two more things in the same response: `content` has no `<think>` tags, and a `usage` object is present.

If it fails, **read the prose before you touch the parser flags.** There are two different failures that both show `"tool_calls": []`, and they have nothing to do with each other.

**Failure 1: coherent prose, no tool call.** Something like *"15% of 12450 is 1867.50."* The model understood the question, answered it correctly in text, and simply never emitted a call. That is the parser problem. Confirm `--enable-auto-tool-choice` and `--tool-call-parser` are both present, and that the parser matches the model family (`hermes` for Qwen, `llama3_json` for Llama 3.x, `mistral` for Mistral).

**Failure 2: garbled prose.** Something like:

```
To find 15% of 14,45 ... 1445 **0.15 ... So, 15% of 1 is45 is n is n is n0n10
```

The model could not copy `12450` out of its own prompt and then degenerated into repeated tokens. **This is broken inference, not a parser problem**, and no parser setting will help — a model in this state cannot produce a well-formed call. Do not spend an evening cycling through parser names; that is a wasted evening.

Fix it in this order, re-running the curl each time:

1. **Remove `--kv-cache-dtype fp8`** if present. It quantizes stored keys and values to 8 bits, and on a kernel/GPU pairing that is not well tested it does far more damage than the accuracy loss it advertises. On an RTX 50xx, suspect it first. This was the actual cause on a 5060 Ti: removing the flag alone, changing nothing else, turned degenerate output into a clean tool call.
2. **Check which quantization kernel loaded.**
   ```bash
   docker compose -f docker-compose.course.yml logs vllm-course | grep -i -E "awq|marlin|quant"
   ```
   `awq_marlin` is the good path. A plain `awq` fallback on a very new card is where numerical garbage tends to live.
3. **Take quantization out of the equation.** Run `Qwen/Qwen2.5-3B-Instruct` with no `--quantization` flag at all. About 6 GB of bf16 weights, ordinary well-trodden kernels. If 3B is coherent and 7B-AWQ is not, quantization is guilty and your GPU is fine.

Known-good replacements once you know the cause: `RedHatAI/Qwen2.5-7B-Instruct-FP8-dynamic` with `--quantization fp8` (FP8 is native on Blackwell, roughly 8 GB), or `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` with `--tool-call-parser llama3_json`, which is already on your disk and already proven on this card by voice-rag.

The bar for passing is all three at once: coherent sentences, the digits `12450` reproduced exactly, and a populated `tool_calls` array.

### A4b. Measure your tokens per second

A working endpoint is not the same as a usable one. Day 1 makes single calls and you will not notice slow. Day 12 runs 30 fixtures with multiple turns each, and the difference between 6 and 40 tokens/s is the difference between a coffee break and an overnight job. Measure now.

Do **not** measure this by reading `Avg generation throughput` out of the vLLM logs. That number is tokens counted in a fixed 10-second window divided by 10 seconds, not the rate while the model was generating. A request that finishes in 4 seconds is reported at 40 percent of its real speed, and you cannot tell from the line itself. The giveaway: when `Avg prompt throughput` reads 17.5 and your prompt was exactly 175 tokens, you are looking at a window average, not a rate.

Use the benchmark in this repo. Standard library only, so it needs no venv and no installs on the Linux box:

```bash
python3 scripts/bench_llm.py
```

It streams the response and reports two numbers separately, because they are different problems with different fixes:

| | what it is | what changes it |
|---|---|---|
| **TTFT** | time to first token: queueing plus prefill | prompt length, prefix caching |
| **decode** | tokens/s *after* the first token | model size, quantization kernel, memory bandwidth |

An agent turn pays TTFT once and decode once per token it writes. So a slow agent with short tool-call outputs is a TTFT problem, and a slow agent with long written answers is a decode problem. A single blended tokens/s figure cannot tell you which one you have, which is why the naive version — total tokens over total wall clock — is not good enough either. It buries TTFT inside the average.

The script runs three times with a slightly different prompt each time, so prefix caching does not flatter the TTFT, and reports the best decode rate.

To know whether your number is good, compute the ceiling rather than guessing. Single-stream decode is memory-bound: every token requires reading the whole weight set once, so the ceiling is roughly `memory bandwidth / weight size`. An RTX 5060 Ti has 448 GB/s and a 4-bit 7B is about 4 GB, giving roughly 110 tok/s in theory. Good kernels reach 70-80% of a bandwidth ceiling.

The measured result on this exact setup — Qwen2.5-7B-Instruct-AWQ, 5060 Ti, the compose file in `infra/` — is **84 tok/s decode and 26ms TTFT**. That is your target. Under about 60 means a configuration problem rather than a slow card, and you now have a principled reason for saying so instead of a vibe.

Note how much this matters for day 13. When you compare a 3B against a 7B, you need to know that a difference is the *model* and not a kernel that silently fell back. A baseline you measured yourself is what makes that comparison trustworthy.

The first thing to check is the quantization kernel, because the failure is silent and scrolls past during boot:

```bash
docker compose -f docker-compose.course.yml logs vllm-course | grep -i marlin
```

If you see this, you are running several times slower than the hardware allows:

```
Detected that the model can run with awq_marlin, however you specified
quantization=awq explicitly, so forcing awq. Use quantization=awq_marlin
for faster inference
```

The fix is to **remove** the `--quantization` flag, not to correct it. vLLM reads the scheme from the model's own `config.json` and selects the fastest kernel that supports it. Naming a scheme explicitly does not confirm that choice, it overrides it — so the flag that looks like documentation is actually an instruction, and a pessimising one.

That is the general lesson, and it will cost you time again elsewhere if you don't take it now: **a config flag that merely restates a default is not free.** It silently opts you out of auto-detection, and auto-detection is usually smarter than you are about the machine you happen to be sitting at.

Second thing to check, if the kernel is right and it's still slow: `nvidia-smi`. Confirm nothing else holds significant VRAM. A desktop session costs roughly 0.8 GB across Xorg, your shell, and the browser, which is expected and already budgeted for. Another vLLM is not.

Write the number you get into your day 0 log. When you change models on day 13, you will want the baseline.

### A4c. Confirm the container reports healthy

```bash
docker ps --format '{{.Names}}\t{{.Status}}'
```

You want `Up N minutes (healthy)`. If it says `(unhealthy)` or sits at `(starting)` long after boot, read what Docker recorded rather than re-running the probe by hand:

```bash
docker inspect --format '{{json .State.Health}}' vllm-course | python3 -m json.tool
```

That prints the `ExitCode` and `Output` of the last few probes. A probe failing for its own reasons looks nothing like a sick server, and the output says which you have. The one that bit this course:

```
exec: "python": executable file not found in $PATH
```

The vLLM image ships `python3` and no `python` alias, and a `["CMD", ...]` healthcheck resolves the executable directly against a bare PATH with no shell. So the probe never ran, the server was fine the whole time, and the container advertised `starting` indefinitely. The compose file now uses `CMD-SHELL` with `python3`.

Two things worth keeping from that:

**A failing healthcheck is not a failing service.** They fail independently, and a red status that is actually a broken probe will send you debugging a healthy system. Always read `.State.Health` before touching the service.

**Verifying a probe by running it yourself proves less than it appears to.** `docker exec ... python` can succeed interactively while the identical healthcheck fails, because they resolve binaries under different rules. The only trustworthy evidence about a healthcheck is the output Docker recorded from running it.

This is cosmetic today, since nothing depends on the condition. It stops being cosmetic in week 4, when `depends_on: condition: service_healthy` will hang your own stack's startup on a probe that can never pass.

### A5. VRAM: run one stack at a time

You have 16 GB. The course service asks for 80 percent of it, which is right when it runs alone and will fail to allocate if voice-rag's vLLM is also up.

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
