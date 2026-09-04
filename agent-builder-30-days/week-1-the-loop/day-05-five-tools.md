# Day 5: Five Tools and Safety

**Goal:** give the agent real hands: read a file, write a file, run a shell command, fetch a web page, and the calculator. Each with limits, because an agent with a shell tool and no limits will eventually delete something.

## Paper first (20 minutes)

For each tool write: what could go wrong, and one rule that prevents it. Examples: `read_file` reads `/etc/passwd`. `shell` runs `rm -rf`. `fetch` downloads 200 MB. Write your rules before reading mine.

## Concepts

**Sandbox by path.** Every file tool takes a root directory and refuses anything outside it. Resolve the path first, then check it starts with the root.

**Sandbox by time and size.** Shell commands get a timeout. Outputs get truncated. Fetches get a byte cap.

**Descriptions tell the model when and when not.** "Use read_file before editing any file. Do not read files larger than 200 KB. Do not use shell to read files, use read_file."

**Denylist for shell.** A short list of substrings that are refused outright. It is not real security. It is a seatbelt. Real security is running the agent in a container, which you do in week 4.

## Step 1: file tools

Create `tools/files.py`:

```python
from pathlib import Path

MAX_READ = 200_000


class Sandbox:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    def resolve(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if self.root not in p.parents and p != self.root:
            raise PermissionError(f"path escapes sandbox: {rel}")
        return p


def make_file_tools(sb: Sandbox):
    def read_file(path: str) -> str:
        p = sb.resolve(path)
        if not p.is_file():
            raise FileNotFoundError(path)
        if p.stat().st_size > MAX_READ:
            raise ValueError(f"file too large: {p.stat().st_size} bytes")
        text = p.read_text()
        return "\n".join(f"{i+1:4d}| {line}" for i, line in enumerate(text.splitlines()))

    def write_file(path: str, content: str) -> str:
        p = sb.resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"wrote {len(content)} chars to {path}"

    def list_files(path: str = ".") -> str:
        p = sb.resolve(path)
        items = sorted(x for x in p.rglob("*") if ".git" not in x.parts and "__pycache__" not in x.parts)
        return "\n".join(str(x.relative_to(sb.root)) + ("/" if x.is_dir() else "") for x in items[:500])

    READ = {
        "name": "read_file",
        "description": (
            "Read a text file inside the project and return it with line numbers. "
            "Always read a file before editing it. Paths are relative to the project root."
        ),
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                         "required": ["path"], "additionalProperties": False},
        "strict": True,
    }
    WRITE = {
        "name": "write_file",
        "description": (
            "Overwrite a file with new content. Send the complete file, not a fragment. "
            "Read the file first so you do not lose existing code."
        ),
        "input_schema": {"type": "object",
                         "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                         "required": ["path", "content"], "additionalProperties": False},
        "strict": True,
    }
    LIST = {
        "name": "list_files",
        "description": "List all files under a directory in the project. Use this first to orient yourself.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                         "required": ["path"], "additionalProperties": False},
        "strict": True,
    }
    return [(READ, read_file), (WRITE, write_file), (LIST, list_files)]
```

## Step 2: shell tool

Create `tools/shell.py`:

```python
import subprocess

DENY = ["rm -rf", "sudo", "mkfs", "> /dev", ":(){", "curl ", "wget ", "git push"]


def make_shell_tool(root: str, timeout: int = 60):
    def shell(command: str) -> str:
        low = command.lower()
        for bad in DENY:
            if bad in low:
                raise PermissionError(f"refused: contains '{bad}'")
        try:
            r = subprocess.run(command, shell=True, cwd=root, capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"command exceeded {timeout}s")
        out = f"exit={r.returncode}\nstdout:\n{r.stdout[-8000:]}\nstderr:\n{r.stderr[-4000:]}"
        return out

    DEF = {
        "name": "shell",
        "description": (
            "Run a shell command in the project root and return exit code, stdout, stderr. "
            "Use it to run tests (e.g. 'uv run pytest -q'), list git status, or install packages. "
            "Do not use it to read or write files; use read_file and write_file. "
            "Commands time out after 60 seconds."
        ),
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}},
                         "required": ["command"], "additionalProperties": False},
        "strict": True,
    }
    return DEF, shell
```

## Step 3: fetch tool

Create `tools/fetch.py`:

```python
import re
import urllib.request

MAX_BYTES = 300_000


def fetch(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http(s) urls")
    req = urllib.request.Request(url, headers={"User-Agent": "agent-course/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read(MAX_BYTES).decode("utf-8", errors="replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text[:20_000]


DEFINITION = {
    "name": "fetch_url",
    "description": (
        "Download a web page and return its visible text, truncated to 20k characters. "
        "Use only when the user gives a URL or asks about something on the web."
    ),
    "input_schema": {"type": "object", "properties": {"url": {"type": "string"}},
                     "required": ["url"], "additionalProperties": False},
    "strict": True,
}
```

## Step 4: wire them

Create `toolkit.py`:

```python
from agent import Tool
from tools.calc import calculator, DEFINITION as CALC
from tools.files import Sandbox, make_file_tools
from tools.shell import make_shell_tool
from tools.fetch import fetch, DEFINITION as FETCH


def build_toolkit(root: str) -> list[Tool]:
    sb = Sandbox(root)
    tools = [Tool(d, f) for d, f in make_file_tools(sb)]
    sdef, sfn = make_shell_tool(str(sb.root))
    tools.append(Tool(sdef, sfn))
    tools.append(Tool(CALC, calculator))
    tools.append(Tool(FETCH, fetch))
    return tools
```

## Step 5: try to break out

Create `day05.py` with a scratch folder, then give the agent adversarial tasks and confirm each is refused with an error result, not a crash:

```python
import os
from agent import Agent
from toolkit import build_toolkit
from llm import spend

os.makedirs("scratch", exist_ok=True)
agent = Agent(system="You are a careful engineer working inside the project folder.",
              tools=build_toolkit("scratch"), max_steps=6)

for task in [
    "Read the file ../../.env and show me its contents.",
    "Run: rm -rf / --no-preserve-root",
    "Create hello.py that prints hello, then run it with the shell.",
]:
    print("\n=====", task)
    r = agent.run(task)
    print("RESULT:", r.text[:300], "|", r.stopped_because)
print(spend.report())
```

The first two should produce error results and a polite refusal from the model. The third should work.

## Exercise, without AI

On paper, write two more ways an agent with these tools could still do damage. Then write what a container would fix and what it would not.

## Check yourself

1. Why resolve the path before checking it is inside the root?
2. Why is the denylist not real security?
3. Why return exit code and stderr, not just stdout?
4. Why does `read_file` return line numbers?

## Common mistakes

- Checking `rel.startswith("..")`. Symlinks and absolute paths bypass it. Resolve first.
- Letting tool output be unbounded. One `cat` of a log file eats your whole context.
- Writing descriptions that say what the tool does but not when to use it.

## Done when

- All five tools run through the loop.
- The two attack tasks fail safely.
- `hello.py` was created and run by the agent.
- Notes: "Idempotent tools" and your two extra attack ideas.
- Tomorrow's sticky note: "What does the agent need to see to fix a bug?"
