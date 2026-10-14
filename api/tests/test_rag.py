import numpy as np

from app.rag import chunk_markdown, rank_by_cosine, split_into_chunks

SAMPLE_LAW_MD = """# Bürgerliches Gesetzbuch (BGB) — Mietrecht (§§ 535–580a)

**Source:** https://example.invalid/bgb

---

## § 535 Inhalt und Hauptpflichten des Mietvertrags

(1) Durch den Mietvertrag wird der Vermieter verpflichtet, dem Mieter den Gebrauch der Mietsache zu gewähren.

(2) Der Mieter ist verpflichtet, dem Vermieter die vereinbarte Miete zu entrichten.

## § 573 Kündigung des Vermieters wegen berechtigten Interesses

Der Vermieter kann kündigen, wenn er ein berechtigtes Interesse an der Beendigung des Mietverhältnisses hat.
"""


def test_split_into_chunks_keeps_short_text_whole():
    text = "Ein kurzer Satz.\n\nEin zweiter Satz."
    chunks = split_into_chunks(text, chunk_size=800, overlap=100)
    assert chunks == [text]


def test_split_into_chunks_respects_chunk_size_with_overlap():
    # One paragraph of 1000 'a's must be sliced, never exceeding chunk_size,
    # with `overlap` characters shared between consecutive chunks.
    text = "a" * 1000
    chunks = split_into_chunks(text, chunk_size=400, overlap=100)
    assert all(len(c) <= 400 for c in chunks)
    assert len(chunks) > 1
    # second chunk should start where (first chunk's length - overlap) left off
    assert chunks[1] == text[300:700]


def test_chunk_markdown_extracts_section_labels():
    chunks = chunk_markdown(SAMPLE_LAW_MD, chunk_size=800, overlap=100)
    labels = [label for label, _text in chunks]
    assert "§ 535 BGB" in labels
    assert "§ 573 BGB" in labels


def test_chunk_markdown_keeps_exact_wording():
    chunks = chunk_markdown(SAMPLE_LAW_MD, chunk_size=800, overlap=100)
    section_573_text = next(text for label, text in chunks if label == "§ 573 BGB")
    assert "berechtigtes Interesse an der Beendigung" in section_573_text


def test_rank_by_cosine_returns_most_similar_first():
    # Three unit vectors in 2D: pointing right, up, and left. A query that
    # points mostly right should rank "right" first, "up" second, "left" last.
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    query = np.array([0.9, 0.1])
    query = query / np.linalg.norm(query)

    ranked = rank_by_cosine(query, matrix, k=2)
    ranked_indices = [i for i, _score in ranked]

    assert ranked_indices == [0, 1]
    assert ranked[0][1] >= ranked[1][1]  # scores sorted descending
