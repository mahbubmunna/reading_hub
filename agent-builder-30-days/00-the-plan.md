# The 30 Day Plan

Print this. Tick each deliverable when it exists and runs.

**Stack:** vLLM on your GPU by default, Cerebras and Groq as backup, 40 USD of Anthropic credit reserved for four specific jobs. Setup in `02-setup.md`, day-by-day differences in `FREE-PROVIDER-GUIDE.md`. Nothing in this plan changes based on provider.

## Week 1: the loop, by hand (days 1 to 7)

Raw chat completions, no frameworks. Streaming, structured output, prompt caching. Then your own agent loop with five hand written tools, retries, max steps, and a stop condition.

**Deliverable:** a coding agent that fixes a failing test in a small repo, plus a 500 word post explaining how the loop works.

- [ ] Day 1: first API call, streaming, token usage printed, three providers answering
- [ ] Day 2: grammar constrained JSON, cache hit rate moved on vLLM, cache read tokens seen on Anthropic
- [ ] Day 3: first tool call, manual round trip, vLLM tool parser verified
- [ ] Day 4: the loop with max steps and a stop condition
- [ ] Day 5: five tools, safety limits, error results
- [ ] Day 6: the coding agent fixes a failing test
- [ ] Day 7: review, write the post, record the explanation

## Week 2: memory, context, and evals (days 8 to 14)

Conversation trimming, summarization, SQLite memory, a token budget. Then an eval harness: 30 tasks, runner, scorer, report with pass rate, cost, latency.

**Deliverable:** your agent measured before and after one prompt change, with a noise floor from three baseline runs, plus a capability table across four model tiers.

- [ ] Day 8: token budget and trimming
- [ ] Day 9: summarization memory
- [ ] Day 10: SQLite long term memory
- [ ] Day 11: eval dataset of 30 tasks
- [ ] Day 12: runner, scorers, an independent judge on Anthropic, concurrent runner
- [ ] Day 13: before and after, three baseline runs for the noise floor, four tier capability table
- [ ] Day 14: review, chart, writeup

Unlimited local runs are the advantage here. Run the baseline three times before changing anything, so your noise floor is measured rather than guessed. Paid teams skip that step to protect their bill.

## Week 3: RAG and MCP on a real project (days 15 to 21)

Rebuild a knowledge base from one of your real projects with chunking, hybrid search, reranking, citations. Measure retrieval recall separately. Build an MCP server exposing three tools and connect it to Claude Code.

**Deliverable:** MCP server on GitHub with README and tests, plus retrieval recall improving across three iterations.

- [ ] Day 15: chunking and embeddings
- [ ] Day 16: hybrid search and reranking
- [ ] Day 17: retrieval evals, three iterations
- [ ] Day 18: MCP server with three tools
- [ ] Day 19: tests and tool description design
- [ ] Day 20: connect to Claude Code and your own agent
- [ ] Day 21: review and publish

## Week 4: ship and show (days 22 to 30)

FastAPI, tracing, cost cap, adversarial inputs, Docker, live URL. Then the portfolio.

**Deliverable:** a link you can send to a recruiter.

- [ ] Day 22: FastAPI with streaming
- [ ] Day 23: tracing, call caps, shadow cost dashboard
- [ ] Day 24: 20 adversarial inputs survived
- [ ] Day 25: Docker, deploy against a hosted provider, provider failover
- [ ] Day 26: portfolio repo and architecture diagram
- [ ] Day 27: demo video and failure writeup
- [ ] Day 28 to 30: review, apply, plan month two

## The five artefacts that get you hired

Everything above produces these. If a week slips, protect these first.

1. **The loop, written by hand**, with the post explaining it. Week 1.
2. **An eval harness with a measured noise floor** and an independent judge. Week 2.
3. **The four tier capability table**, on your own tasks. Day 13. Almost no applicant has this.
4. **Retrieval measured separately from generation**, three iterations. Week 3.
5. **A live URL with tracing, caps, and 20 adversarial cases survived**, plus the failure writeup. Week 4.

## Imagination, every day

- Morning walk with nothing in your ears, one question in your head.
- Three ideas a night in `templates/idea-log.md`.
- One constraint prototype per week, two hours max. See `01-imagination-practice.md`.
- Twenty minutes of reading outside the field, four nights a week, paper book in bed.
- One "steal from another domain" note per week.
- Two minute spoken recap daily.
- Once a week ask: what would make this project embarrassing in two years?

## Body, every day

- Asleep by 1 to 2am this month, moving 30 minutes earlier every three days.
- Outside within an hour of waking.
- Walk 30 minutes daily. Strength 20 minutes, three days a week.
- Caffeine before 1pm only.
- D3 daily. Creatine 3 to 5 g daily. Magnesium glycinate in the evening.
