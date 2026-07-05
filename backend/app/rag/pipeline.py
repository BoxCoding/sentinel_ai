"""RAG ingestion + retrieval pipeline.

Upload -> Document AI (parse) -> chunk -> Vertex AI Embeddings ->
Vertex AI Vector Search -> Gemini grounded answer with citations."""
import hashlib

from app.core.logging import get_logger
from app.services.document_ai_svc import docai
from app.services.gemini import gemini
from app.services.storage_svc import storage
from app.services.vector_search import vector_search

log = get_logger(__name__)

CHUNK_SIZE = 900       # chars — ~200 tokens, small enough for precise citations
CHUNK_OVERLAP = 150


def chunk_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + CHUNK_SIZE
        # break on sentence boundary where possible
        if end < len(text):
            period = text.rfind(". ", start + CHUNK_SIZE // 2, end)
            if period != -1:
                end = period + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


class RAGPipeline:
    def ingest_document(self, filename: str, content: bytes,
                        mime_type: str, source_type: str = "sop") -> dict:
        gcs_uri = storage.upload(content, f"knowledge-base/{filename}",
                                 content_type=mime_type)
        text = docai.extract_text(content, mime_type)
        chunks = chunk_text(text)
        doc_hash = hashlib.md5(content).hexdigest()[:8]
        for i, chunk in enumerate(chunks):
            vector_search.upsert(
                doc_id=f"{doc_hash}-{i}",
                text=chunk,
                metadata={"source": filename, "source_type": source_type,
                          "gcs_uri": gcs_uri, "chunk_index": i},
            )
        log.info("rag_ingested", file=filename, chunks=len(chunks))
        return {"filename": filename, "gcs_uri": gcs_uri, "chunks": len(chunks)}

    def ingest_text(self, name: str, text: str, source_type: str = "sop") -> dict:
        chunks = chunk_text(text)
        doc_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        for i, chunk in enumerate(chunks):
            vector_search.upsert(
                doc_id=f"{doc_hash}-{i}", text=chunk,
                metadata={"source": name, "source_type": source_type, "chunk_index": i},
            )
        return {"filename": name, "chunks": len(chunks)}

    async def answer(self, question: str, top_k: int = 5) -> dict:
        hits = vector_search.search(question, top_k=top_k)
        context = "\n\n".join(
            f"[{i + 1}] (source: {h['source']})\n{h['text']}" for i, h in enumerate(hits)
        )
        prompt = (
            "You are Sentinel AI's emergency-operations assistant. Answer strictly "
            "from the SOP/guideline excerpts below. Cite sources as [n]. If the "
            f"excerpts don't cover the question, say so.\n\nEXCERPTS:\n{context}\n\n"
            f"QUESTION: {question}"
        )
        answer = await gemini.generate(prompt)
        return {
            "answer": answer,
            "citations": [
                {"index": i + 1, "source": h["source"], "score": round(h["score"], 3),
                 "excerpt": h["text"][:220]}
                for i, h in enumerate(hits)
            ],
        }


rag = RAGPipeline()
