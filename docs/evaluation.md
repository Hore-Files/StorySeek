# Evaluation

StorySeek includes a small evaluation harness so retrieval changes can be measured, not just observed. This checkpoint reports BM25-only numbers; the harness is built to compare BM25 vs. Dense vs. Hybrid once those land.

## Datasets

| File | Purpose |
|---|---|
| `data/eval/queries.jsonl` | 8 hand-written natural-language queries with target tropes/themes/genres and optional excluded content warnings. |
| `data/eval/qrels.csv` | Graded relevance judgments per (query, work). |
| `reports/metrics.json` | Most recent metrics dump produced by `scripts/run_eval.py`. |

## Relevance scale

| Grade | Meaning |
|---|---|
| 3 | All target tropes, themes, and genres are present; no excluded warning. |
| 2 | At least one hit in each specified kind (trope/theme/genre), or all targets of a single kind match; no excluded warning. |
| 1 | Any single target overlap; no excluded warning. |
| 0 | No overlap, or the work contains a content warning the query excluded. |

## How qrels are produced

For the synthetic corpus we have no human-labeled gold set, so qrels are **rule-derived** from each query's `target_*` fields and each work's metadata. The rule is the relevance scale above, implemented in `scripts/generate_eval_qrels.py`. This keeps the eval story reproducible: regenerating `qrels.csv` is deterministic given `queries.jsonl` and `data/sample/works.jsonl`.

When we move to a real dataset (Project Gutenberg / Standard Ebooks metadata) the queries stay; the qrels will be hand-labeled by the team instead of derived.

## Metrics

- **nDCG@10** — graded gain discounted by rank; uses the qrel grades directly. Captures both whether top results are relevant and how relevant they are.
- **MRR@10** — reciprocal rank of the first result with relevance ≥ 1. Captures top-rank quality.
- **Recall@20** — fraction of judged-relevant docs returned in the top 20. Captures coverage.

Each query's metric is averaged uniformly across the query set.

## How to run

```bash
# 1. Start OpenSearch and build the index (one-time).
docker compose up -d opensearch
python scripts/build_index.py --recreate

# 2. (Re)generate qrels if you edited queries.jsonl or works.jsonl.
python scripts/generate_eval_qrels.py

# 3. Start the backend in another terminal.
uvicorn backend.app.main:app --port 8000

# 4. Run the eval.
python scripts/run_eval.py
# -> prints per-query and mean metrics
# -> writes reports/metrics.json
```

## Roadmap

| Method | Status |
|---|---|
| BM25 | Reported in `reports/metrics.json`. |
| Dense (sentence-transformers + OpenSearch knn_vector) | Planned. Same harness — just a different `mode`. |
| Hybrid BM25 + Dense via RRF | Planned. Reports will compare all three side-by-side. |

## Known limits of this checkpoint

- Qrels are rule-derived, not hand-labeled, so they reward exact metadata overlap and do not penalize a system for missing the "vibes" of a query. Once dense lands, this will under-credit it; we will mitigate by hand-labeling a small sample.
- The synthetic corpus is templated, so vocabulary diversity is low. Real text will be the harder test.
- Only 8 queries today. We will grow this set as we add features and observe gaps.
