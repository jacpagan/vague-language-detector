#!/usr/bin/env python3
"""Objective Language Detector stress test (stdlib-only).

Sends concurrent POST requests to /classify and reports:
- requests/sec
- error rate
- latency percentiles (p50/p95/p99)

Example:
  python scripts/stress_test.py --url http://127.0.0.1:8000/classify --concurrency 50 --duration 20
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional, Tuple


DEFAULT_TEXTS = [
    "I practice coding daily.",
    "I always mess everything up.",
    "I am a failure.",
    "It is either a total success or a complete failure.",
    "This failed yesterday.",
    "No one ever listens.",
    "I write tests and refactor.",
    "You are useless.",
    "Nothing works.",
    "We shipped the fix.",
]


@dataclass
class Result:
    ok: bool
    status: Optional[int]
    latency_ms: float
    error: Optional[str] = None


def percentile(sorted_values: List[float], p: float) -> float:
    if not sorted_values:
        return float("nan")
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def do_request(url: str, timeout_s: float, texts: List[str]) -> Result:
    payload = {"text": random.choice(texts)}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        method="POST",
        data=data,
        headers={"Content-Type": "application/json"},
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read()
            latency_ms = (time.perf_counter() - start) * 1000.0

            # Validate response is JSON and contains required key.
            try:
                parsed = json.loads(body.decode("utf-8"))
            except Exception:
                return Result(
                    ok=False,
                    status=getattr(resp, "status", None),
                    latency_ms=latency_ms,
                    error="invalid_json",
                )

            ok = (
                isinstance(parsed, dict)
                and "has_cognitive_distortion" in parsed
                and isinstance(parsed["has_cognitive_distortion"], bool)
            )
            return Result(
                ok=ok,
                status=getattr(resp, "status", None),
                latency_ms=latency_ms,
                error=None if ok else "invalid_schema",
            )

    except urllib.error.HTTPError as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return Result(ok=False, status=e.code, latency_ms=latency_ms, error=f"http_{e.code}")
    except urllib.error.URLError as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return Result(ok=False, status=None, latency_ms=latency_ms, error=f"url_error:{e}")
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return Result(ok=False, status=None, latency_ms=latency_ms, error=f"exception:{type(e).__name__}:{e}")


def worker_loop(
    *,
    stop_event: threading.Event,
    url: str,
    timeout_s: float,
    texts: List[str],
    results: List[Result],
    results_lock: threading.Lock,
    max_requests: Optional[int],
    counter: List[int],
    counter_lock: threading.Lock,
) -> None:
    while not stop_event.is_set():
        # Respect max_requests globally.
        if max_requests is not None:
            with counter_lock:
                if counter[0] >= max_requests:
                    stop_event.set()
                    break
                counter[0] += 1

        r = do_request(url=url, timeout_s=timeout_s, texts=texts)
        with results_lock:
            results.append(r)


def run(concurrency: int, duration_s: float, url: str, timeout_s: float, max_requests: Optional[int], texts: List[str]) -> Tuple[float, List[Result]]:
    stop_event = threading.Event()
    results: List[Result] = []
    results_lock = threading.Lock()
    counter = [0]
    counter_lock = threading.Lock()

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for _ in range(concurrency):
            pool.submit(
                worker_loop,
                stop_event=stop_event,
                url=url,
                timeout_s=timeout_s,
                texts=texts,
                results=results,
                results_lock=results_lock,
                max_requests=max_requests,
                counter=counter,
                counter_lock=counter_lock,
            )

        # Run for duration or until max_requests reached.
        if max_requests is None:
            time.sleep(duration_s)
            stop_event.set()
        else:
            while not stop_event.is_set():
                time.sleep(0.05)

    elapsed = time.perf_counter() - start
    return elapsed, results


def main() -> int:
    parser = argparse.ArgumentParser(description="Stress test Objective Language Detector /classify")
    parser.add_argument("--url", default="http://127.0.0.1:8000/classify", help="Full classify URL")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrent workers")
    parser.add_argument("--duration", type=float, default=15.0, help="Seconds to run (ignored if --requests is set)")
    parser.add_argument("--requests", type=int, default=None, help="Max total requests (overrides --duration)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Per-request timeout (seconds)")
    parser.add_argument("--seed", type=int, default=1337, help="RNG seed")
    args = parser.parse_args()

    if args.concurrency < 1:
        raise SystemExit("--concurrency must be >= 1")

    random.seed(args.seed)

    elapsed, results = run(
        concurrency=args.concurrency,
        duration_s=args.duration,
        url=args.url,
        timeout_s=args.timeout,
        max_requests=args.requests,
        texts=DEFAULT_TEXTS,
    )

    total = len(results)
    oks = [r for r in results if r.ok]
    errors = [r for r in results if not r.ok]
    latencies = sorted([r.latency_ms for r in results])

    rps = (total / elapsed) if elapsed > 0 else 0.0
    err_rate = (len(errors) / total * 100.0) if total else 0.0

    print("=== Stress test results ===")
    print(f"url         : {args.url}")
    print(f"concurrency : {args.concurrency}")
    if args.requests is None:
        print(f"duration    : {args.duration:.2f}s")
    else:
        print(f"requests    : {args.requests}")
    print(f"elapsed     : {elapsed:.2f}s")
    print(f"total       : {total}")
    print(f"ok          : {len(oks)}")
    print(f"errors      : {len(errors)} ({err_rate:.2f}%)")
    print(f"throughput  : {rps:.1f} req/s")

    if total:
        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        mean = statistics.mean(latencies)
        print("latency_ms  : " f"mean={mean:.2f}  p50={p50:.2f}  p95={p95:.2f}  p99={p99:.2f}  max={latencies[-1]:.2f}")

    if errors:
        # show a small breakdown
        counts = {}
        for e in errors:
            counts[e.error or "unknown"] = counts.get(e.error or "unknown", 0) + 1
        top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
        print("error_breakdown:")
        for k, v in top:
            print(f"  - {k}: {v}")

    # Non-zero exit if anything failed.
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
