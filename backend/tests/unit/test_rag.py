import pytest

from app.rag.knowledge_seed import seed_knowledge_base
from app.rag.pipeline import chunk_text, rag


def test_chunking_overlap_and_coverage():
    text = ". ".join(f"Sentence number {i} about flood response" for i in range(200))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)
    # no content lost at boundaries
    assert "Sentence number 0" in chunks[0]
    assert "Sentence number 199" in chunks[-1]


@pytest.mark.asyncio
async def test_rag_retrieval_relevance():
    seed_knowledge_base()
    result = await rag.answer("When is Level 3 flood emergency activated?")
    assert result["citations"]
    sources = [c["source"] for c in result["citations"]]
    assert any("flood" in s for s in sources), f"expected flood SOP in {sources}"
