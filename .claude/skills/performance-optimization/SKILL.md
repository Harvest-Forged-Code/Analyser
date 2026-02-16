# ---
# name: performance-optimization
# description: >
#   Use when profiling and optimizing code for performance — bottleneck
#   identification, caching, async patterns, DB query optimization, memory
#   reduction, and latency improvement.
# trigger: >
#   When user reports slow performance, asks for optimization, profiling,
#   or mentions high latency, slow queries, memory pressure, or CPU spikes.
# references:
#   - CLAUDE.md [ARCHITECTURE] caching and async patterns
# ---

# Performance Optimization Skill

## Purpose

Systematically identify and resolve performance bottlenecks using profiling,
categorization, and targeted optimization techniques. Every optimization must
be backed by before/after benchmarks and protected by regression tests.

## Workflow — Follow Each Step in Order

### Step 1: Identify the Performance Complaint

Ask clarifying questions or inspect the reported issue to determine what is slow:

- **Slow endpoint** — HTTP response time exceeds acceptable threshold
- **Slow query** — Database queries taking too long or running too frequently
- **High memory** — Process memory grows unbounded or exceeds limits
- **High CPU** — CPU saturation during specific operations
- **Slow startup** — Application boot time is excessive
- **Slow batch job** — Scheduled or background tasks taking too long

Document the specific symptom, the affected code path, and any available metrics
(response time, p50/p95/p99 latencies, memory usage, query counts).

### Step 2: Explore the Relevant Code Path End-to-End

Trace the full execution path from entry point to completion:

- Identify the entry point (route handler, CLI command, cron job, message consumer)
- Map every function call, service interaction, and I/O operation in the path
- Note external dependencies: databases, caches, APIs, file systems, queues
- Identify any middleware, decorators, or interceptors in the path
- Check for existing caching, connection pooling, or optimization attempts

### Step 3: Profile — Add Timing and Logging at Each Stage

Insert instrumentation to measure where time is actually spent:

- Add timing decorators or context managers around each major stage
- Log wall-clock time, CPU time, and I/O wait time separately
- For database paths: enable query logging with execution times
- For HTTP paths: log time-to-first-byte and total response time
- For memory concerns: snapshot heap usage before and after key operations

Example instrumentation pattern:
```python
import time
import logging

logger = logging.getLogger(__name__)

def timed_section(name):
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, *args):
            elapsed = time.perf_counter() - self.start
            logger.info(f"[PERF] {name}: {elapsed:.4f}s")
    return Timer()

# Usage
with timed_section("fetch_user_data"):
    user = db.query(User).filter_by(id=user_id).first()
```

### Step 4: Categorize the Bottleneck

Based on profiling results, classify the bottleneck into one of four categories:

| Category       | Indicators                                                        |
|----------------|-------------------------------------------------------------------|
| **CPU-bound**  | High CPU usage, slow computation, no I/O wait                     |
| **I/O-bound**  | Low CPU, long wait times on network/disk, many sequential calls   |
| **Query-bound**| Slow SQL queries, high query count (N+1), missing indexes         |
| **Memory-bound**| High memory usage, frequent GC, large object allocations          |

If multiple categories apply, address them in order of greatest impact.

### Step 5: Fix I/O-Bound Bottlenecks

Apply these techniques for I/O-bound problems:

- **Convert sequential I/O to async**: Use `asyncio`, `aiohttp`, `httpx` for
  concurrent HTTP calls; use async DB drivers (`asyncpg`, `aiomysql`)
- **Add connection pooling**: Configure pool sizes for DB connections, HTTP
  sessions, and Redis connections; reuse connections across requests
- **Batch requests**: Replace N individual API calls with a single batch call;
  use `IN` clauses instead of loops of single-row queries
- **Add timeouts**: Set connect and read timeouts on all external calls to
  prevent indefinite waits
- **Use streaming**: For large payloads, stream data instead of buffering
  entire response in memory

```python
# BEFORE: Sequential HTTP calls
results = []
for url in urls:
    resp = requests.get(url)
    results.append(resp.json())

# AFTER: Concurrent HTTP calls
import asyncio
import httpx

async def fetch_all(urls):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

### Step 6: Fix CPU-Bound Bottlenecks

Apply these techniques for CPU-bound problems:

- **Optimize the algorithm**: Replace O(n^2) with O(n log n); use appropriate
  data structures (sets for membership, dicts for lookup)
- **Add caching**: Use `functools.lru_cache` for pure functions; use Redis or
  Memcached for shared/distributed caching; set appropriate TTLs
- **Precompute**: Move expensive computations to build time or startup time
  when inputs are known in advance
- **Offload to async workers**: Use Celery, RQ, or similar task queues to move
  heavy computation out of the request path
- **Use efficient serialization**: Replace JSON with msgpack or protobuf for
  internal communication; avoid repeated serialization

```python
# BEFORE: Recomputes expensive result every call
def get_report(user_id):
    data = fetch_all_transactions(user_id)
    return compute_aggregates(data)  # expensive

# AFTER: Cache with TTL
from functools import lru_cache
import redis

cache = redis.Redis()

def get_report(user_id):
    cache_key = f"report:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    data = fetch_all_transactions(user_id)
    result = compute_aggregates(data)
    cache.setex(cache_key, 300, json.dumps(result))  # 5 min TTL
    return result
```

### Step 7: Fix Query-Bound Bottlenecks

Apply these techniques for database query problems:

- **Analyze query plans**: Run `EXPLAIN ANALYZE` on slow queries; look for
  sequential scans, nested loops, and high row estimates
- **Add indexes**: Create indexes on columns used in WHERE, JOIN, and ORDER BY
  clauses; use composite indexes for multi-column filters
- **Fix N+1 queries**: Use eager loading (`joinedload`, `selectinload` in
  SQLAlchemy; `select_related`, `prefetch_related` in Django)
- **Optimize ORM usage**: Use `.only()` or `.defer()` to load only needed
  columns; avoid loading entire objects when only IDs are needed
- **Use database-level aggregation**: Push SUM, COUNT, GROUP BY to the database
  instead of computing in application code
- **Add query result caching**: Cache frequently-read, rarely-changed query
  results with appropriate invalidation

```python
# BEFORE: N+1 query — 1 query for orders + N queries for users
orders = session.query(Order).all()
for order in orders:
    print(order.user.name)  # triggers lazy load each iteration

# AFTER: Eager load with joinedload — 1 query total
from sqlalchemy.orm import joinedload
orders = session.query(Order).options(joinedload(Order.user)).all()
for order in orders:
    print(order.user.name)  # no additional query
```

### Step 8: Fix Memory-Bound Bottlenecks

Apply these techniques for memory problems:

- **Use generators**: Replace list comprehensions with generator expressions
  for large datasets; use `yield` instead of building lists in memory
- **Reduce data copies**: Avoid unnecessary `.copy()` calls; use views/slices
  where possible; process data in chunks
- **Profile with memory_profiler**: Use `@profile` decorator or
  `memory_usage()` to identify allocation hotspots
- **Use appropriate data types**: Use `__slots__` on frequently-instantiated
  classes; use `array` module or NumPy for numeric data instead of lists
- **Implement streaming processing**: Process large files line-by-line instead
  of loading entirely into memory

```python
# BEFORE: Loads all rows into memory
def process_large_file(path):
    with open(path) as f:
        data = f.readlines()  # entire file in memory
    return [transform(line) for line in data]

# AFTER: Generator-based streaming
def process_large_file(path):
    with open(path) as f:
        for line in f:  # one line at a time
            yield transform(line)
```

### Step 9: Implement Fix with Before/After Benchmarks

- Record the baseline metric before making changes (response time, query count,
  memory peak, CPU usage)
- Implement the optimization using the technique from the applicable step above
- Record the same metric after the change
- Document the improvement as a percentage and absolute value
- If improvement is less than 10%, reconsider whether the optimization is
  worthwhile given added complexity

### Step 10: Write Regression Test

Create a test that will fail if the performance bottleneck is reintroduced:

```python
import time
import pytest

def test_endpoint_response_time():
    """Regression test: /api/reports must respond within 500ms."""
    start = time.perf_counter()
    response = client.get("/api/reports")
    elapsed = time.perf_counter() - start
    assert response.status_code == 200
    assert elapsed < 0.5, f"Response took {elapsed:.2f}s, exceeds 500ms threshold"

def test_query_count(django_assert_num_queries):
    """Regression test: report generation must use <= 5 queries."""
    with django_assert_num_queries(5):
        generate_report(user_id=1)
```

### Step 11: Verify

Run the complete verification sequence:

1. Run the specific benchmark to confirm the improvement meets expectations
2. Run the full test suite to confirm no regressions
3. Review the change against CLAUDE.md [ARCHITECTURE] caching and async patterns
4. Confirm the optimization does not introduce new failure modes (cache
   stampede, connection pool exhaustion, race conditions)
5. Document the optimization: what was slow, why, what was changed, and the
   measured improvement

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during performance optimization MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during performance optimization MUST follow this format:
- **Signed commits**: Always use `git commit -S`
- **Semantic prefix**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `ci:`
- **File-change table** in the commit body:
  ```
  type: concise description

  | File (Location) | Summary of Change |
  |---|---|
  | path/to/file.py | What changed in this file |

  Author: PrabhukumarSivamoorthy@gmail.com
  ```
- See CLAUDE.md [GIT] for full specification.

## Checklist Before Completion

- [ ] Bottleneck identified and categorized
- [ ] Root cause understood (not just symptom treated)
- [ ] Before/after benchmarks recorded
- [ ] Regression test written and passing
- [ ] Full test suite passing
- [ ] No new failure modes introduced
- [ ] Change documented with metrics
- [ ] Consistent with CLAUDE.md [ARCHITECTURE] patterns
