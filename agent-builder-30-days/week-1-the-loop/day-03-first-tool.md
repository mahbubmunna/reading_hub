# Day 3: The First Tool

**Goal:** one tool, one full round trip, done by hand. After today you know exactly what a "tool call" is: a request from the model, executed by you, whose result you send back.

## Paper first (20 minutes)

Draw the sequence:

1. You send messages plus a list of tool definitions.
2. The model replies. What does it reply with if it wants a tool?
3. You run the tool. Where does the output go?
4. The model replies again.

Now answer: at step 2, has the tool run yet? Who runs it?

## Concepts

**A tool definition is a prompt.** It is a name, a description, and a JSON schema for inputs. The model reads the description to decide when to call it. Bad descriptions are the number one cause of agents that do not use tools, or use them wrongly.

**The model never runs anything.** It returns a `tool_use` content block: a name, an id, and an input dict. Your code runs the function. Your code sends back a `tool_result` block with the same id. The model then continues.

**Tool results are user messages.** This surprises everyone. The conversation is user, assistant, user, assistant. The assistant said "call this tool". The result comes from the outside world, which is the user side. So it goes in a user message.

**Errors are results too.** If the tool fails, send the error text back with `is_error: true`. Never crash. The model is often good at recovering, for example by fixing a path.

## Step 1: define a tool

Create `tools/__init__.py` (empty) and `tools/calc.py`:

```python
import ast
import operator as op

_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def calculator(expression: str) -> str:
    """Evaluate arithmetic safely. No eval()."""
    tree = ast.parse(expression, mode="eval")
    return str(_eval(tree.body))


DEFINITION = {
    "name": "calculator",
    "description": (
        "Evaluate an arithmetic expression exactly. Use this whenever the user "
        "asks for a calculation, a total, a percentage, or a date difference in "
        "days. Do not do arithmetic in your head. Supports + - * / ** % and parentheses."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A single arithmetic expression, e.g. (1200*0.15)+40",
            }
        },
        "required": ["expression"],
        "additionalProperties": False,
    },
    "strict": True,
}
```

Read the description again. It says what the tool does, when to call it, and what not to do. That is the shape of every good description.

## Step 2: the manual round trip

Create `day03.py`:

```python
import json
from llm import ask, text_of, spend
from tools.calc import calculator, DEFINITION

TOOLS = [DEFINITION]
messages = [{"role": "user", "content": "A court fee is 15% of 12,450 taka plus a fixed 300. What is the total?"}]

# --- call 1: the model decides whether to use the tool
msg = ask(messages, tools=TOOLS, system="Use the calculator for all arithmetic.")
print("stop_reason:", msg.stop_reason)
print("blocks:", [b.type for b in msg.content])

# Append the assistant's full content, including the tool_use block
messages.append({"role": "assistant", "content": msg.content})

# --- run the tools it asked for
results = []
for block in msg.content:
    if block.type == "tool_use":
        print("tool requested:", block.name, json.dumps(block.input))
        try:
            out = calculator(**block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        except Exception as e:
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": f"error: {e}", "is_error": True})

# Results go back as ONE user message
messages.append({"role": "user", "content": results})

# --- call 2: the model sees the result and answers
msg = ask(messages, tools=TOOLS, system="Use the calculator for all arithmetic.")
print(text_of(msg))
print(spend.report())
```

Run it. You should see `stop_reason: tool_use`, then the tool request, then the final answer.

## Step 3: watch it not use the tool

Change the question to "What is the capital of Bangladesh?" and run. `stop_reason` is `end_turn`, no tool block. The model decided. That is `tool_choice: auto`, the default.

Now weaken the description to just "A calculator." and ask the fee question again. Does it still call the tool? Sometimes it will do the arithmetic itself. Descriptions matter. Put the good description back.

## Step 4: send an error

Make `calculator` raise for anything containing a letter. Ask "What is x plus 2?". Watch the model receive `is_error` and explain the problem, or ask you for the value. Your loop never crashed. That is the behaviour you want.

## Exercise, without AI

Write the tool definition for a `read_file(path)` tool on paper, including a description that says when to use it and when not to. You will need it tomorrow.

## Check yourself

1. What is in a `tool_use` block?
2. Why is the `tool_result` a user message?
3. What is `tool_use_id` for?
4. What happens if you send two tool results in two separate user messages instead of one?

Answer to 4: it works but it teaches the model not to call tools in parallel. Always one user message with all results.

## Common mistakes

- Appending only the text of the assistant reply, dropping the `tool_use` block. The next call then fails because the result has no matching id.
- Forgetting to pass `tools` on the second call.
- Doing string matching on `block.input`. Always treat it as a dict.

## Done when

- The round trip runs and prints a correct total.
- You saw the model skip the tool for a non arithmetic question.
- You saw an `is_error` result handled gracefully.
- Notes updated: "Tool result vs tool use".
- Tomorrow's sticky note: "When should a loop stop?"
