# Days 28 to 30: Interview Prep, Applications, Month Two

Three days. Morning blocks for interview practice, afternoon blocks for applications, block 3 for the review of the whole month.

## Day 28: system design for agents

Practice, out loud, recorded, 15 minutes each:

1. **"Design a support agent for a bank."** Cover: what it may and may not do, tools, confirmation gates, memory scopes, evals, cost caps, tracing, injection defenses, what to log, how to roll out.
2. **"Your agent's pass rate dropped from 80 to 70 after a model upgrade. What do you do?"** Cover: rerun the eval, per tag breakdown, read flips, check the judge, check tool descriptions, check the noise floor.
3. **"How would you cut cost by half without losing quality?"** Cover: caching and prefix stability, budget and trimming, cheaper model for summaries and judge, fewer steps via better prompts, measure each.
4. **"What happens when a tool fails?"** Cover: error results, error budget, retries with backoff, idempotency, user facing messages.

Then a coding round: rewrite the agent loop from memory in 20 minutes with tests. You did this on day 4. Do it again.

## Day 29: applications and the story

Send ten applications. Each with the tailored first sentence, the live URL, one number, and the video.

Then write your two minute story for "tell me about yourself", built from the month: what you built, one number, one failure, what you want next. Record it. This replaces the rambling version. Listen to your day 1 recap and this one back to back. Write the difference down.

## Day 30: the review of the month

Fill in `notes/weekly-review.md` for week 4, then a month review:

**The three signals:**
- Longest stretch on one hard problem without wanting to switch: __ minutes. Week 1 was __.
- Idea log: __ starred out of 90. Which three are worth a weekend each?
- Recap on day 1 versus day 30: rambling worse, same, or better?

**The body:**
- Bedtime day 1 versus day 30.
- Walks and strength sessions completed.
- Slips. No judgement. Data.
- Did the blood test happen? Results?

**What I built:** list every deliverable with its link.

**What I still do not understand:** be honest. This becomes month two's reading list.

**Ten remaining applications** sent.

## Month two, the shape

Do not plan it in detail today. Just the shape:

- **Depth project.** Pick the clinic or the causelist app and take it to real users. Real users generate the failures that teach the most.
- **Voice.** Speech to text and text to speech on the receptionist, latency budget under two seconds, interruption handling. This is the feature that makes the demo memorable.
- **Reading.** The month two list at the bottom of `reading-list.md`.
- **Writing.** One post every two weeks. The writeup format from day 27.
- **Keep the routine.** Walk, blocks, idea log, recap, weekly review. The routine is the product. The projects are what it produces.

## Done when

- Four design answers recorded.
- Twenty applications sent.
- Month review written.
- Month two shape written.
- You have read your day 1 log and your day 30 log back to back.

That is the month. Whatever the applications do, you now have something most applicants do not: a system you built from the API up, measured, hardened, and shipped, and the written record of how. Keep going.
