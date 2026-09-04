# Day 15: Chunking and Embeddings

**Goal:** turn your documents into searchable chunks with vector similarity, stored in SQLite. No vector database yet. You will understand what one does before you pay for one.

## Paper first (20 minutes)

Take one of your documents. Cut it into pieces with a pen. What did you cut on? Headings, paragraphs, a fixed number of words? Now write a question a user would ask. Which piece answers it? Would a smaller piece have been better or worse?

## Concepts

**Chunks are the unit of retrieval.** Too small and a chunk loses its context. Too big and the answer is buried in noise and you waste tokens. Start at 300 to 500 tokens with 50 token overlap, then measure.

**Chunks need context.** A chunk that says "Closed on Fridays" is useless if you do not know it is about the dental department. Prepend the document title and section heading to every chunk. This one trick lifts recall more than most fancy methods.

**Embeddings** turn text into a vector so that similar meanings are near each other. Anthropic does not provide an embeddings endpoint. Use a local model for the course. It is free and good enough to learn with.

**Cosine similarity over a few thousand vectors is a numpy one liner.** You do not need a vector database until you have hundreds of thousands of chunks or need filtering at scale.

## Step 1: dependencies and corpus

```bash
uv add sentence-transformers numpy rank-bm25
mkdir -p rag/corpus
```

Put your 40 to 60 documents in `rag/corpus/` as markdown files. Use headings. Each file is one document. Example for the clinic: `services.md`, `hours.md`, `dr-rahman.md`, `pricing.md`, `cancellation-policy.md`, `faq-pregnancy.md`, and so on.

## Step 2: chunking

Create `rag/__init__.py` (empty) and `rag/chunk.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    id: str
    doc: str
    heading: str
    text: str          # what gets embedded and shown: heading context + body

    @property
    def body(self) -> str:
        return self.text.split("\n\n", 1)[-1]


def _sections(md: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) sections."""
    parts = re.split(r"^(#{1,3} .+)$", md, flags=re.M)
    out, heading = [], "Introduction"
    if parts[0].strip():
        out.append((heading, parts[0].strip()))
    for i in range(1, len(parts), 2):
        heading, body = parts[i].lstrip("# ").strip(), parts[i + 1].strip()
        if body:
            out.append((heading, body))
    return out


def _windows(words: list[str], size: int, overlap: int):
    step = max(1, size - overlap)
    for start in range(0, max(1, len(words) - overlap), step):
        yield words[start:start + size]
        if start + size >= len(words):
            break


def chunk_file(path: Path, size_words: int = 220, overlap_words: int = 40) -> list[Chunk]:
    doc = path.stem
    title = doc.replace("-", " ").title()
    chunks = []
    for heading, body in _sections(path.read_text()):
        words = body.split()
        for n, w in enumerate(_windows(words, size_words, overlap_words)):
            cid = f"{doc}::{heading[:30]}::{n}"
            context = f"Document: {title}\nSection: {heading}"
            chunks.append(Chunk(cid, doc, heading, f"{context}\n\n{' '.join(w)}"))
    return chunks


def chunk_corpus(folder: str = "rag/corpus") -> list[Chunk]:
    out = []
    for p in sorted(Path(folder).glob("*.md")):
        out.extend(chunk_file(p))
    return out


if __name__ == "__main__":
    cs = chunk_corpus()
    print(len(cs), "chunks")
    print(cs[0].text[:400])
```

Run it. Look at three chunks. Do they make sense alone? If a chunk starts mid sentence in a way that loses meaning, increase overlap.

## Step 3: embeddings and a vector index in SQLite

Create `rag/index.py`:

```python
from __future__ import annotations

import json
import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer

from rag.chunk import Chunk, chunk_corpus

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # small, fast, free


class Index:
    def __init__(self, path: str = "rag/index.db") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS chunks(
            id TEXT PRIMARY KEY, doc TEXT, heading TEXT, text TEXT, emb BLOB)""")
        self.model = SentenceTransformer(EMB_MODEL)
        self._ids: list[str] = []
        self._mat: np.ndarray | None = None

    def build(self, chunks: list[Chunk]) -> None:
        texts = [c.text for c in chunks]
        embs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        self.conn.execute("DELETE FROM chunks")
        self.conn.executemany(
            "INSERT INTO chunks VALUES (?,?,?,?,?)",
            [(c.id, c.doc, c.heading, c.text, e.astype(np.float32).tobytes()) for c, e in zip(chunks, embs)])
        self.conn.commit()
        self._load()

    def _load(self) -> None:
        rows = self.conn.execute("SELECT id, emb FROM chunks").fetchall()
        self._ids = [r[0] for r in rows]
        self._mat = np.stack([np.frombuffer(r[1], dtype=np.float32) for r in rows]) if rows else None

    def get(self, cid: str) -> Chunk:
        r = self.conn.execute("SELECT id, doc, heading, text FROM chunks WHERE id=?", (cid,)).fetchone()
        return Chunk(*r)

    def all_chunks(self) -> list[Chunk]:
        return [Chunk(*r) for r in self.conn.execute("SELECT id, doc, heading, text FROM chunks")]

    def vector_search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        if self._mat is None:
            self._load()
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self._mat @ q
        top = np.argsort(-scores)[:k]
        return [(self._ids[i], float(scores[i])) for i in top]


if __name__ == "__main__":
    idx = Index()
    idx.build(chunk_corpus())
    for cid, s in idx.vector_search("what time does the clinic close on Friday", 5):
        print(f"{s:.3f} {cid}")
```

Run it. The first run downloads the model. Then try five questions you know the answers to. Is the right chunk in the top five? Keep a tally. That tally is tomorrow's baseline.

## Step 4: a first RAG answer with citations

Create `rag/answer.py`:

```python
from llm import ask, text_of, spend
from rag.index import Index

SYSTEM = """You answer questions about the clinic using only the provided chunks.
Cite chunk ids in square brackets after each claim, like [hours::Friday::0].
If the chunks do not contain the answer, say you do not know and suggest calling the front desk."""


def answer(question: str, idx: Index, k: int = 5) -> str:
    hits = idx.vector_search(question, k)
    context = "\n\n".join(f"<chunk id=\"{cid}\">\n{idx.get(cid).text}\n</chunk>" for cid, _ in hits)
    msg = ask([{"role": "user", "content": f"Chunks:\n{context}\n\nQuestion: {question}"}], system=SYSTEM)
    return text_of(msg)


if __name__ == "__main__":
    idx = Index()
    print(answer("Is the dental department open on Friday afternoon?", idx))
    print(spend.report())
```

Spot check three answers. Are the citations pointing at chunks that actually say the thing? If a citation is wrong, write it down. Wrong citations are the most common RAG bug and the most embarrassing one in front of a user.

## Exercise, without AI

Explain to an imaginary junior why "Closed on Fridays" is a bad chunk and how you fixed it.

## Check yourself

1. Why prepend document and section to each chunk?
2. What happens to recall as chunks get very large?
3. Why normalize embeddings before the dot product?
4. When would you actually need a vector database?

## Common mistakes

- Chunking on fixed characters and cutting words in half.
- Embedding the chunk body without its context.
- Rebuilding the index on every query.

## Done when

- Index built, five questions tallied.
- Three answers spot checked for citation correctness.
- Notes: "Chunking".
- Sticky note: "When would keyword search beat vectors?"
