#!/usr/bin/env python3
"""Measure the real speed of an OpenAI-compatible endpoint.

    python3 scripts/bench_llm.py

Standard library only, so it runs on the Linux box with no venv and no installs.

Reports two numbers that are usually confused, and have different fixes:

  TTFT     time to first token. Queueing plus prefill. Grows with prompt
           length, and is what prefix caching improves.
  decode   tokens per second AFTER the first token. Depends on model size,
           quantization kernel and memory bandwidth, and is flat regardless
           of how long your prompt was.

An agent turn pays TTFT once and decode for every token it writes, so a slow
agent with short outputs is a TTFT problem and a slow agent with long outputs
is a decode problem. Averaging them together hides which one you have.

Env: VLLM_HOST, VLLM_API_KEY, BENCH_MODEL, BENCH_RUNS, BENCH_MAX_TOKENS
"""
import json, os, time, urllib.request

BASE = os.getenv("VLLM_HOST", "http://localhost:8000").rstrip("/")
KEY = os.getenv("VLLM_API_KEY", "local-dev-key")
MODEL = os.getenv("BENCH_MODEL", "local")
RUNS = int(os.getenv("BENCH_RUNS", "3"))
MAX_TOKENS = int(os.getenv("BENCH_MAX_TOKENS", "400"))


def one_run(n):
    body = {
        "model": MODEL,
        # Vary the prompt per run so prefix caching does not flatter the TTFT.
        "messages": [{"role": "user", "content":
                      f"Write {40 + n} numbered facts about how neural networks "
                      f"are trained. One short sentence each, no preamble."}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    req = urllib.request.Request(
        f"{BASE}/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "content-type": "application/json"},
    )
    t0 = time.perf_counter()
    first = last = None
    seen = 0
    usage = None
    with urllib.request.urlopen(req) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            chunk = json.loads(payload)
            if chunk.get("usage"):
                usage = chunk["usage"]
            for choice in chunk.get("choices", []):
                if choice.get("delta", {}).get("content"):
                    now = time.perf_counter()
                    first = now if first is None else first
                    last = now
                    seen += 1

    if first is None:
        raise RuntimeError("no content tokens streamed back")

    # Prefer the server's own count; fall back to counting chunks.
    out = usage["completion_tokens"] if usage else seen
    prompt = usage["prompt_tokens"] if usage else 0
    ttft = first - t0
    decode_s = last - first
    # The first token is excluded: its cost is TTFT, not decode.
    rate = (out - 1) / decode_s if decode_s > 0 and out > 1 else float("nan")
    return ttft, rate, out, prompt, time.perf_counter() - t0


def main():
    print(f"endpoint {BASE}  model {MODEL}  max_tokens {MAX_TOKENS}\n")
    print(f"{'run':>4}  {'TTFT':>8}  {'decode':>12}  {'out':>5}  {'in':>5}  {'total':>7}")
    rates = []
    for i in range(RUNS):
        ttft, rate, out, prompt, total = one_run(i)
        rates.append(rate)
        print(f"{i+1:>4}  {ttft*1000:>6.0f}ms  {rate:>7.1f} tok/s  "
              f"{out:>5}  {prompt:>5}  {total:>6.1f}s")

    best = max(rates)
    print(f"\nbest decode: {best:.1f} tok/s")
    print("""
How to judge that number
------------------------
Single-stream decode is memory-bound: every token reads the entire weight set
once, so the ceiling is roughly (memory bandwidth / weight size).

  RTX 5060 Ti     448 GB/s
  7B at 4-bit     ~4 GB (4-bit weights plus fp16 embeddings and norms)
  ceiling         ~110 tok/s

Real kernels reach 70-80% of that. Measured on this exact setup, Qwen2.5-7B
AWQ on a 5060 Ti: 84 tok/s decode, 26ms TTFT. Treat that as the target.

Under about 60 means a configuration problem, not a slow card. Check the
quantization kernel first, it is the usual culprit and it fails silently:

  docker compose -f docker-compose.course.yml logs vllm-course | grep -i marlin

Record your best number in the day 0 log. It is the baseline you compare
against when you swap models on day 13.""")


if __name__ == "__main__":
    main()
