# Evaluation

StorySeek includes a small retrieval evaluation harness so ranking changes can be compared instead of only demonstrated manually.

## Files

| File | Purpose |
|---|---|
| `data/eval/queries.jsonl` | Natural-language eval queries and optional excluded warnings. |
| `data/eval/qrels.csv` | Rule-derived graded relevance labels. |
| `scripts/generate_eval_qrels.py` | Rebuilds qrels from queries and synthetic work metadata. |
| `scripts/run_eval.py` | Calls the running backend and computes metrics. |
| `reports/metrics.json` | Machine-readable eval output. |
| `reports/comparison.md` | Human-readable comparison table. |

## Relevance Scale

| Grade | Meaning |
|---|---|
| 3 | Strong metadata match and no excluded warning. |
| 2 | Relevant but missing one soft preference. |
| 1 | Weakly related metadata overlap. |
| 0 | Irrelevant or violates an excluded warning. |

The current qrels are deterministic and rule-derived from the synthetic metadata. This is useful for regression checks, but it is not a substitute for human relevance labels.

These qrels target `data/sample/works.jsonl` IDs (`w_####`). They do not evaluate the optional Project Gutenberg dataset (`g_####`) until a new hand-labeled or regenerated qrels file is created for that corpus.

## Metrics

- nDCG@10: graded relevance with rank discount.
- MRR@10: reciprocal rank of the first relevant result.
- Recall@20: fraction of judged-relevant documents retrieved in the top 20.

## How To Run

Start OpenSearch, build the index, and run the backend first:

```bash
docker compose up -d opensearch
python scripts/build_index.py --recreate
uvicorn backend.app.main:app --port 8000
```

Then run:

```bash
python scripts/run_eval.py --modes bm25 dense hybrid
```

Expected outputs:

- console metrics per query and per mode,
- `reports/metrics.json`,
- `reports/comparison.md`.

## Interpretation

Evaluation numbers should be described as prototype evidence only. The synthetic qrels reward exact metadata overlap, so dense retrieval may find semantically plausible matches that receive low rule-derived relevance. Before making strong claims about hybrid or dense superiority, add a small hand-labeled pooled set.
