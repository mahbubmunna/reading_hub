# Week 2: Memory, Context, and Evals

> **Stack note.** Day files show Anthropic SDK code. Your stack differs on days 8 and 11 to 14. See `FREE-PROVIDER-GUIDE.md`. The judge runs on Anthropic credit; everything else runs local and unlimited, so run the baseline three times.

## Goal

Two skills that separate hobby agents from hirable engineers. First, controlling what the model sees: a token budget, trimming, summarization, and a store that survives restarts. Second, measuring: an eval harness that tells you, with numbers, whether a change helped.

## Why this week matters most for a job

Anyone can call an API. The interview question is "how do you know your agent got better after you changed the prompt?" If the answer is "I tried it a few times", the interview is over. If the answer is "pass rate went from 63 to 81 percent on 30 tasks, cost per task dropped 12 percent, here is the chart", you are hired.

## The deliverable

1. `memory/` with a context budget, trimming, summarization, and SQLite persistence, all used by `agent.py`.
2. `evals/` with a 30 task dataset, a runner, exact match and LLM judge scorers, and a report.
3. A before and after experiment: one prompt change, two eval runs, one chart, a short writeup with the numbers.

## Days

| Day | File | You will have |
|---|---|---|
| 8 | day-08-context-budget.md | Token counting and trimming in the loop |
| 9 | day-09-summarization-memory.md | Old turns compressed into a running summary |
| 10 | day-10-sqlite-memory.md | Memory that survives restarts, per user |
| 11 | day-11-eval-dataset.md | 30 tasks with expected outcomes |
| 12 | day-12-runner-and-judge.md | Runner, scorers, LLM judge, report |
| 13 | day-13-before-and-after.md | The experiment, with numbers |
| 14 | day-14-review.md | Chart, writeup, review |

## Checklist

- [ ] The agent never sends more than the budget, and I can prove it from the usage lines
- [ ] Summaries preserve facts the tests need
- [ ] Memory is per user and per session, and I can restart the process and continue
- [ ] Dataset has 30 tasks, each with an expected outcome and a scoring method
- [ ] The judge has a rubric and I checked it against 10 human scored examples
- [ ] Report shows pass rate, mean cost, p50 and p95 latency
- [ ] One chart, one writeup, committed

## Sticky note questions

- Day 8: What does the model actually need to see to answer the next turn?
- Day 9: What gets lost in a summary, and does it matter?
- Day 10: What should an agent remember about a person across weeks?
- Day 11: What does "correct" mean for my agent?
- Day 12: Where would a judge be wrong?
- Day 13: If pass rate went up, what else could have gone down?
- Day 14: What did I not understand this week?
