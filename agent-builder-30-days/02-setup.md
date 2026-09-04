# Day 0: Setup

Do this before day 1. It takes about an hour.

> **Running this free?** Read `FREE-PROVIDER-GUIDE.md` first. It replaces steps 3 and 4 below with your own GPU plus free hosted tiers, and gives you a client that works with both. Steps 1, 2, 5, 6, and 7 apply either way.

## 1. Python and uv

```bash
# macOS
brew install uv
uv --version
```

We use `uv` for everything. It is fast and handles Python versions and virtual environments.

## 2. The project

```bash
mkdir -p ~/agent-course && cd ~/agent-course
git init
uv init --python 3.12
uv add anthropic pydantic rich python-dotenv pytest "fastapi[standard]" uvicorn
```

Folder shape you will grow over the month:

```
agent-course/
  .env                 <- API key, never committed
  .gitignore
  llm.py               <- day 1: thin client wrapper
  tools/               <- day 3 onward
  agent.py             <- day 4: the loop
  memory/              <- week 2
  evals/               <- week 2
  rag/                 <- week 3
  mcp_server/          <- week 3
  app/                 <- week 4: FastAPI service wrapping agent.py
  notes/               <- your daily logs
```

```bash
cat > .gitignore <<'G'
.env
.venv/
__pycache__/
*.db
.pytest_cache/
G
```

## 3. API key and spend limit

1. Console at console.anthropic.com. Create a key.
2. In the console, set a monthly spend limit. Twenty USD is enough for the course if you follow the token budgets.
3. Save the key:

```bash
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

The SDK reads it from the environment. Load it with `python-dotenv` in your scripts, or export it in your shell.

## 4. Smoke test

```bash
uv run python -c "
import anthropic
from dotenv import load_dotenv
load_dotenv()
c = anthropic.Anthropic()
r = c.messages.create(model='claude-opus-5', max_tokens=100,
    messages=[{'role':'user','content':'Say ready.'}])
print(r.content[0].text, r.usage)
"
```

You should see "Ready." and a usage object. If you see an auth error, the key is not loading.

## 5. Tools you will use

- **Claude Code** for building. You already have it.
- **A blocker** for feeds and porn. Cold Turkey Blocker or Freedom on the Mac. Give the password to your wife. Block at the router as well if you can.
- **A paper notebook** for the 20 minutes before each build session.
- **Voice memos** on the phone for the two minute recap.

## 6. Copy the templates

```bash
mkdir -p ~/agent-course/notes
cp agent-builder-30-days/templates/*.md ~/agent-course/notes/
```

## 7. Read the plan once

Open `00-the-plan.md` and `01-imagination-practice.md`. Read once. Do not read the week folders ahead of time.

## Done when

- Smoke test prints "Ready."
- Spend limit is set.
- Blocker is on and you do not hold the password.
- Notes folder exists with the templates.
- Tomorrow's sticky note is written: "What is the smallest thing an agent needs to be an agent?"
