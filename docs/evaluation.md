# Evaluation

StorySeek includes a small retrieval evaluation harness so ranking changes can be compared instead of only demonstrated manually.

## Files

| File | Purpose |
|---|---|
| `data/eval/queries.jsonl` | Natural-language eval queries and optional excluded warnings. |
| `data/eval/qrels.csv` | Rule-derived graded relevance labels. |
| `data/eval/gutenberg_queries.jsonl` | Natural-language eval queries for the Project Gutenberg corpus. |
| `data/eval/gutenberg_qrels.csv` | LLM-assisted pooled relevance labels for Gutenberg candidates. |
| `scripts/generate_eval_qrels.py` | Rebuilds qrels from queries and synthetic work metadata. |
| `scripts/run_eval.py` | Calls the running backend and computes metrics. Supports `/search` and `/search-content`. |
| `reports/metrics.json` | Machine-readable eval output. |
| `reports/comparison.md` | Human-readable comparison table. |
| `reports/gutenberg_metrics.json` | Machine-readable Gutenberg eval output. |
| `reports/gutenberg_comparison.md` | Human-readable Gutenberg comparison table. |

## Relevance Scale

| Grade | Meaning |
|---|---|
| 3 | Strong metadata match and no excluded warning. |
| 2 | Relevant but missing one soft preference. |
| 1 | Weakly related metadata overlap. |
| 0 | Irrelevant or violates an excluded warning. |

The synthetic qrels are deterministic and rule-derived from synthetic metadata. This is useful for regression checks, but it is not a substitute for human relevance labels.

The Gutenberg qrels use pooled judgments: candidate works were collected from the top BM25, dense, and hybrid results, then graded 0-3 with LLM assistance using title, summary, and metadata. This is stronger than synthetic rule-derived qrels for the deployed real corpus, but it is still prototype evidence rather than benchmark-grade human annotation.

## Metrics

- nDCG@10: graded relevance with rank discount.
- MRR@10: reciprocal rank of the first relevant result.
- Recall@20: fraction of judged-relevant documents retrieved in the top 20.

## How To Run

Start OpenSearch, build the indexes, and run the backend first:

```bash
docker compose up -d opensearch
python scripts/build_index.py --recreate --path data/sample/works_gutenberg.jsonl
python scripts/build_chunk_index.py --recreate
uvicorn backend.app.main:app --port 8000
```

Then run:

```bash
python scripts/run_eval.py --modes bm25 dense hybrid
```

For the Project Gutenberg corpus:

```bash
python scripts/run_eval.py \
  --endpoint /search-content \
  --queries data/eval/gutenberg_queries.jsonl \
  --qrels data/eval/gutenberg_qrels.csv \
  --out reports/gutenberg_metrics.json \
  --comparison-out reports/gutenberg_comparison.md \
  --modes bm25 dense hybrid
```

Expected outputs:

- console metrics per query and per mode,
- `reports/metrics.json`,
- `reports/comparison.md`.

Use `/search` to evaluate work-level retrieval, and `/search-content` to evaluate the current frontend path: passage/chunk retrieval grouped back to works.

## Interpretation

Evaluation numbers should be described as prototype evidence only. The synthetic qrels reward exact metadata overlap, so dense retrieval may find semantically plausible matches that receive low rule-derived relevance. Before making strong claims about hybrid or dense superiority, add a small hand-labeled pooled set.

For the current Gutenberg report, hybrid has the strongest recall because it fuses candidates from both lexical and dense retrieval. Dense has slightly stronger mean nDCG than BM25 on the current LLM-assisted labels, but the small query count and AI-assisted judgments should be disclosed. After chunk deployment, the Gutenberg report should be regenerated with `--endpoint /search-content`.
