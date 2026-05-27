# StorySeek Load Test Results

Lightweight local load test against `POST /search`.

## Environment

- OS: Microsoft Windows 11 Home Single Language
- CPU: AMD Ryzen 5 6600H with Radeon Graphics
- RAM: 15.2 GB
- Python: 3.12.10
- Node.js: v22.14.0
- OpenSearch: single Docker node, 512 MB heap (`-Xms512m -Xmx512m`)
- Dataset: 300 synthetic works in a 1-primary / 0-replica local index
- Backend: one local Uvicorn process

| Mode | Concurrency | Requests | Success rate | p50 ms | p95 ms | max ms |
|---|---:|---:|---:|---:|---:|---:|
| bm25 | 10 | 30 | 100.0% | 498.2 | 585.9 | 607.1 |
| bm25 | 50 | 150 | 100.0% | 1522.8 | 2829.9 | 3055.5 |
| bm25 | 100 | 300 | 100.0% | 4532.6 | 7693.5 | 8357.8 |
| hybrid | 10 | 30 | 100.0% | 757.3 | 884.2 | 894.2 |
| hybrid | 50 | 150 | 100.0% | 1811.7 | 3267.2 | 3478.6 |
| hybrid | 100 | 300 | 100.0% | 5267.3 | 8827.2 | 9400.0 |

## Method

- Each request uses the same API path as the UI.
- Queries include natural-language trope/theme searches and content-warning exclusion.
- Results are intended as local prototype evidence, not production capacity guarantees.
