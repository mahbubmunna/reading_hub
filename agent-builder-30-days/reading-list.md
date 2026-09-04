# Reading List

Block 3 is 45 minutes. One item per session, in this order. Five lines of notes in your own words after each. If an item takes two sessions, that is fine.

Only sources that matter. Skip everything else until month two.

## Week 1

1. Anthropic, "Building effective agents". The single most important thing to read this month. Note the difference between workflows and agents, and the five patterns.
2. Anthropic, "Effective context engineering for AI agents". How context is a budget, not a bucket.
3. ReAct paper (Yao et al., 2022). Read the intro, figure 1, and section 3. Skip the benchmarks.
4. Anthropic docs, "Tool use" overview and "Prompt caching". Read with the code from day 2 and day 3 open.
5. Claude Agent SDK source: find the agent loop file and read only that file. Compare with your day 4 loop.
6. Anthropic, "Writing tools for agents". Tool descriptions are prompts.

## Week 2

7. Reflexion paper (Shinn et al., 2023). Intro and figure 1. The idea: an agent that reads its own failure and tries again.
8. Anthropic docs, "Context editing" and "Compaction". Compare server side compaction with your day 9 summarizer.
9. Hamel Husain, "Your AI product needs evals". The best practical eval writing.
10. Anthropic, "Demystifying evals for AI agents".
11. Anthropic docs, "Structured outputs". Read with day 12 open.
12. Any recent paper on LLM judge bias. Search "LLM as a judge position bias". Read one.

## Week 3

13. Anthropic, "Contextual retrieval". Chunking with context, and why it helps.
14. A hybrid search explainer. Search "BM25 plus vector hybrid search reciprocal rank fusion". Read one good one.
15. MCP specification, the "Tools" section. Then the Python MCP SDK README.
16. SWE-agent paper (Yang et al., 2024). The section on agent computer interface design. Why the interface matters more than the model.
17. Anthropic docs, "MCP connector".
18. Read the source of one MCP server you use. The filesystem server is a good choice.

## Week 4

19. Anthropic docs, "Streaming" and "Errors and rate limits".
20. Simon Willison, any two posts tagged "prompt-injection". Read the lethal trifecta post.
21. Langfuse docs, "Tracing" quickstart.
22. Anthropic, "Building agents with the Claude Agent SDK". Compare with what you built.
23. One system design writeup of a production LLM agent. Search "how we built our AI agent postmortem".
24. Your own daily log, start to finish.

## Sunday only, one hour, the news sources

- Anthropic research and engineering blog
- OpenAI research blog
- Google DeepMind blog
- Simon Willison's weblog
- Latent Space newsletter or podcast
- Hacker News front page, skim titles only

Nothing from these on weekdays. If a Sunday item is genuinely important, add it to next week's block 3.

## Fiction and outside the field (bed, paper, 20 minutes)

- Ted Chiang, *Stories of Your Life and Others*
- Douglas Hofstadter, *Gödel, Escher, Bach*, chapters 1 to 5

## Month two and beyond, do not start now

- Sutton and Barto, *Reinforcement Learning*, chapters 1 to 3
- Anthropic, "Claude's constitution" and system prompt release notes
- Chip Huyen, *AI Engineering*
- Karpathy, "Let's build GPT" video, then the nanoGPT source
