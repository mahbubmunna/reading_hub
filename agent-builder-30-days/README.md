# Agent Builder in 30 Days

A step by step course for one intense month. Goal: by day 30 you can build, evaluate, and ship an LLM agent, and you have a portfolio link that proves it.

This is written as a personal instructor would write it. It tells you what to do each day, why it matters, what to type, what to check, and when you are done. Do not read ahead. Do today's file, finish today's "Done when", then stop.

## How to use this folder

```
agent-builder-30-days/
  README.md                     <- you are here, read once
  FREE-PROVIDER-GUIDE.md        <- your stack, and every day-file delta. Read second
  00-the-plan.md                <- the month at a glance, print it
  01-imagination-practice.md    <- the daily creativity routine
  02-setup.md                   <- do this before day 1
  reading-list.md               <- what to read in block 3, in order
  templates/                    <- copy these, fill them daily
  week-1-the-loop/              <- day 01 to 07
  week-2-memory-and-evals/      <- day 08 to 14
  week-3-rag-and-mcp/           <- day 15 to 21
  week-4-ship/                  <- day 22 to 30
```

Each week has a README with the goal, the deliverable, and a checklist. Each day is one file.

## The daily shape

| Block | Length | What |
|---|---|---|
| Morning walk | 20 to 30 min | Outside, no phone, no audio. Hold one question from yesterday. |
| Block 1 | 90 min | Build. First 20 minutes pen and paper only. Then code. |
| Strength | 20 min, 3 days a week | Push ups, squats, rows, planks. |
| Block 2 | 60 min | Build, continued. End with something that runs. |
| Block 3 | 45 min | Read. One item from reading-list.md. Five lines of notes. |
| Evening | 10 min | Three ideas in the idea log. Two minute spoken recap, recorded. |
| Midnight | Screens off. Paper book until sleep. |

If a baby day gives you only one block, do Block 1.

## The rules

1. **No deliverable, no next week.** Slip a day. Never skip a deliverable.
2. **Paper before AI.** Every build session starts with 20 minutes of pen and paper. Write what you will build, what the pieces are, what could break. Only then open Claude Code or Antigravity. Compare its plan with yours. The gap is where you learn.
3. **Own notes, own words.** After each block, five lines in `templates/daily-log.md`. Reread the whole log every Sunday.
4. **Blockers stay on.** Feeds and porn are blocked by a tool someone else holds the password for. Week 2 will feel worst. That is withdrawal, not failure.
5. **News once a week.** Sunday, one hour, from the sources in reading-list.md. Nothing daily.
6. **Explain out loud daily.** Two minutes, recorded. Rambling shrinks when you hear it.
7. **Judge nothing before day 30.**

## How to know it is working

Three signals at day 30:

- You can hold one hard problem for 40 minutes without wanting to switch.
- The idea log is getting more interesting to reread.
- You can explain your agent in two minutes without rambling.

## Where FastAPI fits

Weeks 1 to 3 build a plain Python library: the loop, tools, memory, evals, retrieval, and an MCP server. Week 4 wraps that library in a FastAPI service with streaming, tracing, and a cost cap, then deploys it. Keeping the agent logic out of the web layer is deliberate. It is what lets you test it, eval it, and reuse it from MCP and from FastAPI without duplication.

## Your stack

You run this on hardware you own, at essentially zero cost.

| Layer | What | Role |
|---|---|---|
| Models, default | vLLM on your RTX 5060 Ti, 16 GB | Unlimited local iteration. Every build day and every eval run |
| Models, hosted backup | Cerebras, Groq | Speed, failover, and a second opinion for the day 13 comparison |
| Models, paid, 40 USD credit | Anthropic | Four jobs only: the eval judge, the caching lesson, the capability ceiling, the live demo |
| Embeddings and reranking | sentence-transformers, local | Free, and fast on the GPU |
| Workstation | MacBook Air M1 | Your code, FastAPI, the RAG index, Claude Code |
| Coding assistant | Claude Code, covered by Claude Pro | Separate from the model your agent calls |

One client file speaks to all of them through the OpenAI-compatible Chat Completions format. Switching providers is one environment variable, and nothing downstream changes. That abstraction is itself a portfolio line in week 4.

**The day files show Anthropic SDK code**, because it is the clearest surface for teaching the concepts. `FREE-PROVIDER-GUIDE.md` lists every place your stack differs, day by day, and carries the provider-agnostic client to copy into the project.

Three lessons are **better** on your hardware than on a paid API. Prompt caching, because vLLM reports hit rates you can watch move. Structured output, because grammar constrained decoding makes invalid JSON impossible. And evals, because unlimited local runs let you measure a noise floor and compare four model tiers, which paid teams skip to protect their bill.

**Read `FREE-PROVIDER-GUIDE.md` next, then `02-setup.md`.**
