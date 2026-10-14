"""Evaluate retrieval quality: for each question, check whether the section
that actually answers it shows up in the top-3 retrieved chunks.

Only needs the embedding model, not an LLM provider, so it runs with no API
key: `python eval/run_eval.py` from the api/ directory.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.rag import RagIndex  # noqa: E402

TOP_K = 3


def main():
    questions = json.loads((Path(__file__).parent / "questions.json").read_text())

    print(f"Building index from {settings.docs_dir} ...")
    index = RagIndex.build(settings.docs_dir, settings.embedding_model, settings.chunk_size, settings.chunk_overlap)
    print(f"Indexed {len(index.chunks)} chunks.\n")

    hits = 0
    rows = []
    for item in questions:
        retrieved = index.retrieve(item["question"], TOP_K)
        retrieved_sections = [chunk.section for chunk, _score in retrieved]
        hit = item["expected_section"] in retrieved_sections
        hits += hit
        rows.append((item["question"], item["expected_section"], retrieved_sections, hit))

    col_q = 60
    print(f"{'question':<{col_q}} {'expected':<14} {'retrieved (top 3)':<45} hit")
    print("-" * (col_q + 14 + 45 + 6))
    for question, expected, retrieved_sections, hit in rows:
        q_display = (question[: col_q - 1] + "…") if len(question) > col_q else question
        mark = "✓" if hit else "✗"
        print(f"{q_display:<{col_q}} {expected:<14} {', '.join(retrieved_sections):<45} {mark}")

    hit_rate = hits / len(questions)
    print(f"\nHit rate @{TOP_K}: {hits}/{len(questions)} = {hit_rate:.0%}")


if __name__ == "__main__":
    main()
