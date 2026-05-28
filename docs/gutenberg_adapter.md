# Gutenberg Adapter

StorySeek can use the real Project Gutenberg fiction dataset through a work-level adapter. The adapter keeps the current backend schema stable by converting Gutenberg books into StorySeek-compatible `work` records.

## Convert Gutenberg

```bash
python scripts/convert_gutenberg_to_storyseek.py --limit 20
python scripts/convert_gutenberg_to_storyseek.py --out data/sample/works_gutenberg.jsonl
```

The output file is ignored by Git because it can be regenerated and may become large.

## Build Index

```bash
python scripts/build_index.py --recreate --path data/sample/works_gutenberg.jsonl
```

## Convert Content Chunks

Use a bounded subset first. The chunk dataset is large, so the defaults process up to 500 books and 100 chunks per book.

```bash
python scripts/convert_gutenberg_chunks.py
python scripts/convert_gutenberg_chunks.py --book-limit 100 --max-chunks-per-book 50
```

This writes:

- `data/processed/gutenberg_chunks.jsonl`

## Build Chunk Index

```bash
python scripts/build_chunk_index.py --recreate
```

The regular book index still powers metadata/detail lookup. The chunk index powers content search.

## Generate Gutenberg Qrels

```bash
python scripts/generate_eval_qrels_gutenberg.py
```

This reads:

- `data/eval/queries_gutenberg.jsonl`
- `data/sample/works_gutenberg.jsonl`

And writes:

- `data/eval/qrels_gutenberg.csv`

## Run Gutenberg Evaluation

```bash
python scripts/run_eval.py \
  --queries data/eval/queries_gutenberg.jsonl \
  --qrels data/eval/qrels_gutenberg.csv \
  --out reports/metrics_gutenberg.json \
  --comparison-out reports/comparison_gutenberg.md
```

## Adapter Defaults

- `book_id` becomes `work_id` as `pg_{book_id}`.
- `author` becomes `creator`.
- `topics` become `genres`.
- `pg_subjects` become `themes`.
- `summary` is an excerpt from the beginning of `text`.
- `status` is always `Complete`.
- `language` is always `English`.
- `source` is always `project_gutenberg`.
- `tropes` and `relationship_dynamics` are empty lists.
- `content_warnings` is `["unknown"]` because Gutenberg does not provide warning metadata.
- `audience_rating` remains `General` to stay compatible with the current backend enum.

## Content Search

After both indexes are built and the backend is running, the React app can use the Content scope. The API endpoint is:

```bash
POST /search-content
```

It searches Gutenberg content chunks, groups results by `work_id`, and returns matched passages with each book result.
