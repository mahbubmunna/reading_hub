# Day 6: The Coding Agent

**Goal:** the week 1 deliverable. An agent that takes a repo with a failing test and makes it pass, using only the tools you wrote.

## Paper first (20 minutes)

You are the agent. A repo has a failing test. Write the exact sequence of tool calls you would make. Most people write: list files, run tests, read the failing test, read the code under test, write the fix, run tests. That is the plan. Now write it as a system prompt.

## Concepts

**The system prompt is the agent's procedure.** For a coding agent it should say: orient first, reproduce the failure, read before editing, make the smallest change, verify, then stop. Agents that skip "reproduce first" guess.

**Give the agent a definition of done.** "Stop when `pytest` exits 0" is far better than "fix the bug". The loop stops on `end_turn`, so the model must know when to say it is done.

**Observe, do not steer.** When the agent does something dumb, do not fix the code yourself. Improve the prompt or the tool and rerun. That is the job.

## Step 1: a repo with a failing test

Create `sample_repo/`:

```bash
mkdir -p sample_repo/tests
cat > sample_repo/causelist.py <<'P'
from dataclasses import dataclass


@dataclass
class Case:
    number: str
    court: int
    urgent: bool


def sort_cases(cases: list[Case]) -> list[Case]:
    """Sort by court number ascending. Within a court, urgent cases first."""
    return sorted(cases, key=lambda c: (c.court, c.urgent))


def total_fee(amounts: list[float], rate: float = 0.15, fixed: float = 300) -> float:
    return sum(a * rate for a in amounts) + fixed
P
cat > sample_repo/tests/test_causelist.py <<'P'
from causelist import Case, sort_cases, total_fee


def test_urgent_first_within_court():
    cases = [Case("A", 7, False), Case("B", 7, True), Case("C", 3, False)]
    out = sort_cases(cases)
    assert [c.number for c in out] == ["C", "B", "A"]


def test_total_fee_fixed_per_case():
    assert total_fee([1000, 1000]) == 900  # 150 + 150 + 300 + 300
P
cat > sample_repo/pyproject.toml <<'P'
[project]
name = "sample"
version = "0.1"
dependencies = ["pytest"]
P
cd sample_repo && uv sync && uv run pytest -q; cd ..
```

Both tests fail. Two bugs: urgent sorts last, and the fixed fee is applied once instead of per case.

## Step 2: the coding agent

Create `coding_agent.py`:

```python
import sys
from agent import Agent
from toolkit import build_toolkit
from llm import spend

SYSTEM = """You are a senior Python engineer fixing a bug in a small repository.

Procedure, in order:
1. list_files to orient yourself.
2. Run the tests with shell: `uv run pytest -q`. Read the failure carefully.
3. read_file the failing test and the code under test. Never edit a file you have not read.
4. Make the smallest change that fixes the failure. Write the complete file with write_file.
5. Run the tests again.
6. If tests pass, reply with a two line summary of what was wrong and what you changed, then stop.
   If tests still fail, go back to step 3. Do not repeat the same edit twice.

Rules: do not modify tests. Do not install packages. Do not touch files outside the repo."""


def main(repo: str) -> None:
    agent = Agent(system=SYSTEM, tools=build_toolkit(repo), max_steps=15)
    res = agent.run("The test suite is failing. Fix the code so all tests pass.")
    print("\n==== RESULT ====")
    print(res.text)
    print("stopped:", res.stopped_because, "steps:", res.steps)
    print(spend.report())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sample_repo")
```

```bash
uv run python coding_agent.py sample_repo
cd sample_repo && uv run pytest -q; cd ..
```

## Step 3: watch three runs

Run it three times, resetting the repo between runs:

```bash
cd sample_repo && git checkout . 2>/dev/null || true; cd ..
```

If the repo is not a git repo, recreate the buggy file from step 1 each time. Record for each run: steps, cost, and whether it fixed both bugs. Agents are not deterministic. Three runs tell you more than one.

## Step 4: make it worse, then better

1. Remove step 2 from the system prompt. Does the agent still reproduce first? Note the difference.
2. Remove the line numbers from `read_file`. Does edit quality drop?
3. Set `max_steps=5`. Does it finish?

Put everything back. Each of these is a lesson you will quote in the post tomorrow.

## Step 5: harder bug

Add a third test that requires reading two files to fix. Watch whether the agent finds it. If it gets stuck, improve the prompt, not the code.

## Exercise, without AI

Write on paper the five most important lines of your system prompt and why each is there.

## Check yourself

1. Why should the agent run tests before reading code?
2. Why "write the complete file" rather than a diff? What would a diff based edit tool need?
3. What does the agent do when it hits `max_steps` mid edit? Is the repo left broken?
4. How would you make the agent's runs more consistent?

## Common mistakes

- Fixing the bug yourself when the agent fails. The point is the agent.
- A system prompt with no stop condition, so the agent keeps "verifying".
- Not resetting the repo between runs, then thinking run 2 was faster.

## Done when

- The agent fixes both bugs in under 15 steps on at least two of three runs.
- You recorded steps and cost for each run.
- You tried the three "make it worse" changes and wrote what happened.
- Sticky note for tomorrow: "What did I not understand this week?"
