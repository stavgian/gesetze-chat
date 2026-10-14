import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.llm import NoneProvider
from app.main import app, get_llm_provider, get_rag_index
from app.rag import Chunk, RagIndex


class FakeRagIndex(RagIndex):
    """A RagIndex with hand-picked vectors, so tests never load the real
    embedding model or touch the network."""

    def __init__(self):
        chunks = [
            Chunk(file="bgb_mietrecht.md", section="§ 573 BGB", text="Kuendigung wegen berechtigten Interesses."),
            Chunk(file="burlg.md", section="§ 3 BUrlG", text="Der Urlaub betraegt jaehrlich mindestens 24 Werktage."),
        ]
        vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
        super().__init__(chunks, vectors, model=None)

    def retrieve(self, question: str, k: int):
        # Ignore the question entirely and always return the first chunk as
        # the top match; good enough to exercise the /ask code path.
        return [(self.chunks[0], 0.99)][:k]


@pytest.fixture
def client():
    # Deliberately not using TestClient as a context manager: that would run
    # the app's startup lifespan, which builds the real embedding index and
    # needs the (large, network-fetched) embedding model. The dependency
    # overrides below are all these tests need.
    app.dependency_overrides[get_rag_index] = FakeRagIndex
    app.dependency_overrides[get_llm_provider] = lambda: NoneProvider()
    yield TestClient(app)
    app.dependency_overrides.clear()
