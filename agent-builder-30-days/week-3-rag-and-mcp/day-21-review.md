# Day 21: Publish and Review

## Block 1: publish the MCP server (90 minutes)

Make `mcp_server/` its own public GitHub repo, or a clearly separated folder with its own README. The README must have:

1. One paragraph: what it exposes and for whom.
2. Install and run, three commands.
3. The three tools with one line each.
4. A 30 second demo: a screen recording or an asciinema cast of Claude Code booking an appointment.
5. How to run the tests.
6. What is deliberately not exposed, and why.

Commit and tag `week-3`.

## Block 2: the retrieval writeup (60 minutes)

`rag/README.md`, 400 words:

- Corpus size, chunking choice and why.
- The iteration table from day 17.
- Recall versus answer quality, with numbers.
- The one thing that moved recall most.
- What you would do with 100 times more documents.

## Block 3: the review (45 minutes)

Fill in `notes/weekly-review.md`. Then the ten, out loud:

1. Why prepend context to chunks?
2. When does keyword search beat vectors?
3. Why fuse ranks instead of scores?
4. Why rerank only a shortlist?
5. What is recall at 5? What is MRR?
6. Why measure retrieval separately from generation?
7. What is the difference between a tool and an endpoint?
8. What are the two parts of a good tool error?
9. How did you test descriptions?
10. Why is one MCP server better than three copies of the functions?

## Constraint prototype (weekend, 2 hours max)

**Two agents that must disagree before answering.** One proposes an answer to a clinic question using the RAG tool. The second is instructed to find a flaw. Only after the second has objected once does the first give a final answer. Does the answer improve? Does it cost double? Ten lines.

## The record

Two minutes: "How I built and measured retrieval." Numbers included.

## Body check

You are three weeks in. Bedtime should be near 1 to 2am. Focus signal: what was your longest stretch on one hard problem this week? Write it down. Compare with week 1.

## Done when

- Server published with demo.
- RAG writeup committed.
- Ten for ten or Monday revision.
- Prototype done.
- Recording kept.
