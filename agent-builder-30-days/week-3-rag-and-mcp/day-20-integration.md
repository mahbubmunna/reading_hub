# Day 20: Connect It Everywhere

**Goal:** the same MCP server used by Claude Code, and by your own agent loop from week 1. One implementation, many clients. That is the point of the protocol.

## Paper first (20 minutes)

Draw three boxes: Claude Code, your agent.py, your MCP server. Draw the arrows. Where do descriptions live? Where does the database live? What would change if the server moved to a remote machine?

## Concepts

**Clients differ, the server does not.** Claude Code adds its own system prompt and its own tools alongside yours. Your loop adds only yours. The same description must work in both contexts, which is one more reason to write descriptions that say when to use the tool.

**Stdio means the client owns the process.** Claude Code will launch `uv run python mcp_server/server.py` itself. Your working directory, environment variables, and Python version must be right from wherever the client starts it. Use absolute paths in the config.

## Step 1: Claude Code

```bash
claude mcp add clinic -- uv run --directory /absolute/path/to/agent-course python mcp_server/server.py
claude mcp list
```

Then in a Claude Code session, ask: "Using the clinic tools, find a slot with Dr Akter next Monday and book it for Test Patient, phone 017." Watch it call `check_availability` then `book_appointment`. Check the database.

If the server fails to start, run `claude mcp get clinic` and check the command. Most failures are a relative path or a missing `--directory`.

## Step 2: your own loop, via the SDK's MCP helpers

Create `day20.py`:

```python
"""Use the MCP server's tools from the week 1 loop, via the SDK tool runner."""
import asyncio
from anthropic import AsyncAnthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

client = AsyncAnthropic()
SYSTEM = "You are the clinic receptionist. Confirm details before booking. Be brief."


async def main():
    params = StdioServerParameters(command="uv", args=["run", "python", "mcp_server/server.py"])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [async_mcp_tool(t, s) for t in (await s.list_tools()).tools]
            runner = client.beta.messages.tool_runner(
                model="claude-opus-5", max_tokens=4096, system=SYSTEM, tools=tools,
                messages=[{"role": "user", "content":
                    "Is Dr Rahman free on 2026-09-07 at 11:00? If so book it for Mahbub, 01700."}],
            )
            async for message in runner:
                for b in message.content:
                    if b.type == "text" and b.text.strip():
                        print("agent>", b.text)
                    elif b.type == "tool_use":
                        print("tool>", b.name, b.input)


asyncio.run(main())
```

This uses the SDK's tool runner, which is the same loop you wrote in week 1, maintained by Anthropic. Read the output and confirm the same two tool calls happened. Then, for understanding, adapt your own `Agent` class to accept MCP tools: list them, convert to definitions, and call them through the session. Do it once so you know there is no magic.

## Step 3: a second client

Any other MCP client you have, for example the Claude desktop app or an IDE, add the server there too. Same command. If it works in three places without changes, your server is done.

## Step 4: remote transport, briefly

Change the last line to `mcp.run(transport="streamable-http")` and start it. It now listens on a port. This is how you would deploy it for the week 4 FastAPI app or for other teams. Note what you would need to add before exposing it publicly: authentication, rate limiting, and logging. Do not deploy it yet.

## Exercise, without AI

Explain, in five lines, why one MCP server is better than pasting the same three functions into three apps.

## Check yourself

1. Where do tool descriptions live, and how many places did you have to change them today?
2. What does Claude Code add around your tools that your loop does not?
3. Why absolute paths in the Claude Code config?
4. What would you need before exposing the HTTP transport?

## Common mistakes

- Server starts in the wrong directory and cannot find the index or database.
- Loading the sentence transformer on every tool call.
- Forgetting that Claude Code also has its own tools, and writing descriptions that clash with them.

## Done when

- Booking made from Claude Code and from your loop, visible in the database.
- HTTP transport started once.
- Notes: "tool vs endpoint", "stdio vs http".
- Sticky note: "What did I not understand this week?"
