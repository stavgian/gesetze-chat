"""FastAPI app: builds the RAG index once at startup, then answers questions."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.llm import NoneProvider, create_provider
from app.rag import RagIndex, build_prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag_index = RagIndex.build(
        settings.docs_dir, settings.embedding_model, settings.chunk_size, settings.chunk_overlap
    )
    app.state.llm_provider = create_provider(settings)
    yield


app = FastAPI(title="gesetze-chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_rag_index() -> RagIndex:
    return app.state.rag_index


def get_llm_provider():
    return app.state.llm_provider


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=settings.max_question_length)


class Source(BaseModel):
    file: str
    section: str
    chunk: str
    score: float


class AskResponse(BaseModel):
    answer: str | None
    sources: list[Source]
    mode: str  # "full" or "retrieval_only"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    rag_index: RagIndex = Depends(get_rag_index),
    llm_provider=Depends(get_llm_provider),
):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    retrieved = rag_index.retrieve(question, settings.top_k)
    sources = [
        Source(file=chunk.file, section=chunk.section, chunk=chunk.text, score=score) for chunk, score in retrieved
    ]

    if isinstance(llm_provider, NoneProvider):
        return AskResponse(answer=None, sources=sources, mode="retrieval_only")

    prompt = build_prompt(question, retrieved)
    answer = llm_provider.generate(prompt)
    return AskResponse(answer=answer, sources=sources, mode="full")
