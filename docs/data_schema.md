# Data schema

Every record in the catalog is a `work`.

## Example

```json
{
  "work_id": "w_0001",
  "title": "The Clocktower Pact",
  "creator": "Synthetic Author",
  "format": "novel",
  "summary": "Two rival students at a magical academy uncover a conspiracy involving forbidden time magic.",
  "genres": ["fantasy", "mystery"],
  "themes": ["dark academia", "political intrigue"],
  "tropes": ["rivals to lovers", "forbidden magic", "slow burn"],
  "relationship_dynamics": ["rivals", "found family"],
  "content_warnings": ["violence"],
  "audience_rating": "Teen",
  "status": "Complete",
  "length_bucket": "medium",
  "language": "English",
  "source": "synthetic"
}
```

## Fields

| Field | Type | Cardinality | Notes |
|---|---|---|---|
| `work_id` | string | 1 | Stable id, `w_####` for synthetic data |
| `title` | string | 1 | Free text |
| `creator` | string | 1 | Author/creator name |
| `format` | enum | 1 | See below |
| `summary` | string | 1 | 1–3 sentences |
| `genres` | enum[] | 1..n | |
| `themes` | enum[] | 0..n | |
| `tropes` | enum[] | 0..n | |
| `relationship_dynamics` | string[] | 0..n | |
| `content_warnings` | enum[] | 0..n | May be `["none"]` |
| `audience_rating` | enum | 1 | `General` \| `Teen` \| `Mature` |
| `status` | enum | 1 | `Complete` \| `Ongoing` \| `Hiatus` |
| `length_bucket` | enum | 1 | `short` \| `medium` \| `long` |
| `language` | string | 1 | ISO-ish English label |
| `source` | string | 1 | `synthetic` for now |

## Controlled vocabularies

### `format`
`novel`, `short_story`, `fanfic_style`, `manga`, `webnovel`

### `genres`
`fantasy`, `mystery`, `romance`, `science fiction`, `horror`, `historical`, `adventure`, `drama`, `comedy`

### `themes`
`dark academia`, `political intrigue`, `healing`, `revenge`, `redemption`, `grief`, `betrayal`, `friendship`, `identity`, `coming of age`

### `tropes`
`slow burn`, `enemies to lovers`, `rivals to lovers`, `found family`, `fake dating`, `forbidden magic`, `time loop`, `chosen one`, `villain redemption`, `academy setting`, `kingdom building`, `mutual pining`, `hurt/comfort`

### `content_warnings`
`major character death`, `graphic violence`, `abuse`, `self harm`, `none`

## Index mapping (OpenSearch)

See `backend/app/opensearch_client.py` `INDEX_MAPPING`. `text` fields are analyzed for BM25; tag fields are `keyword` so they can be used in `filter` clauses and `must_not` for hard constraints.

`combined_text` is the concatenation `title + " " + summary + " " + genres + themes + tropes + relationship_dynamics`. It is the source of truth for `more_like_this` today and will be the embedding source for the dense field tomorrow.
