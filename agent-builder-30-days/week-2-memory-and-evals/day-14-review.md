# Day 14: Chart, Writeup, Review

**Goal:** turn the week into a portfolio piece and consolidate what you learned.

## Block 1: the chart and writeup (90 minutes)

**Chart.** One bar chart, pass rate per run, and a second small chart of cost per run. Use matplotlib, save to `evals/results/summary.png`.

```python
import matplotlib.pyplot as plt
from evals.report import load, summarize

runs = ["baseline", "v2", "sonnet"]
stats = {r: summarize(load(r)) for r in runs}
fig, ax = plt.subplots(1, 2, figsize=(9, 3.5))
ax[0].bar(runs, [stats[r]["pass_rate"] for r in runs]); ax[0].set_title("Pass rate"); ax[0].set_ylim(0, 1)
ax[1].bar(runs, [stats[r]["mean_cost"] for r in runs]); ax[1].set_title("Mean cost per task (USD)")
plt.tight_layout(); plt.savefig("evals/results/summary.png", dpi=150)
```

**Writeup.** `evals/README.md`, 400 to 600 words:

1. What the agent does and what the tasks are. Include the tag mix.
2. How scoring works, including the judge and the agreement check.
3. The table from yesterday and the chart.
4. What the one change was and why you thought it would help.
5. What actually happened, with the flip analysis.
6. The noise floor and what that means for the claim.
7. What you would try next.

Be honest. A writeup that says "the change did not help and here is why" is more impressive than a fake win.

## Block 2: the repo (60 minutes)

- Move eval results and the chart into the repo. Commit.
- Update the main README: link to the evals README and the week 1 post.
- Tag the commit `week-2`.

## Block 3: the review (45 minutes)

Fill in `notes/weekly-review.md`. Then the ten questions, out loud:

1. What is a context budget and how does your loop enforce it?
2. Why must a tool use and its result stay together when trimming?
3. What goes in a structured summary for your agent?
4. Where does the summary live in the request and why?
5. What are the three memory scopes?
6. Why explicit remember and recall tools?
7. What are the three kinds of scoring?
8. How did you check the judge?
9. What was your noise floor?
10. What did your one change do, and what did it cost?

## Constraint prototype (weekend, 2 hours max)

**An agent that may only ask questions.** It never answers. Give it a real problem from your day. See whether its questions alone get you to a solution. Ten lines afterward.

## The record

Two minutes: "How I know my agent got better." Numbers included. Listen back. Keep the second take.

## Body check

Bedtime should now be an hour earlier than day 1. Walks: how many of seven? Strength: how many of three? Slips? Write it down. No judgement, just data.

## Done when

- Chart and writeup committed.
- Ten for ten out loud, or Monday revision block.
- Prototype done.
- Recording kept.
- Weekly review filled.
