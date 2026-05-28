# StorySeek Retrieval Comparison

This report compares retrieval modes on the same query set and qrels.

- Queries: `data/eval/gutenberg_queries.jsonl`
- Qrels: `data/eval/gutenberg_qrels.csv`
- Endpoint: `/search-content`

| Mode | mean nDCG@10 | mean MRR@10 | mean Recall@20 | Queries |
|---|---:|---:|---:|---:|
| bm25 | 0.1958 | 0.4345 | 0.3010 | 8 |
| dense | 0.4261 | 0.7470 | 0.5799 | 8 |
| hybrid | 0.4221 | 0.7304 | 0.5058 | 8 |

## Notes

- BM25 is the lexical baseline with field boosting and metadata filters.
- Dense uses sentence-transformer embeddings and OpenSearch kNN search.
- Hybrid uses Reciprocal Rank Fusion over BM25 and Dense rankings.
- `/search` evaluates work-level retrieval; `/search-content` evaluates passage/chunk retrieval grouped back to works.
- Current qrels are LLM-assisted pooled judgments over Project Gutenberg candidates.

## Per-query Results

### bm25

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.2732 | 1.0000 | 0.5556 | christmas ghost story about redemption and moral change |
| gq_002 | 0.5274 | 1.0000 | 0.5000 | king arthur knights chivalric adventure |
| gq_003 | 0.2733 | 0.3333 | 0.3077 | detective mystery involving murder and deception |
| gq_004 | 0.2126 | 0.5000 | 0.2143 | coming of age school adventure |
| gq_005 | 0.0000 | 0.0000 | 0.0769 | historical romance adventure with political intrigue |
| gq_006 | 0.2218 | 0.5000 | 0.6000 | supernatural ghost tales horror |
| gq_007 | 0.0000 | 0.0000 | 0.0000 | sea adventure survival and travel |
| gq_008 | 0.0582 | 0.1429 | 0.1538 | children fantasy adventure with animals |

### dense

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.5667 | 1.0000 | 0.8889 | christmas ghost story about redemption and moral change |
| gq_002 | 0.5734 | 1.0000 | 0.5000 | king arthur knights chivalric adventure |
| gq_003 | 0.3021 | 0.3333 | 0.6923 | detective mystery involving murder and deception |
| gq_004 | 0.4055 | 1.0000 | 0.5000 | coming of age school adventure |
| gq_005 | 0.1336 | 0.1429 | 0.1538 | historical romance adventure with political intrigue |
| gq_006 | 0.7364 | 1.0000 | 0.8000 | supernatural ghost tales horror |
| gq_007 | 0.4608 | 0.5000 | 0.6429 | sea adventure survival and travel |
| gq_008 | 0.2306 | 1.0000 | 0.4615 | children fantasy adventure with animals |

### hybrid

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.6386 | 1.0000 | 0.8889 | christmas ghost story about redemption and moral change |
| gq_002 | 0.6412 | 1.0000 | 0.5000 | king arthur knights chivalric adventure |
| gq_003 | 0.4116 | 1.0000 | 0.4615 | detective mystery involving murder and deception |
| gq_004 | 0.5002 | 1.0000 | 0.4286 | coming of age school adventure |
| gq_005 | 0.0702 | 0.1429 | 0.0769 | historical romance adventure with political intrigue |
| gq_006 | 0.5108 | 1.0000 | 0.8000 | supernatural ghost tales horror |
| gq_007 | 0.3682 | 0.5000 | 0.4286 | sea adventure survival and travel |
| gq_008 | 0.2359 | 0.2000 | 0.4615 | children fantasy adventure with animals |
