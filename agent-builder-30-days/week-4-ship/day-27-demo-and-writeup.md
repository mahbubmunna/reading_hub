# Day 27: Demo Video and the Failure Writeup

**Goal:** a three minute video and a writeup of what broke. Hiring managers read failure stories more carefully than feature lists, because failure stories show judgement.

## Paper first (20 minutes)

List every real failure from the month: the cache breaking on a timestamp, the agent guessing when you removed "reproduce first", facts lost in summaries, the judge disagreeing with you, wrong citations, the poisoned document, the runaway loop. Pick the four best. For each: what happened, how you noticed, what you changed, how you proved the fix.

## The video

Script it. Three minutes is about 400 words. Structure:

| Time | Content |
|---|---|
| 0:00 | One sentence: what it is. Show the live page. |
| 0:15 | Ask a factual question. Show citations. |
| 0:40 | Ask for availability, propose a booking, show the confirmation gate, confirm, show the database row. |
| 1:20 | Show a trace for that request in the query tool. Point at cost. |
| 1:45 | Show the eval chart and the retrieval table. Say the numbers. |
| 2:15 | Show Claude Code calling the MCP server. |
| 2:40 | One failure and the fix, 20 seconds. |
| 2:55 | Link to the repo. |

Record with QuickTime or OBS. No music. Speak slowly. Record it three times, keep the third. Upload unlisted to YouTube. Link it from the README.

## The writeup

`WRITEUP.md`, 800 to 1000 words, four sections, one per failure:

**Shape of each section:**
1. What I expected.
2. What actually happened, with the exact observation. A usage line, a wrong citation, a trace.
3. Why, once I understood it.
4. The fix, and the number that proves it.
5. What I would do differently in a bigger system.

This document is the strongest thing in your portfolio. It shows you measure, you debug, and you are honest. Have Claude Code check it for accuracy, not tone.

## Prepare the applications

Make a list of 20 roles: AI engineer, LLM engineer, agent engineer, applied AI, forward deployed engineer, and full stack roles that mention LLMs. Local, remote, and contract. For each, one line on why you fit.

Write a base cover note, 120 words, that leads with the live URL and one number. Tailor the first sentence per role.

Update LinkedIn: headline includes "LLM agents", the featured section has the repo, the video, and the three posts.

## Exercise, without AI

Tell the four failure stories out loud in one minute each. Record. These are your interview answers.

## Done when

- Video uploaded and linked.
- `WRITEUP.md` committed.
- 20 roles listed, cover note written, LinkedIn updated.
- Sticky note: "What would I build next, and why?"
