"""Minimal RAG pipeline: load documents, chunk them, embed them, retrieve by
cosine similarity, and build the final prompt.

No vector database and no LangChain on purpose — this is small enough (a few
hundred chunks for the demo corpus) that a NumPy matrix in memory is simpler,
faster, and easier to explain than either.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from pypdf import PdfReader

# A heading like "## § 573 Kündigung des Vermieters ..." -> group(1) = "§ 573"
SECTION_HEADING_RE = re.compile(r"^##\s+(§\s*\d+[a-z]?)")
# The H1 title line may contain a law abbreviation in parentheses, e.g.
# "# Bürgerliches Gesetzbuch (BGB) — Mietrecht (§§ 535-580a)" -> "BGB".
LAW_ABBREVIATION_RE = re.compile(r"\(([A-Za-zÄÖÜäöüß]{2,10})\)")


@dataclass
class Chunk:
    file: str  # e.g. "bgb_mietrecht.md"
    section: str  # e.g. "§ 573 BGB", or "" if the source has no headings
    text: str  # the chunk's actual text, used for embedding and display


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Pack paragraphs into chunks of about `chunk_size` characters.

    Paragraphs (separated by a blank line) are kept whole when they fit.
    A paragraph longer than chunk_size (this happens with some long law
    paragraphs) is sliced with a sliding window so no chunk ever exceeds
    the size, and `overlap` characters are repeated across the cut so an
    answer that happens to span the cut isn't lost from both halves.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if not current:
            candidate = para
        else:
            candidate = f"{current}\n\n{para}"

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(para) <= chunk_size:
            current = para
        else:
            start = 0
            while start < len(para):
                end = start + chunk_size
                chunks.append(para[start:end])
                start = end - overlap
            current = ""

    if current:
        chunks.append(current)

    return chunks


def chunk_markdown(text: str, chunk_size: int, overlap: int) -> list[tuple[str, str]]:
    """Split a markdown law file into (section, chunk_text) pairs.

    Splits on "## § ..." headings first, so a chunk never mixes two
    sections, then chunks each section's body with `split_into_chunks`.
    """
    abbrev_match = LAW_ABBREVIATION_RE.search(text.splitlines()[0]) if text else None
    abbreviation = abbrev_match.group(1) if abbrev_match else ""

    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []  # (section_label, body_lines)
    current_label: str | None = None  # None = still before the first heading
    current_lines: list[str] = []

    for line in lines:
        heading_match = SECTION_HEADING_RE.match(line)
        if heading_match:
            if current_label is not None and current_lines:
                sections.append((current_label, current_lines))
            section_number = heading_match.group(1)
            current_label = f"{section_number} {abbreviation}".strip()
            current_lines = []
        elif line.startswith("#"):
            continue  # title, or a heading that doesn't look like "§ N"
        elif current_label is None:
            continue  # source/retrieved metadata above the first heading: not legal text
        else:
            current_lines.append(line)

    if current_label is not None and current_lines:
        sections.append((current_label, current_lines))

    result: list[tuple[str, str]] = []
    for label, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        for chunk in split_into_chunks(body, chunk_size, overlap):
            result.append((label, chunk))

    return result


def load_documents(docs_dir: Path) -> list[tuple[str, str]]:
    """Read every .md, .txt and .pdf file in docs_dir. Returns (filename, text)."""
    documents = []
    for path in sorted(docs_dir.iterdir()):
        if path.name.startswith("."):
            continue
        if path.suffix == ".pdf":
            reader = PdfReader(str(path))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        elif path.suffix in (".md", ".txt"):
            text = path.read_text(encoding="utf-8")
        else:
            continue
        documents.append((path.name, text))
    return documents


def build_chunks(docs_dir: Path, chunk_size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for filename, text in load_documents(docs_dir):
        if filename.endswith(".md"):
            for section, chunk_text in chunk_markdown(text, chunk_size, overlap):
                chunks.append(Chunk(file=filename, section=section, text=chunk_text))
        else:
            for chunk_text in split_into_chunks(text, chunk_size, overlap):
                chunks.append(Chunk(file=filename, section="", text=chunk_text))
    return chunks


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize each row so a plain dot product equals cosine similarity."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero for an all-zero embedding
    return matrix / norms


def rank_by_cosine(query_vector: np.ndarray, matrix: np.ndarray, k: int) -> list[tuple[int, float]]:
    """Return the (row_index, score) of the top-k rows most similar to query_vector.

    Both query_vector and matrix must already be L2-normalized.
    """
    scores = matrix @ query_vector
    top_indices = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in top_indices]


class RagIndex:
    """Holds the embedded chunks in memory and answers retrieval queries."""

    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, model: TextEmbedding):
        self.chunks = chunks
        self.vectors = vectors  # normalized, shape (n_chunks, embedding_dim)
        self.model = model

    @classmethod
    def build(cls, docs_dir: Path, model_name: str, chunk_size: int, overlap: int) -> "RagIndex":
        chunks = build_chunks(docs_dir, chunk_size, overlap)
        model = TextEmbedding(model_name=model_name)
        embeddings = np.array(list(model.embed([c.text for c in chunks])))
        vectors = normalize_rows(embeddings)
        return cls(chunks, vectors, model)

    def retrieve(self, question: str, k: int) -> list[tuple[Chunk, float]]:
        query_vector = normalize_rows(np.array(list(self.model.embed([question]))))[0]
        return [(self.chunks[i], score) for i, score in rank_by_cosine(query_vector, self.vectors, k)]


def build_prompt(question: str, retrieved: list[tuple[Chunk, float]]) -> str:
    """Build the prompt sent to the LLM: context chunks + instructions.

    The instructions are deliberately strict (answer only from context, cite
    the section, say "don't know" otherwise) because a RAG demo is only
    trustworthy if it doesn't quietly fall back to the model's own knowledge.
    """
    context_blocks = []
    for chunk, _score in retrieved:
        label = chunk.section or chunk.file
        context_blocks.append(f"[{label}]\n{chunk.text}")
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You answer questions about German law using ONLY the context below.

Rules:
- Answer only using information contained in the context. Do not use outside knowledge.
- Answer in the same language as the question.
- Cite the section you used, in the form "§ NNN <Law>" (e.g. "§ 573 BGB"), exactly as given in the context's [brackets].
- If the context does not contain the answer, say clearly that you don't know based on the
  provided documents. Do not guess.

Context:
{context}

Question: {question}

Answer:"""
