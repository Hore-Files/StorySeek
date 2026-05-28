# StorySeek Retrieval Comparison

This report compares retrieval modes on the same query set and qrels.

| Mode | mean nDCG@10 | mean MRR@10 | mean Recall@20 | Queries |
|---|---:|---:|---:|---:|
| bm25 | 0.6159 | 1.0000 | 0.0144 | 4 |
| dense | 0.6425 | 1.0000 | 0.0200 | 4 |
| hybrid | 0.6721 | 1.0000 | 0.0202 | 4 |

## Notes

- BM25 is the lexical baseline with field boosting and metadata filters.
- Dense uses sentence-transformer embeddings and OpenSearch kNN search.
- Hybrid uses Reciprocal Rank Fusion over BM25 and Dense rankings.
- Current qrels are rule-derived from metadata, so dense semantic matches can be under-credited.

## Per-query Results

### bm25

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.7141 | 1.0000 | 0.0174 | detective mystery with burglary and hidden identity |
| gq_002 | 0.4523 | 1.0000 | 0.0203 | science fiction about telepathy and extrasensory perception |
| gq_003 | 0.6667 | 1.0000 | 0.0063 | adventure story for young readers set in Africa |
| gq_004 | 0.6307 | 1.0000 | 0.0137 | short ghost story with supernatural elements |

### dense

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.6464 | 1.0000 | 0.0214 | detective mystery with burglary and hidden identity |
| gq_002 | 0.4050 | 1.0000 | 0.0203 | science fiction about telepathy and extrasensory perception |
| gq_003 | 0.7182 | 1.0000 | 0.0075 | adventure story for young readers set in Africa |
| gq_004 | 0.8004 | 1.0000 | 0.0309 | short ghost story with supernatural elements |

### hybrid

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| gq_001 | 0.7141 | 1.0000 | 0.0241 | detective mystery with burglary and hidden identity |
| gq_002 | 0.5199 | 1.0000 | 0.0203 | science fiction about telepathy and extrasensory perception |
| gq_003 | 0.6667 | 1.0000 | 0.0071 | adventure story for young readers set in Africa |
| gq_004 | 0.7875 | 1.0000 | 0.0292 | short ghost story with supernatural elements |
