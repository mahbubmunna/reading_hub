# Agent Builder in 30 Days

A step by step course for one intense month. Goal: by day 30 you can build, evaluate, and ship an LLM agent, and you have a portfolio link that proves it.

This is written as a personal instructor would write it. It tells you what to do each day, why it matters, what to type, what to check, and when you are done. Do not read ahead. Do today's file, finish today's "Done when", then stop.

## How to use this folder

```
agent-builder-30-days/
  README.md                     <- you are here, read once
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

## Cost: run this for free

The day files are written against the Anthropic API because it is the clearest teaching surface. You do not have to use it, and you should not spend money on it.

**Read `FREE-PROVIDER-GUIDE.md` before `02-setup.md`.** It gives you a provider-agnostic client that runs the entire course on your own GPU plus free hosted tiers, at zero cost, and lists every place a day file differs. Your Claude Pro subscription already covers Claude Code as your coding assistant, which is a separate thing from the model your agent calls.

The two paths:

| | Setup | Cost |
|---|---|---|
| **Free (recommended)** | `FREE-PROVIDER-GUIDE.md` then `02-setup.md` | Zero |
| Anthropic API | `02-setup.md` as written | About 20 to 60 USD for the month |

Start with `FREE-PROVIDER-GUIDE.md`.
