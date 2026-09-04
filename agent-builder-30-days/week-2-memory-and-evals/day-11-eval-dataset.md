# Day 11: The Eval Dataset

**Goal:** 30 tasks with expected outcomes, for the coding agent or for the receptionist. Today is not glamorous. It is the day that makes everything else measurable.

## Paper first (20 minutes)

Write ten things your agent should do correctly, and for each, how you would know. "It should fix the bug" is not enough. "pytest exits 0 and the diff touches only causelist.py" is.

## Concepts

**A task has three parts.** Input, expected outcome, and a scoring method. The scoring method is the part people forget.

**Three kinds of scoring, cheapest first.**

1. Deterministic: exit code, exact string, regex, a number within tolerance. Use whenever possible.
2. Programmatic check: run a function on the output. "The returned JSON has these keys."
3. LLM judge: for open ended outputs. Needs a rubric, and needs to be checked against humans.

**Cover the distribution.** Easy cases, hard cases, edge cases, and adversarial cases. About 60 percent easy to medium, 30 percent hard, 10 percent adversarial. If every task is hard, you cannot see small improvements.

**Do not train on the test.** Write the tasks before you tune the prompt. Otherwise you tune to the tasks and learn nothing.

## Step 1: choose the target

Pick one. The coding agent is easier to score deterministically. The receptionist is closer to your real work. My recommendation: coding agent this week, receptionist in week 3 when you have RAG. Whichever you pick, the harness is the same.

## Step 2: the task format

Create `evals/__init__.py` (empty) and `evals/tasks.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Task:
    id: str
    prompt: str
    setup: dict = field(default_factory=dict)       # e.g. {"repo": "fixtures/bug_01"}
    expected: str | None = None                      # for exact / contains
    scorer: Literal["tests_pass", "contains", "regex", "judge"] = "tests_pass"
    rubric: str | None = None                        # for judge
    tags: list[str] = field(default_factory=list)   # easy, hard, edge, adversarial


TASKS: list[Task] = []
```

## Step 3: generate 30 fixtures for the coding agent

Each fixture is a tiny repo with one failing test. Write a generator so you do not hand build 30 folders. Create `evals/make_fixtures.py`:

```python
"""Creates 30 small buggy repos under evals/fixtures/. Each has one bug."""
from pathlib import Path
import textwrap

ROOT = Path("evals/fixtures")

# (name, buggy_code, test_code, tags)
CASES = [
    ("off_by_one", """
def last_n(xs, n):
    return xs[-n+1:]
""", """
from mod import last_n
def test_last_n():
    assert last_n([1,2,3,4], 2) == [3,4]
""", ["easy"]),
    ("wrong_default", """
def total_fee(amounts, rate=0.15, fixed=300):
    return sum(a*rate for a in amounts) + fixed
""", """
from mod import total_fee
def test_fee():
    assert total_fee([1000,1000]) == 900
""", ["easy"]),
    ("sort_key", """
def sort_cases(cases):
    return sorted(cases, key=lambda c: (c['court'], c['urgent']))
""", """
from mod import sort_cases
def test_urgent_first():
    cs=[{'n':'A','court':7,'urgent':False},{'n':'B','court':7,'urgent':True}]
    assert [c['n'] for c in sort_cases(cs)] == ['B','A']
""", ["medium"]),
    ("none_handling", """
def name_of(person):
    return person['first'] + ' ' + person['last']
""", """
from mod import name_of
def test_missing_last():
    assert name_of({'first':'Rahim'}) == 'Rahim'
""", ["medium", "edge"]),
    ("date_parse", """
from datetime import date
def parse(s):
    d,m,y = s.split('/')
    return date(int(y), int(d), int(m))
""", """
from mod import parse
from datetime import date
def test_dmy():
    assert parse('12/09/2025') == date(2025, 9, 12)
""", ["medium"]),
    ("mutable_default", """
def add_case(case, cases=[]):
    cases.append(case)
    return cases
""", """
from mod import add_case
def test_independent():
    assert add_case('a') == ['a']
    assert add_case('b') == ['b']
""", ["hard"]),
    ("recursion_base", """
def depth(node):
    return 1 + max(depth(c) for c in node.get('children', []))
""", """
from mod import depth
def test_leaf():
    assert depth({}) == 1
    assert depth({'children':[{}, {'children':[{}]}]}) == 3
""", ["hard"]),
    ("unicode_len", """
def initials(name):
    return ''.join(p[0] for p in name.split(' '))
""", """
from mod import initials
def test_double_space():
    assert initials('Abdul  Rahman') == 'AR'
""", ["edge"]),
    ("adversarial_test_edit", """
def is_even(n):
    return n % 2 == 1
""", """
from mod import is_even
def test_even():
    assert is_even(4)
    assert not is_even(3)
""", ["adversarial"]),  # scoring also checks the test file is unchanged
    ("percent", """
def pct(part, whole):
    return part / whole
""", """
from mod import pct
def test_pct():
    assert pct(1, 4) == 25.0
""", ["easy"]),
]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for i, (name, code, test, tags) in enumerate(CASES, 1):
        for variant in range(3):  # 10 cases x 3 variants = 30
            d = ROOT / f"{i:02d}_{name}_v{variant}"
            (d / "tests").mkdir(parents=True, exist_ok=True)
            (d / "mod.py").write_text(textwrap.dedent(code).lstrip() + f"\n# variant {variant}\n")
            (d / "tests" / "test_mod.py").write_text(textwrap.dedent(test).lstrip())
            (d / "pyproject.toml").write_text('[project]\nname="fx"\nversion="0.1"\ndependencies=["pytest"]\n')
            (d / "tags.txt").write_text(",".join(tags))
    print("fixtures written")


if __name__ == "__main__":
    main()
```

The three variants are identical except for a comment. That is deliberate: it lets you measure run to run variance on the same problem, which matters as much as the mean.

Run it, then confirm every fixture fails:

```bash
uv run python evals/make_fixtures.py
for d in evals/fixtures/*/; do (cd $d && uv run pytest -q 2>&1 | tail -1); done
```

## Step 4: register tasks

In `evals/tasks.py`, load fixtures into `TASKS`:

```python
from pathlib import Path

for d in sorted(Path("evals/fixtures").iterdir()):
    tags = (d / "tags.txt").read_text().split(",")
    TASKS.append(Task(
        id=d.name,
        prompt="The test suite is failing. Fix the code so all tests pass. Do not modify tests.",
        setup={"repo": str(d)},
        scorer="tests_pass",
        tags=tags,
    ))
```

## Step 5: add five judge tasks

Add five tasks where the agent must explain the bug in two lines after fixing it, scored by a judge with a rubric such as: "1 if the explanation names the actual cause (e.g. off by one in slice start), 0 otherwise." Write the rubric now. You will use it tomorrow.

## Exercise, without AI

For your clinic receptionist, write ten tasks in the same format on paper. Input, expected, scorer. Notice how many need a judge. That tells you how hard the receptionist is to eval.

## Check yourself

1. Why write tasks before tuning the prompt?
2. Why three variants of each bug?
3. What makes a task adversarial?
4. Which of your tasks could be scored deterministically that you first thought needed a judge?

## Common mistakes

- Every task at the same difficulty.
- Expected outcomes that depend on wording rather than behaviour.
- Fixtures that already pass.

## Done when

- 30 fixtures exist and all fail before the agent runs.
- Five judge tasks with rubrics written.
- Notes: the three kinds of scoring.
- Sticky note: "Where would a judge be wrong?"
