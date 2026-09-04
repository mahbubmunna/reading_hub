# Day 25: Docker and a Live URL

**Goal:** the service runs in a container, then on a host, with a health check and secrets handled correctly.

## Paper first (20 minutes)

List everything your service needs at runtime: Python version, packages, the embedding model files, the index, the databases, the API key, a port. Now decide which of these go in the image, which are mounted, and which are environment variables.

## Concepts

**The image holds code and dependencies.** Not secrets, not data that changes. The API key is an environment variable. Databases are on a volume or an external service.

**The embedding model is a download.** Either bake it into the image at build time so the container starts fast, or accept a slow first start. Bake it.

**Health checks let the platform restart you.** `/health` must be cheap and must not call the model.

**One process per container** for now. Two workers with SQLite means write conflicts. Scale later by moving state to Postgres.

## Step 1: Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /srv
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
# bake the models so the container starts fast
RUN uv run python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"
RUN uv run python -c "from rag.index import Index; from rag.chunk import chunk_corpus; Index('rag/index.db').build(chunk_corpus())"
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add `.dockerignore` with `.env`, `.venv`, `*.db` except the index, `traces.jsonl`, `evals/results`, `.git`.

```bash
docker build -t clinic-agent .
docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -v $(pwd)/data:/srv/data clinic-agent
curl localhost:8000/health
```

Point `MemoryStore` and traces at `/srv/data/` via an environment variable so they land on the volume.

## Step 2: deploy

Pick one. Fly.io and Railway are both fine and both have a free or near free tier. Follow their current docs. The steps are always: install their CLI, log in, create an app, set the `ANTHROPIC_API_KEY` secret, attach a volume for `/srv/data`, deploy.

Confirm:

```bash
curl https://your-app.example/health
curl -N https://your-app.example/chat -H 'content-type: application/json' \
  -d '{"user_id":"demo","message":"What are your hours?"}'
```

## Step 3: production hardening, the short list

Do these today, they are quick:

- Add a simple API key header check on `/chat` so strangers cannot spend your money. A shared secret in an environment variable is enough for a demo.
- Set the global daily cost cap to something you can afford to lose.
- Add rate limiting: ten requests per minute per user id, in memory is fine.
- Log the trace id on every response so you can find it.
- Turn on the server side refusal fallbacks from day 1's production note in `llm.py`, since this is now a real service.

Write down what you did not do and why: Postgres, multiple workers, HTTPS termination details, log shipping. Knowing the gap is the professional answer.

## Step 4: a status page

`GET /status` returning: uptime, requests today, cost today, cache hit rate from your traces, last five trace ids. Render it as a tiny HTML table. That is your dashboard, and it is enough for the demo.

## Exercise, without AI

Explain to a friend why the API key is not in the image and what happens if it were.

## Check yourself

1. What is baked into the image and what is mounted?
2. Why one worker?
3. What does the platform do with the health check?
4. What would you change first with 100 users?

## Common mistakes

- Committing `.env`.
- Building the index at container start, so every restart takes minutes.
- A health check that calls the model.

## Done when

- Container runs locally.
- Live URL answers `/health` and streams `/chat`.
- API key gate, cap, and rate limit on.
- `/status` renders.
- Sticky note: "What does a recruiter look at first?"
