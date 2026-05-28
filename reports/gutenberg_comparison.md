# StorySeek Retrieval Comparison

This report compares retrieval modes on the same query set and qrels.

- Queries: `data/eval/gutenberg_queries.jsonl`
- Qrels: `data/eval/gutenberg_qrels.csv`

| Mode | mean nDCG@10 | mean MRR@10 | mean Recall@20 | Queries |
|---|---:|---:|---:|---:|
| bm25 | 0.7492 | 1.0000 | 0.7303 | 8 |
| dense | 0.8040 | 1.0000 | 0.7830 | 8 |
| hybrid | 0.8082 | 1.0000 | 1.0000 | 8 |

## Notes

- BM25 is the lexical baseline with field boosting and metadata filters.
- Dense uses sentence-transformer embeddings and OpenSearch kNN search.
- Hybrid uses Reciprocal Rank Fusion over BM25 and Dense rankings.
- Current qrels are LLM-assisted pooled judgments over Project Gutenberg candidates.

## Per-query Results

### bm25

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.8829 | 1.0000 | 0.8889 | christmas ghost story about redemption and moral change |
| gq_002 | 0.7242 | 1.0000 | 0.6250 | king arthur knights chivalric adventure |
| gq_003 | 0.7060 | 1.0000 | 0.7692 | detective mystery involving murder and deception |
| gq_004 | 0.7294 | 1.0000 | 0.5714 | coming of age school adventure |
| gq_005 | 0.6541 | 1.0000 | 0.5385 | historical romance adventure with political intrigue |
| gq_006 | 0.9003 | 1.0000 | 0.9000 | supernatural ghost tales horror |
| gq_007 | 0.7543 | 1.0000 | 0.8571 | sea adventure survival and travel |
| gq_008 | 0.6425 | 1.0000 | 0.6923 | children fantasy adventure with animals |

### dense

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.8892 | 1.0000 | 0.8889 | christmas ghost story about redemption and moral change |
| gq_002 | 0.9192 | 1.0000 | 0.7500 | king arthur knights chivalric adventure |
| gq_003 | 0.8804 | 1.0000 | 0.9231 | detective mystery involving murder and deception |
| gq_004 | 0.5874 | 1.0000 | 0.6429 | coming of age school adventure |
| gq_005 | 0.6982 | 1.0000 | 0.5385 | historical romance adventure with political intrigue |
| gq_006 | 0.9283 | 1.0000 | 0.9000 | supernatural ghost tales horror |
| gq_007 | 0.8639 | 1.0000 | 0.9286 | sea adventure survival and travel |
| gq_008 | 0.6655 | 1.0000 | 0.6923 | children fantasy adventure with animals |

### hybrid

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.8865 | 1.0000 | 1.0000 | christmas ghost story about redemption and moral change |
| gq_002 | 0.8833 | 1.0000 | 1.0000 | king arthur knights chivalric adventure |
| gq_003 | 0.8074 | 1.0000 | 1.0000 | detective mystery involving murder and deception |
| gq_004 | 0.7938 | 1.0000 | 1.0000 | coming of age school adventure |
| gq_005 | 0.6382 | 1.0000 | 1.0000 | historical romance adventure with political intrigue |
| gq_006 | 0.8543 | 1.0000 | 1.0000 | supernatural ghost tales horror |
| gq_007 | 0.8972 | 1.0000 | 1.0000 | sea adventure survival and travel |
| gq_008 | 0.7048 | 1.0000 | 1.0000 | children fantasy adventure with animals |
