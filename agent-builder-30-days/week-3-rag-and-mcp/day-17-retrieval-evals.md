# Day 17: Retrieval Evals, Three Iterations

**Goal:** measure retrieval on its own, then improve it three times and show the numbers. This is the RAG equivalent of week 2's before and after, and it answers the interview question "how do you debug a RAG system".

## Paper first (20 minutes)

Two failure types. The right chunk was not retrieved. The right chunk was retrieved but the answer was still wrong. Which is which in the three wrong answers you found this week? You cannot fix what you cannot separate.

## Concepts

**Recall at k.** For a question, is at least one of the known correct chunks in the top k? Averaged over questions. This is the retrieval metric. It does not involve the generator at all.

**Mean reciprocal rank.** One divided by the position of the first correct chunk. Rewards putting the right thing first. Report both.

**Answer quality is a separate metric**, scored by a judge, exactly like week 2. Keep them separate. If recall is 90 percent and answer quality is 60 percent, the problem is the prompt, not retrieval. If recall is 50 percent, do not touch the prompt.

**Iterate on one knob.** Chunk size, overlap, context prefix, candidates for reranking, hybrid weights. One at a time, measure each.

## Step 1: the retrieval dataset

Create `rag/eval_set.py`. Twenty five questions, each with the chunk ids that answer it. Build it by reading your chunks, not by guessing:

```python
# (question, [correct chunk ids])   fill from your own corpus
RETRIEVAL_SET = [
    ("What time does the clinic close on Friday?", ["hours::Friday::0"]),
    ("How much is a first consultation with Dr Rahman?", ["pricing::Consultations::0", "dr-rahman::Fees::0"]),
    # ... 25 in total. Include:
    #  - 10 easy: wording matches the chunk
    #  - 8 paraphrased: same meaning, different words
    #  - 4 keyword heavy: names, numbers, codes
    #  - 3 unanswerable: correct list is [] and the answer should be "I do not know"
]
```

Get chunk ids from `idx.all_chunks()`. Yes, this is tedious. It is also the single highest leverage hour of the week.

## Step 2: the metrics

Create `rag/eval_retrieval.py`:

```python
from __future__ import annotations

import json
import sys
import time

from rag.index import Index
from rag.hybrid import hybrid_search, retrieve
from rag.eval_set import RETRIEVAL_SET

METHODS = {
    "vector": lambda idx, q, k: idx.vector_search(q, k),
    "keyword": lambda idx, q, k: idx.keyword_search(q, k),
    "hybrid": lambda idx, q, k: hybrid_search(idx, q, k),
    "hybrid+rerank": lambda idx, q, k: retrieve(idx, q, k),
}


def evaluate(idx: Index, method: str, k: int = 5) -> dict:
    fn = METHODS[method]
    recall_hits, rr_sum, n, lat = 0, 0.0, 0, []
    misses = []
    for q, gold in RETRIEVAL_SET:
        if not gold:
            continue  # unanswerables are scored in the answer eval, not here
        t0 = time.time()
        got = [cid for cid, _ in fn(idx, q, k)]
        lat.append(time.time() - t0)
        n += 1
        ranks = [i for i, cid in enumerate(got) if cid in gold]
        if ranks:
            recall_hits += 1
            rr_sum += 1.0 / (ranks[0] + 1)
        else:
            misses.append((q, gold, got))
    lat.sort()
    return {"method": method, "k": k, "recall@k": round(recall_hits / n, 3),
            "mrr": round(rr_sum / n, 3), "p50_ms": int(lat[len(lat)//2]*1000), "misses": misses}


if __name__ == "__main__":
    idx = Index()
    for m in sys.argv[1:] or METHODS:
        r = evaluate(idx, m)
        print(json.dumps({k: v for k, v in r.items() if k != "misses"}))
        for q, gold, got in r["misses"][:3]:
            print("   MISS:", q, "| wanted", gold, "| got", got[:3])
```

Run all four methods. That is iteration zero. Write the table.

## Step 3: three iterations

Each iteration: change one thing, rerun, record, read the misses.

**Iteration 1: chunk size.** Try 150 and 350 words. Rebuild the index each time. Which is better for recall? Which for MRR?

**Iteration 2: context prefix.** Remove the "Document / Section" prefix from chunks and rebuild. Watch recall drop. Put it back. Then try adding the first sentence of the document as well.

**Iteration 3: reranker candidates.** Try 10, 20, 40 candidates into the reranker. Watch latency versus MRR.

You now have a table with at least seven rows. Pick the best configuration and freeze it.

## Step 4: answer quality, separately

Reuse week 2's judge. For the 25 questions, generate answers with the frozen configuration, judge with a rubric that checks correctness and that citations point at chunks containing the claim. Include the three unanswerables: the correct behaviour is to say it does not know. Record answer pass rate next to recall.

If recall is high and answer quality is low, fix the prompt in `rag/answer.py`. Rerun. That is your fourth iteration, on the other half of the system.

## Exercise, without AI

Write the two sentence explanation of why you measure retrieval and generation separately, for a hiring manager.

## Check yourself

1. What is recall at 5 and what is MRR? When do they disagree?
2. Which knob moved recall most?
3. How do you score an unanswerable question?
4. What was your final recall, answer pass rate, and p50 latency?

## Common mistakes

- Gold chunk ids that are wrong because the index was rebuilt with a different chunk size. Ids include the window number, so rebuild the eval set when you change chunking, or key gold by document and heading instead.
- Measuring only end to end answer quality and then changing retrieval settings blindly.
- Only ten eval questions.

## Done when

- Iteration table with at least seven rows.
- Answer quality measured with citations checked.
- Final configuration frozen and committed.
- Notes: "Retrieval recall vs answer quality".
- Sticky note: "What makes a tool worth exposing?"
