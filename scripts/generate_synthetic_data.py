"""Generate a synthetic fiction catalog for StorySeek.

Usage:
    python scripts/generate_synthetic_data.py --count 300 --seed 42
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

FORMATS = ["novel", "short_story", "fanfic_style", "manga", "webnovel"]
GENRES = [
    "fantasy", "mystery", "romance", "science fiction", "horror",
    "historical", "adventure", "drama", "comedy",
]
THEMES = [
    "dark academia", "political intrigue", "healing", "revenge", "redemption",
    "grief", "betrayal", "friendship", "identity", "coming of age",
]
TROPES = [
    "slow burn", "enemies to lovers", "rivals to lovers", "found family",
    "fake dating", "forbidden magic", "time loop", "chosen one",
    "villain redemption", "academy setting", "kingdom building",
    "mutual pining", "hurt/comfort",
]
RELATIONSHIP_DYNAMICS = [
    "rivals", "found family", "mentor and student", "childhood friends",
    "strangers to allies", "siblings", "exes", "co-conspirators",
]
CONTENT_WARNINGS = [
    "major character death", "graphic violence", "abuse", "self harm", "none",
]
AUDIENCE_RATINGS = ["General", "Teen", "Mature"]
STATUSES = ["Complete", "Ongoing", "Hiatus"]
LENGTHS = ["short", "medium", "long"]

TITLE_PATTERNS = [
    "The {noun} of {place}",
    "{adj} {noun}",
    "A {noun} for {noun2}",
    "{place}'s {noun}",
    "Beneath the {noun}",
    "The {adj} {noun}",
    "{noun} and {noun2}",
    "When the {noun} {verb}",
]
NOUNS = [
    "Clocktower", "Garden", "Heir", "Pact", "Lantern", "Crown", "Letter",
    "Apprentice", "Verdict", "Map", "Empire", "Tide", "Mirror", "Library",
    "Compass", "Cipher", "Throne", "Whisper", "Oath", "Ashes",
]
NOUNS2 = [
    "Storms", "Echoes", "Strangers", "Liars", "Saints", "Wolves", "Embers",
    "Heretics", "Dreamers", "Ghosts",
]
ADJECTIVES = [
    "Silver", "Hollow", "Golden", "Quiet", "Burning", "Last", "Forgotten",
    "Crimson", "Glass", "Borrowed",
]
PLACES = [
    "Avelin", "Karasu", "Northreach", "Velmoor", "the Capital", "Saint-Yves",
    "Bramblehold", "Hekate", "Lower Ward", "Mirefall",
]
VERBS = ["Fall", "Wake", "Sing", "Forget", "Burn", "Return"]

SUMMARY_TEMPLATES = [
    "A {format_phrase} about {protagonist_phrase} caught between {theme1} and {theme2}, where {trope1} drives the plot toward {trope2}.",
    "Set in {setting}, this {format_phrase} follows {protagonist_phrase} as they navigate {theme1}. Features {trope1} and {trope2}.",
    "When {event}, {protagonist_phrase} must reckon with {theme1}. Expect {trope1}, {trope2}, and {dynamic}.",
    "{protagonist_phrase} find themselves entangled in {theme1} and {theme2}. A story of {trope1} with strong {dynamic} energy.",
]
FORMAT_PHRASES = {
    "novel": "novel",
    "short_story": "short story",
    "fanfic_style": "fanfic-style work",
    "manga": "manga",
    "webnovel": "webnovel",
}
PROTAGONIST_PHRASES = [
    "two old rivals", "a reluctant heir", "a band of misfit scholars",
    "a disgraced knight", "a quiet archivist and a loud thief",
    "a found family of outlaws", "a pair of estranged siblings",
    "a careful spy and a careless prince",
]
SETTINGS = [
    "a crumbling magical academy", "a city of canals and conspiracies",
    "a frontier kingdom rebuilding after war", "an island where time slips",
    "a postwar coastal town", "a workshop guild on the verge of revolt",
]
EVENTS = [
    "an old letter resurfaces", "the wrong heir is crowned",
    "a forbidden door is opened", "a familiar face returns from exile",
    "a festival ends in blood",
]


def _choose_unique(rng: random.Random, pool: list[str], lo: int, hi: int) -> list[str]:
    n = rng.randint(lo, min(hi, len(pool)))
    return rng.sample(pool, n)


def _title(rng: random.Random) -> str:
    p = rng.choice(TITLE_PATTERNS)
    return p.format(
        noun=rng.choice(NOUNS),
        noun2=rng.choice(NOUNS2),
        adj=rng.choice(ADJECTIVES),
        place=rng.choice(PLACES),
        verb=rng.choice(VERBS),
    )


def _summary(rng: random.Random, fmt: str, themes: list[str], tropes: list[str], dyns: list[str]) -> str:
    tpl = rng.choice(SUMMARY_TEMPLATES)
    theme1 = themes[0] if themes else "loss"
    theme2 = themes[1] if len(themes) > 1 else "memory"
    trope1 = tropes[0] if tropes else "slow burn"
    trope2 = tropes[1] if len(tropes) > 1 else "found family"
    dynamic = dyns[0] if dyns else "found family"
    return tpl.format(
        format_phrase=FORMAT_PHRASES.get(fmt, fmt),
        protagonist_phrase=rng.choice(PROTAGONIST_PHRASES),
        setting=rng.choice(SETTINGS),
        event=rng.choice(EVENTS),
        theme1=theme1,
        theme2=theme2,
        trope1=trope1,
        trope2=trope2,
        dynamic=dynamic,
    )


def generate_work(rng: random.Random, idx: int) -> dict:
    fmt = rng.choice(FORMATS)
    genres = _choose_unique(rng, GENRES, 1, 3)
    themes = _choose_unique(rng, THEMES, 1, 3)
    tropes = _choose_unique(rng, TROPES, 1, 4)
    dyns = _choose_unique(rng, RELATIONSHIP_DYNAMICS, 1, 2)
    # ~30% have "none"; otherwise 1-2 real warnings.
    if rng.random() < 0.3:
        warnings = ["none"]
    else:
        warnings = _choose_unique(
            rng, [w for w in CONTENT_WARNINGS if w != "none"], 1, 2
        )

    return {
        "work_id": f"w_{idx:04d}",
        "title": _title(rng),
        "creator": f"Synthetic Author {rng.randint(1, 80)}",
        "format": fmt,
        "summary": _summary(rng, fmt, themes, tropes, dyns),
        "genres": genres,
        "themes": themes,
        "tropes": tropes,
        "relationship_dynamics": dyns,
        "content_warnings": warnings,
        "audience_rating": rng.choice(AUDIENCE_RATINGS),
        "status": rng.choice(STATUSES),
        "length_bucket": rng.choice(LENGTHS),
        "language": "English",
        "source": "synthetic",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fiction works JSONL.")
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "sample" / "works.jsonl",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", encoding="utf-8") as f:
        for i in range(1, args.count + 1):
            f.write(json.dumps(generate_work(rng, i), ensure_ascii=False) + "\n")

    print(f"Wrote {args.count} works to {args.out}")


if __name__ == "__main__":
    main()
