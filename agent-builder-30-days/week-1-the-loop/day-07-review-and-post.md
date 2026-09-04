# Day 7: Review, Post, Record

**Goal:** turn the week into something you will remember and something others can see. This day is not optional and it is not lighter. Writing is the test of understanding.

## Block 1: the post (90 minutes)

Write "How an agent loop works", 500 words, from your notes only. Do not open the code until the draft is done. Structure:

1. **What an agent is** in one paragraph. The loop, in words.
2. **The four stop conditions** and why each exists. Use the moment you hit each one.
3. **Why tool results are user messages.** Most readers have never understood this.
4. **One thing that surprised you.** The cache breaking on a timestamp. The model skipping the tool when the description was weak. The agent guessing when you removed "reproduce first".
5. **What I would do differently.** Two sentences.

Then open the code and correct any wrong claims. Then have Claude Code review it for accuracy only, not style. Publish it: GitHub README, dev.to, or your site. Put the link in your log.

## Block 2: the repo (60 minutes)

Make `agent-course` presentable:

- `README.md` with: what it is, how to run `coding_agent.py`, a 20 line sample of the output, and the cost of one run.
- Delete scratch files. Keep `day0X.py` files in a `days/` folder.
- Commit with a clear message. Push to GitHub, public.

This repo grows for four weeks and becomes part of the portfolio.

## Block 3: the review (45 minutes)

Open `notes/weekly-review.md` and fill it in fully. Then:

1. Reread all seven daily logs. Write the three things you kept not understanding.
2. For each, write one sentence in your own words now. If you still cannot, that is Monday's first sticky note.
3. Listen to all seven recaps. Score the rambling: worse, same, better.
4. Reread the idea log. Star anything still interesting.

## Constraint prototype (weekend, 2 hours max)

**An agent with no tools.** Only a system prompt and a conversation. Pick a real task from the clinic or causelist project and see how far pure reasoning gets. Write ten lines: where did it fail for lack of hands, where did it surprise you?

## The record

Record a two minute explanation of the agent loop as if to a hiring manager. No notes. Listen back. Record again. Keep the second one.

## Check yourself, the week

Answer out loud, not on paper:

1. What is in a request? What is in a response?
2. What is a content block?
3. What is prompt caching and what breaks it?
4. What is a tool definition? Who runs the tool?
5. Write the loop in the air with your finger.
6. Name the four stop conditions.
7. Why do tool results go in one user message?
8. What makes a good tool description?
9. What did you sandbox and why?
10. What did the coding agent do when you removed "reproduce first"?

Ten for ten means week 2. Fewer means Monday morning is a revision block before day 8.

## Done when

- Post published, link in log.
- Repo public with a README.
- Weekly review filled in.
- Constraint prototype done, ten lines written.
- Two minute recording kept.
- Body: bedtime moved 30 minutes earlier than Monday.
