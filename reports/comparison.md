# StorySeek Retrieval Comparison

This report compares retrieval modes on the same query set and qrels.

| Mode | mean nDCG@10 | mean MRR@10 | mean Recall@20 | Queries |
|---|---:|---:|---:|---:|
| bm25 | 0.7058 | 1.0000 | 0.1692 | 8 |
| dense | 0.6786 | 1.0000 | 0.1573 | 8 |
| hybrid | 0.7304 | 1.0000 | 0.1642 | 8 |

## Notes

- BM25 is the lexical baseline with field boosting and metadata filters.
- Dense uses sentence-transformer embeddings and OpenSearch kNN search.
- Hybrid uses Reciprocal Rank Fusion over BM25 and Dense rankings.
- Current qrels are rule-derived from metadata, so dense semantic matches can be under-credited.

## Per-query Results

### bm25

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| q_001 | 1.0000 | 1.0000 | 0.1418 | slow burn rivals to lovers with found family |
| q_002 | 0.8975 | 1.0000 | 0.1136 | dark academia mystery with political intrigue and forbidden magic |
| q_003 | 0.5013 | 1.0000 | 0.1786 | found family adventure, no major character death |
| q_004 | 0.5947 | 1.0000 | 0.1653 | enemies to lovers with mutual pining |
| q_005 | 0.5351 | 1.0000 | 0.2532 | kingdom building fantasy without graphic violence |
| q_006 | 0.7092 | 1.0000 | 0.1980 | time loop coming of age story |
| q_007 | 0.8093 | 1.0000 | 0.1325 | academy setting with betrayal and redemption |
| q_008 | 0.5991 | 1.0000 | 0.1709 | hurt comfort found family healing story |

### dense

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| q_001 | 1.0000 | 1.0000 | 0.1418 | slow burn rivals to lovers with found family |
| q_002 | 0.7643 | 1.0000 | 0.1136 | dark academia mystery with political intrigue and forbidden magic |
| q_003 | 0.3608 | 1.0000 | 0.1548 | found family adventure, no major character death |
| q_004 | 0.5715 | 1.0000 | 0.1405 | enemies to lovers with mutual pining |
| q_005 | 0.6719 | 1.0000 | 0.2278 | kingdom building fantasy without graphic violence |
| q_006 | 0.7347 | 1.0000 | 0.1980 | time loop coming of age story |
| q_007 | 0.6989 | 1.0000 | 0.1192 | academy setting with betrayal and redemption |
| q_008 | 0.6265 | 1.0000 | 0.1624 | hurt comfort found family healing story |

### hybrid

| Query ID | nDCG@10 | MRR@10 | Recall@20 | Query |
|---|---:|---:|---:|---|
| q_001 | 1.0000 | 1.0000 | 0.1493 | slow burn rivals to lovers with found family |
| q_002 | 0.8930 | 1.0000 | 0.1136 | dark academia mystery with political intrigue and forbidden magic |
| q_003 | 0.5145 | 1.0000 | 0.1667 | found family adventure, no major character death |
| q_004 | 0.6059 | 1.0000 | 0.1570 | enemies to lovers with mutual pining |
| q_005 | 0.6439 | 1.0000 | 0.2405 | kingdom building fantasy without graphic violence |
| q_006 | 0.7424 | 1.0000 | 0.1980 | time loop coming of age story |
| q_007 | 0.7629 | 1.0000 | 0.1258 | academy setting with betrayal and redemption |
| q_008 | 0.6805 | 1.0000 | 0.1624 | hurt comfort found family healing story |
