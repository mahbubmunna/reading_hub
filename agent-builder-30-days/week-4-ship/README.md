# Week 4: Ship and Show

## Goal

Everything you built becomes a running service with a URL, and a portfolio a recruiter can read in five minutes. This week is FastAPI, tracing, cost control, safety, Docker, deployment, and presentation.

## The deliverable

A link you can send to a recruiter, containing:

1. A live clinic receptionist agent at a URL, streaming, with a status page and cost dashboard.
2. A GitHub repo with an architecture diagram, eval results, retrieval results, and the MCP server.
3. A three minute demo video.
4. A writeup of what broke and how you fixed it.

## Days

| Day | File | You will have |
|---|---|---|
| 22 | day-22-fastapi.md | Agent behind FastAPI, streaming responses, sessions |
| 23 | day-23-tracing-and-cost.md | Every step traced, a cost cap, a dashboard |
| 24 | day-24-adversarial.md | 20 attacks survived, guardrails, approval gate |
| 25 | day-25-docker-and-deploy.md | Container, live URL, health check |
| 26 | day-26-portfolio-repo.md | Clean repo, architecture diagram, README |
| 27 | day-27-demo-and-writeup.md | Video, failure writeup, applications ready |
| 28 to 30 | day-28-30-review-and-next.md | Interview prep, applications, month two plan |

## Checklist

- [ ] `POST /chat` streams tokens and tool events as server sent events
- [ ] Sessions persist across requests via the week 2 store
- [ ] Every request has a trace id and every step is a span
- [ ] A daily cost cap stops the agent cleanly with a clear message
- [ ] All 20 adversarial inputs handled: no leaked system prompt, no unauthorized booking, no crash
- [ ] Writes require confirmation from the user
- [ ] Container builds in one command and runs locally
- [ ] Live URL responds, health endpoint green
- [ ] README with diagram, numbers, and links
- [ ] Demo video under three minutes
- [ ] Ten applications sent by day 30

## Sticky note questions

- Day 22: What must the web layer never know about the agent?
- Day 23: If a user complains, what do I need to see?
- Day 24: How would I attack my own agent?
- Day 25: What is different about running this on someone else's machine?
- Day 26: What does a recruiter look at first?
- Day 27: What broke that I am proud of fixing?
- Day 28: What would I build next, and why?
