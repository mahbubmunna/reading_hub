# Day 13: The Before and After Experiment

**Goal:** change one thing, measure, and be able to say whether it helped. This is the core skill of applied AI engineering, and the piece of your portfolio a hiring manager will read twice.

## Paper first (20 minutes)

Look at the baseline report. Which tag failed most? Read the failed outputs. Write three hypotheses about why. Pick the one you can test with a single prompt change. Write the change on paper before touching the file.

## Concepts

**One variable.** Change the prompt, or the tool description, or the budget, or the model. Not two. If you change two and it improves, you learned nothing about either.

**Same tasks, same settings, same model.** The only difference between the two runs is your change.

**Variance is real.** Agents are not deterministic. That is why you have three variants of each bug. If the change moves pass rate by two points, that is noise. If it moves ten points and the per tag pattern makes sense, that is signal. For a serious claim you would run each condition three times. Do that if budget allows.

**Watch the second metric.** Pass rate up, cost up 40 percent is a trade, not a win. Always report both.

## Step 1: the change

Copy `evals/system_prompt.txt` to `evals/system_prompt_v2.txt`. Make your one change. Good candidates from typical baselines:

- Add "Before editing, state in one line what you believe the bug is." Forces diagnosis.
- Add "After writing a file, run the tests immediately." Reduces stacked edits.
- Add explicit "do not modify tests" if the adversarial fixtures caught it.
- Improve a tool description, for example telling `write_file` to keep existing functions.

Change `SYSTEM_PATH` handling in `run.py` to accept the prompt file as a second argument.

## Step 2: run

```bash
uv run python evals/run.py v2 evals/system_prompt_v2.txt
uv run python evals/report.py baseline v2
```

## Step 3: read the diff, not the number

For every task that flipped, fail to pass or pass to fail, read both outputs. Write one line per flip: what changed in the agent's behaviour. This is where the understanding lives, not in the pass rate.

## Step 4: the variance check

If budget allows, rerun the baseline as `baseline_2`. Compare `baseline` with `baseline_2`. That gap is your noise floor. Any improvement smaller than it is not a result.

## Step 5: a second experiment, different variable

Try one of: `claude-sonnet-5` as the model, `budget_tokens` halved, `max_steps` cut to 8. One only. Report pass rate and cost. You now have a small table:

| Run | Pass rate | Mean cost | p95 s | Note |
|---|---|---|---|---|
| baseline | | | | |
| v2 prompt | | | | |
| sonnet | | | | |

Fill it in. That table goes in tomorrow's writeup.

## Exercise, without AI

Write the paragraph you would say in an interview about this experiment. Include the numbers, the noise floor, and what you would try next.

## Check yourself

1. Why one variable?
2. What is your noise floor, and how did you measure it?
3. Which tag improved most, and why do you think so?
4. Did anything get worse?

## Common mistakes

- Changing the prompt and the tools together.
- Celebrating a three point move.
- Only reporting the metric that went up.

## Done when

- At least two additional runs exist beyond baseline.
- The table is filled.
- Flip analysis written, one line per flipped task.
- Sticky note: "What did I not understand this week?"
