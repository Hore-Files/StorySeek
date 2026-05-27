# StorySeek Load Test Results

Lightweight local load test against `POST /search`.

| Mode | Concurrency | Requests | Success rate | p50 ms | p95 ms | max ms |
|---|---:|---:|---:|---:|---:|---:|
| bm25 | 10 | 30 | 100.0% | 561.7 | 658.0 | 671.0 |
| bm25 | 50 | 150 | 100.0% | 1425.3 | 2366.2 | 2405.1 |
| bm25 | 100 | 300 | 100.0% | 3906.3 | 6672.9 | 7100.8 |
| hybrid | 10 | 30 | 100.0% | 496.3 | 602.2 | 608.0 |
| hybrid | 50 | 150 | 100.0% | 1230.8 | 2236.1 | 2368.0 |
| hybrid | 100 | 300 | 100.0% | 6705.0 | 9634.0 | 10277.7 |

## Method

- Each request uses the same API path as the UI.
- Queries include natural-language trope/theme searches and content-warning exclusion.
- Results are intended as local prototype evidence, not production capacity guarantees.