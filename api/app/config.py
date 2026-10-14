"""Application settings, read once from environment variables.

Using plain env vars (not a secrets manager) is fine for a demo: the only
secret is ANTHROPIC_API_KEY, and it never leaves the process.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        # Directory of documents to index. Point this at private-docs/ to
        # run the RAG pipeline over your own files instead of the demo laws.
        self.docs_dir: Path = Path(
            os.environ.get("DOCS_DIR", str(Path(__file__).resolve().parents[2] / "docs"))
        )

        # Which LLM generates the final answer from retrieved context.
        # "none" skips generation entirely, so the app works with zero API keys.
        self.llm_provider: str = os.environ.get("LLM_PROVIDER", "none")

        self.anthropic_api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")
        self.anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

        self.ollama_model: str = os.environ.get("OLLAMA_MODEL", "llama3.1")
        self.ollama_url: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")

        # Embedding model used for both indexing and query embedding. Must be
        # multilingual: the demo corpus is German, but we also want to answer
        # English questions about it.
        self.embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

        self.chunk_size: int = 800
        self.chunk_overlap: int = 100
        self.top_k: int = 3
        self.max_question_length: int = 500


settings = Settings()
