# Week 3: RAG and MCP on a Real Project

## Goal

Two production skills on one of your real projects. First, retrieval: give the agent a knowledge base it can search, and measure retrieval quality separately from answer quality. Second, MCP: expose your project's capabilities as tools any agent can use, including Claude Code.

## Pick the project now

Choose one, and use it all week:

- **Clinic receptionist.** Knowledge base: services, hours, doctors, prices, policies, FAQs. Tools: check availability, book appointment, look up a patient's next visit.
- **Causelist Pro.** Knowledge base: court rules, practice directions, case notes. Tools: search causelist, get case status, list today's matters for a lawyer.

My recommendation is the clinic, because it has real users and a voice component in week 4. Whatever you pick, write down 40 to 60 documents' worth of content by Monday night. Real content, not lorem ipsum. Generate it with Claude if you must, then edit it so you know what is in it.

## The deliverable

1. `rag/` with chunking, embeddings, BM25, hybrid search, reranking, and citations.
2. Retrieval eval: 25 questions with known source chunks. Recall at 5 measured across three iterations.
3. `mcp_server/` on GitHub: three tools, README, tests, connected to Claude Code and to your own agent.

## Days

| Day | File | You will have |
|---|---|---|
| 15 | day-15-chunking-and-embeddings.md | Chunks, embeddings, vector search in SQLite |
| 16 | day-16-hybrid-and-rerank.md | BM25, fusion, reranking |
| 17 | day-17-retrieval-evals.md | Recall at 5, three iterations, a table |
| 18 | day-18-mcp-server.md | An MCP server with three tools |
| 19 | day-19-tests-and-descriptions.md | Tests, description design, error shapes |
| 20 | day-20-integration.md | Connected to Claude Code and to agent.py |
| 21 | day-21-review.md | Publish, review |

## Checklist

- [ ] I can explain why chunk size matters and what I chose
- [ ] Retrieval recall is measured without the generator involved
- [ ] Hybrid beats either method alone on my eval, or I know why not
- [ ] Answers cite chunk ids and the citations are correct on spot check
- [ ] MCP server runs, three tools, each with a description that says when to use it
- [ ] Tests cover each tool's happy path and one failure
- [ ] Claude Code can call my server; so can my own loop
- [ ] Published, README has a 30 second demo

## Sticky note questions

- Day 15: How big should a chunk be, and who decides?
- Day 16: When would keyword search beat vectors?
- Day 17: Can retrieval be right while the answer is wrong?
- Day 18: What makes a tool worth exposing?
- Day 19: What should a tool say when it fails?
- Day 20: What is the difference between a tool and an API?
- Day 21: What did I not understand this week?
