# Day 2: Structured Output and Prompt Caching

**Goal:** get typed data out of the model reliably, and cut input cost with caching. Both are things a hiring manager will ask about.

## Paper first (20 minutes)

1. Write down three places in your clinic or causelist app where you need the model to return data, not prose. What fields? What types?
2. Draw a request with a big system prompt and a small question. Now draw it again for a second question. Circle what is identical. That circle is what caching saves.

## Concepts

**Structured output** means the API guarantees the response matches a JSON schema. No more regex on the model's prose. You give a Pydantic model, you get a Pydantic instance back.

**Prompt caching** is a prefix match. The API caches the start of your request: tools, then system prompt, then messages, in that order. If the next request starts with the exact same bytes, that part is read from cache at about a tenth of the price. Any change anywhere in the prefix, even one character, invalidates everything after it. There is a minimum size before caching kicks in, so tiny prompts never cache.

## Step 1: structured output with Pydantic

Create `day02_structured.py`:

```python
from pydantic import BaseModel
from llm import client, MODEL, spend


class CaseEntry(BaseModel):
    case_number: str
    court: str
    date: str          # ISO date
    parties: list[str]
    urgent: bool


raw = """
Item 14. Writ Petition 4521 of 2025. Rahman vs Bangladesh Bank.
Listed before Court 7, hearing on 12 September 2025. Marked urgent.
"""

resp = client.messages.parse(
    model=MODEL,
    max_tokens=1024,
    messages=[{"role": "user", "content": f"Extract the case entry:\n{raw}"}],
    output_format=CaseEntry,
)
spend.add(resp.usage, MODEL)
entry = resp.parsed_output
print(entry)
print(type(entry).__name__, entry.urgent)
```

Run it. You get a `CaseEntry` instance, typed. Try changing `urgent: bool` to `urgent: str` and see the output change. Try adding a field the text does not contain and see what the model does. Write it down.

## Step 2: the raw schema form

You will need this when you cannot use Pydantic, for example in a config file:

```python
resp = client.messages.create(
    model=MODEL,
    max_tokens=1024,
    messages=[{"role": "user", "content": f"Extract the case entry:\n{raw}"}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "case_number": {"type": "string"},
                    "court": {"type": "string"},
                    "urgent": {"type": "boolean"},
                },
                "required": ["case_number", "court", "urgent"],
                "additionalProperties": False,
            },
        }
    },
)
import json
data = json.loads(next(b.text for b in resp.content if b.type == "text"))
print(data)
```

Note `additionalProperties: False` and `required`. Strict schemas need both.

## Step 3: caching, verified

Create `day02_cache.py`. We need a system prompt big enough to cache, so we build one.

```python
from llm import client, MODEL, spend

# A long, stable system prompt. In real apps this is your rules, examples, docs.
rules = "\n".join(
    f"Rule {i}: When a case is marked urgent, list it before non urgent cases "
    f"from the same court. Court numbers are integers. Dates are ISO." 
    for i in range(1, 120)
)
system = [
    {
        "type": "text",
        "text": "You are a High Court causelist assistant.\n" + rules,
        "cache_control": {"type": "ephemeral"},
    }
]

for q in ["What format are dates in?", "How are urgent cases ordered?", "What type is a court number?"]:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": q}],
    )
    spend.add(resp.usage, MODEL)
    print(">", next(b.text for b in resp.content if b.type == "text")[:80])

print(spend.report())
```

Run it. First call: `cache_write` is large, `cache_read` is zero. Second and third calls: `cache_read` is large, `in` is small. If `cache_read` stays zero, the prompt is under the minimum size. Increase the range.

## Step 4: break the cache on purpose

Add the current time to the system prompt:

```python
import datetime
system[0]["text"] = f"Time: {datetime.datetime.now()}\n" + system[0]["text"]
```

Run again. Every call is now a cache write and never a read. This is the most common caching bug in real codebases: a timestamp, a user id, or an unsorted dict at the top of the prompt. Put volatile things at the end, after the cached block.

## Exercise, without AI

Write on paper the order in which the API assembles the prefix. Then write three things that silently break caching.

## Check yourself

1. Why must the cached block be a prefix, not just any part of the request?
2. What does `additionalProperties: False` do?
3. When would you use the raw schema form instead of Pydantic?
4. Roughly what fraction of the price is a cache read?

## Common mistakes

- Putting the user's question inside the cached system block.
- Rebuilding the tool list in a different order each call. Tools come before system in the prefix.
- Expecting cache hits on a 200 token prompt.

## Done when

- Structured extraction returns a typed instance.
- You saw `cache_read` go from zero to large, and then back to zero when you added the timestamp.
- Five lines in the log. Concept notes updated for "Structured output" and "Prompt caching".
- Tomorrow's sticky note: "Who decides when a tool is called, me or the model?"
