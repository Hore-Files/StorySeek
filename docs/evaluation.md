# Evaluation

StorySeek includes an evaluation harness so retrieval changes can be measured instead of only demonstrated manually. The harness compares BM25, Dense, and Hybrid retrieval on the same query set and qrels.

## Datasets

| File | Purpose |
|---|---|
| `data/eval/queries.jsonl` | 8 natural-language queries with target tropes, themes, genres, and optional excluded warnings. |
| `data/eval/qrels.csv` | Graded relevance judgments per `(query, work)`. |
| `reports/metrics.json` | Latest machine-readable metrics dump from `scripts/run_eval.py`. |
| `reports/comparison.md` | Latest human-readable comparison table. |

## Relevance scale

| Grade | Meaning |
|---|---|
| 3 | All target tropes, themes, and genres are present; no excluded warning. |
| 2 | At least one hit in each specified category, or all targets of a single category match; no excluded warning. |
| 1 | Any single target overlap; no excluded warning. |
| 0 | No overlap, or the work contains an excluded content warning. |

## How qrels are produced

The current corpus is synthetic, so qrels are rule-derived from query targets and work metadata. This is deterministic and reproducible through `scripts/generate_eval_qrels.py`.

Rule-derived qrels are useful for regression testing and controlled comparisons, but they favor exact metadata overlap. Dense retrieval can find semantically plausible matches that this qrel set under-credits, so a small hand-labeled subset should be added before making strong claims about semantic wins.

## Metrics

- **nDCG@10** - graded relevance discounted by rank.
- **MRR@10** - reciprocal rank of the first result with relevance at least 1.
- **Recall@20** - fraction of judged-relevant docs returned in the top 20.

Each query contributes equally to the mean.

## How to run

```bash
# 1. Start OpenSearch and build the index.
docker compose up -d opensearch
python scripts/build_index.py --recreate

# 2. Regenerate qrels if queries or works changed.
python scripts/generate_eval_qrels.py

# 3. Start the backend in another terminal.
uvicorn backend.app.main:app --port 8000

# 4. Compare retrieval modes.
python scripts/run_eval.py
# -> prints per-query and mean metrics
# -> writes reports/metrics.json and reports/comparison.md
```

To evaluate only selected modes:

```bash
python scripts/run_eval.py --modes bm25 dense
```

## Current methods

| Method | Status |
|---|---|
| BM25 | Implemented and evaluated by `scripts/run_eval.py`. |
| Dense | Implemented and evaluated by `scripts/run_eval.py`. |
| Hybrid | Implemented with Reciprocal Rank Fusion and evaluated by `scripts/run_eval.py`. |

## Known limits

- Qrels are rule-derived, not hand-labeled.
- The synthetic corpus is intentionally schema-rich but vocabulary-limited.
- There are only 8 eval queries, so the metrics are a project demo signal, not a benchmark-grade result.
