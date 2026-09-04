# Day 16: Hybrid Search and Reranking

**Goal:** combine keyword search with vector search, then rerank the merged list. This is the standard production retrieval stack, and you will build every part.

## Paper first (20 minutes)

Write five questions where exact words matter: a doctor's name, a price, a drug name, a case number, a court number. Would a vector search find "Dr. Farhana Rahman" when the query says "Farhana"? Would it find "Court 7" when many chunks mention courts? That is why keyword search still exists.

## Concepts

**BM25** is keyword search with good weighting. It is exact on names, numbers, and rare words, which vectors are bad at. Vectors are good at meaning and paraphrase, which BM25 is bad at.

**Reciprocal rank fusion** merges two ranked lists using positions, not scores. Scores from different systems are not comparable, ranks are. Score for a chunk is the sum over lists of 1 divided by (60 plus its rank).

**Reranking** takes the top 20 or so merged candidates and rescores each against the query with a stronger model that reads both together. It is slower per item, which is why it runs only on the shortlist. You will do it with a cross encoder, and once with Claude to see the difference.

## Step 1: BM25

Add to `rag/index.py`:

```python
import re
from rank_bm25 import BM25Okapi

def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())

class Index(Index):  # or just add these methods to the class above
    def build_bm25(self) -> None:
        self._bm_ids = [c.id for c in self.all_chunks()]
        self._bm = BM25Okapi([_tok(c.text) for c in self.all_chunks()])

    def keyword_search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        if not hasattr(self, "_bm"):
            self.build_bm25()
        scores = self._bm.get_scores(_tok(query))
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [(self._bm_ids[i], float(scores[i])) for i in top]
```

Put the methods directly in the `Index` class rather than subclassing. The snippet above is shaped to show what to add.

## Step 2: fusion

Create `rag/hybrid.py`:

```python
from __future__ import annotations

from rag.index import Index


def rrf(lists: list[list[tuple[str, float]]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked in lists:
        for rank, (cid, _) in enumerate(ranked):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])


def hybrid_search(idx: Index, query: str, k: int = 10, candidates: int = 20) -> list[tuple[str, float]]:
    v = idx.vector_search(query, candidates)
    b = idx.keyword_search(query, candidates)
    return rrf([v, b])[:k]
```

Run your five keyword questions through vector only, keyword only, and hybrid. Tally which finds the right chunk in the top five. Write the three tallies in your log.

## Step 3: cross encoder reranking

```bash
uv add sentence-transformers  # already present; cross encoders ship with it
```

Add to `rag/hybrid.py`:

```python
from sentence_transformers import CrossEncoder

_reranker = None

def rerank(idx: Index, query: str, hits: list[tuple[str, float]], k: int = 5) -> list[tuple[str, float]]:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    pairs = [(query, idx.get(cid).text) for cid, _ in hits]
    scores = _reranker.predict(pairs)
    ranked = sorted(zip([h[0] for h in hits], scores), key=lambda x: -x[1])
    return [(cid, float(s)) for cid, s in ranked[:k]]


def retrieve(idx: Index, query: str, k: int = 5) -> list[tuple[str, float]]:
    return rerank(idx, query, hybrid_search(idx, query, k=20), k=k)
```

## Step 4: reranking with Claude, once, to compare

Create `rag/llm_rerank.py`:

```python
from pydantic import BaseModel
from llm import client, spend

class Ranking(BaseModel):
    ordered_chunk_ids: list[str]

def llm_rerank(idx, query: str, hits, k: int = 5, model: str = "claude-haiku-4-5"):
    listing = "\n\n".join(f"[{cid}]\n{idx.get(cid).text[:800]}" for cid, _ in hits)
    resp = client.messages.parse(
        model=model, max_tokens=500,
        messages=[{"role": "user", "content":
            f"Query: {query}\n\nRank these chunks from most to least relevant to the query. "
            f"Return only chunk ids.\n\n{listing}"}],
        output_format=Ranking,
    )
    spend.add(resp.usage, model)
    return [(cid, 0.0) for cid in resp.parsed_output.ordered_chunk_ids[:k]]
```

Run both rerankers on your five hard questions. Compare quality, latency, and cost. Write the comparison. Most teams use a cross encoder for speed and an LLM reranker only for the hardest queries. Now you know why from your own data.

## Step 5: swap into the answerer

In `rag/answer.py`, replace `idx.vector_search(question, k)` with `retrieve(idx, question, k)`. Spot check three answers again.

## Exercise, without AI

Explain reciprocal rank fusion to a rubber duck without looking. Include why ranks and not scores.

## Check yourself

1. Give one query where BM25 wins and one where vectors win, from your own corpus.
2. Why is the fusion constant 60 and not 1?
3. Why rerank only 20 candidates and not all chunks?
4. What did the LLM reranker cost per query?

## Common mistakes

- Adding raw BM25 scores to cosine scores.
- Reranking the whole corpus.
- Tokenizing differently at index time and query time.

## Done when

- Three tallies: vector, keyword, hybrid.
- Cross encoder versus LLM reranker comparison written.
- Answerer uses `retrieve`.
- Notes: "Hybrid search", "Reranking".
- Sticky note: "Can retrieval be right while the answer is wrong?"
