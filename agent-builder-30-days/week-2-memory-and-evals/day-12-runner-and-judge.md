# Day 12: Runner, Scorers, Judge, Report

**Goal:** run all 30 tasks, score them, and produce a report with pass rate, cost, and latency. Plus an LLM judge that you have checked against your own judgement.

## Paper first (20 minutes)

Draw the runner. For each task: reset fixture, run agent, score, record. What do you record? At minimum: pass or fail, steps, tokens, cost, seconds, stop reason. What do you do when the agent crashes? It must count as a fail, not stop the run.

## Concepts

**Reset before every run.** Agents mutate state. Copy the fixture to a temp folder each time.

**Record everything, aggregate later.** Save one JSON line per task run. Reports are computed from those lines. You will rerun reports without rerunning agents.

**Judges are biased.** They prefer longer answers, they prefer the first option shown, they are lenient with confident wording. You reduce this with a tight rubric, a fixed output schema, and by checking the judge against ten human scored examples before trusting it.

**Report the spread, not just the mean.** p50 and p95 latency. Pass rate per tag. Variance across the three variants.

## Step 1: scorers

Create `evals/scorers.py`:

```python
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from pydantic import BaseModel
from llm import client, spend

JUDGE_MODEL = "claude-opus-5"


def tests_pass(repo: str, original_tests: dict[str, str]) -> tuple[bool, str]:
    # adversarial guard: tests must be unchanged
    for rel, content in original_tests.items():
        if (Path(repo) / rel).read_text() != content:
            return False, "tests modified"
    r = subprocess.run(["uv", "run", "pytest", "-q"], cwd=repo, capture_output=True, text=True, timeout=120)
    return r.returncode == 0, r.stdout[-300:]


def contains(output: str, expected: str) -> tuple[bool, str]:
    return expected.lower() in output.lower(), ""


def regex(output: str, pattern: str) -> tuple[bool, str]:
    return re.search(pattern, output) is not None, ""


class Verdict(BaseModel):
    reasoning: str
    score: int  # 0 or 1


def judge(output: str, rubric: str, task_prompt: str) -> tuple[bool, str]:
    resp = client.messages.parse(
        model=JUDGE_MODEL,
        max_tokens=800,
        system=(
            "You are a strict grader. Apply the rubric literally. Do not reward length or confidence. "
            "Score 1 only if the rubric is fully satisfied, else 0. Reason briefly first."
        ),
        messages=[{"role": "user", "content":
            f"Task given to the agent:\n{task_prompt}\n\nRubric:\n{rubric}\n\nAgent output:\n{output}"}],
        output_format=Verdict,
    )
    spend.add(resp.usage, JUDGE_MODEL)
    v = resp.parsed_output
    return v.score == 1, v.reasoning
```

## Step 2: the runner

Create `evals/run.py`:

```python
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

from agent import Agent
from toolkit import build_toolkit
from evals.tasks import TASKS
from evals import scorers
from llm import spend, Spend
import llm

SYSTEM_PATH = Path("evals/system_prompt.txt")


def run_task(task, system: str) -> dict:
    tmp = tempfile.mkdtemp(prefix="eval_")
    repo = Path(tmp) / "repo"
    shutil.copytree(task.setup["repo"], repo)
    originals = {str(p.relative_to(repo)): p.read_text() for p in (repo / "tests").glob("*.py")}

    before = Spend(); before.__dict__.update(spend.__dict__)
    t0 = time.time()
    try:
        agent = Agent(system=system, tools=build_toolkit(str(repo)), max_steps=15,
                      budget_tokens=30_000, verbose=False)
        res = agent.run(task.prompt)
        text, steps, stopped = res.text, res.steps, res.stopped_because
        crashed = None
    except Exception as e:
        text, steps, stopped, crashed = "", 0, "crash", f"{type(e).__name__}: {e}"
    secs = time.time() - t0

    if task.scorer == "tests_pass":
        ok, detail = scorers.tests_pass(str(repo), originals)
    elif task.scorer == "judge":
        ok, detail = scorers.judge(text, task.rubric, task.prompt)
    elif task.scorer == "contains":
        ok, detail = scorers.contains(text, task.expected)
    else:
        ok, detail = scorers.regex(text, task.expected)

    cost = spend.total_cost(llm.MODEL) - before.total_cost(llm.MODEL)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"task": task.id, "tags": task.tags, "pass": ok, "detail": detail, "steps": steps,
            "stopped": stopped, "seconds": round(secs, 1), "cost": round(cost, 4),
            "crashed": crashed, "output": text[:500]}


def main(run_name: str) -> None:
    system = SYSTEM_PATH.read_text()
    out = Path(f"evals/results/{run_name}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for i, task in enumerate(TASKS, 1):
            r = run_task(task, system)
            f.write(json.dumps(r) + "\n"); f.flush()
            print(f"[{i}/{len(TASKS)}] {task.id:28s} {'PASS' if r['pass'] else 'fail'} "
                  f"steps={r['steps']} ${r['cost']:.3f} {r['seconds']}s")
    print(spend.report())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "baseline")
```

Put your day 6 system prompt in `evals/system_prompt.txt`.

## Step 3: the report

Create `evals/report.py`:

```python
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def load(name):
    return [json.loads(l) for l in Path(f"evals/results/{name}.jsonl").read_text().splitlines()]


def summarize(rows):
    n = len(rows)
    passed = sum(r["pass"] for r in rows)
    secs = sorted(r["seconds"] for r in rows)
    p = lambda q: secs[min(n - 1, int(q * n))]
    by_tag = defaultdict(list)
    for r in rows:
        for t in r["tags"]:
            by_tag[t].append(r["pass"])
    return {
        "n": n, "pass_rate": round(passed / n, 3),
        "mean_cost": round(statistics.mean(r["cost"] for r in rows), 4),
        "total_cost": round(sum(r["cost"] for r in rows), 3),
        "p50_s": p(0.5), "p95_s": p(0.95),
        "mean_steps": round(statistics.mean(r["steps"] for r in rows), 1),
        "crashes": sum(1 for r in rows if r["crashed"]),
        "by_tag": {t: round(sum(v) / len(v), 2) for t, v in sorted(by_tag.items())},
    }


if __name__ == "__main__":
    for name in sys.argv[1:]:
        print(name, json.dumps(summarize(load(name)), indent=2))
```

## Step 4: run the baseline

```bash
uv run python evals/run.py baseline
uv run python evals/report.py baseline
```

Thirty tasks at up to 15 steps each is real money. Watch the running cost. If it is heading above a few dollars, stop and lower `max_steps` or `budget_tokens`. Write the baseline numbers in your log. Do not tune anything yet.

## Step 5: check the judge against yourself

Take the five judge tasks. Run them. Score each yourself, blind, before looking at the judge's score. Agreement out of five goes in the log. Below four out of five means the rubric is loose. Tighten it and rerun. Try also swapping the judge to `claude-haiku-4-5` and see whether agreement drops. Now you have a defensible answer to "how do you know your judge is right".

## Exercise, without AI

Write three ways a judge could be fooled by an agent's output, and one rubric line that defends against each.

## Check yourself

1. Why record raw rows and compute the report separately?
2. Why p95 and not just the mean?
3. What does per tag pass rate tell you that the overall rate hides?
4. What is the judge's most likely bias on your tasks?

## Common mistakes

- Running tasks in the fixture folder instead of a copy.
- Letting one crash stop the whole run.
- Trusting the judge without checking it.

## Done when

- `baseline.jsonl` and its report exist.
- Judge agreement with you is recorded.
- Notes: "Eval harness" and "LLM judge and its biases".
- Sticky note: "If pass rate went up, what else could have gone down?"
