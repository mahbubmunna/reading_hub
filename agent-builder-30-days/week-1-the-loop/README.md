# Week 1: The Loop, By Hand

## Goal

Understand, at the level of individual API calls, what an agent is. By Sunday you will have written every piece of an agent loop yourself with no framework, and you will be able to explain it in two minutes without notes.

## Why no frameworks this week

LangChain, CrewAI, LlamaIndex, and smolagents all hide the same three lines of logic. If you learn the framework first, you learn its vocabulary and never see the mechanism. You forgot the smolagents course because you learned the wrapper, not the thing inside. This week you write the thing inside. You will never forget it again, because you will have built it.

## The deliverable

A coding agent, `agent.py`, that:

1. Takes a path to a small repo with one failing test.
2. Reads files, runs the tests, edits code, reruns the tests.
3. Stops when the tests pass or after a maximum number of steps.
4. Prints total tokens and cost.

Plus a 500 word post: "How an agent loop works", written from your notes, published on GitHub, dev.to, or your own site.

## Days

| Day | File | You will have |
|---|---|---|
| 1 | day-01-first-call.md | A client wrapper that streams and prints cost |
| 2 | day-02-structured-output-and-caching.md | Pydantic output, cache hits verified |
| 3 | day-03-first-tool.md | One tool, one manual round trip |
| 4 | day-04-the-loop.md | The loop, max steps, stop condition |
| 5 | day-05-five-tools.md | read, write, shell, fetch, calculator, with safety |
| 6 | day-06-coding-agent.md | The deliverable running |
| 7 | day-07-review-and-post.md | The post, the recording, the weekly review |

## Checklist

- [ ] `llm.py` prints input tokens, output tokens, cache reads, and cost for every call
- [ ] I can explain why `tool_result` must be a user message
- [ ] The loop stops on `end_turn`, on max steps, and on a tool error budget
- [ ] Tool errors go back to the model as `is_error: true`, never crash the loop
- [ ] The coding agent fixes the failing test in under 15 steps
- [ ] The post is published
- [ ] Sunday review done in `templates/weekly-review.md`

## Sticky note questions for the walks

- Day 1: What is the smallest thing an agent needs to be an agent?
- Day 2: Why would the same prompt cost less the second time?
- Day 3: Who decides when a tool is called, me or the model?
- Day 4: When should a loop stop?
- Day 5: What is the worst thing a shell tool could do?
- Day 6: What does the agent need to see to fix a bug?
- Day 7: What did I not understand this week?
