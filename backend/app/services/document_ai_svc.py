"""Document AI — parses SOP PDFs/DOCs for the RAG ingestion pipeline.
Demo mode falls back to naive text decode (works for the sample text-PDFs)."""
from app.core.config import settings


class DocumentAIService:
    def extract_text(self, content: bytes, mime_type: str = "application/pdf") -> str:
        if settings.DEMO_MODE or not settings.DOCAI_PROCESSOR_ID:
            # crude but sufficient for demo: extract printable ASCII runs
            text = content.decode("latin-1", errors="ignore")
            runs = [r for r in text.split() if r.isprintable()]
            return " ".join(runs)
        from google.cloud import documentai

        client = documentai.DocumentProcessorServiceClient()
        name = client.processor_path(
            settings.GCP_PROJECT_ID, settings.GCP_REGION, settings.DOCAI_PROCESSOR_ID
        )
        result = client.process_document(request=documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(content=content, mime_type=mime_type),
        ))
        return result.document.text


docai = DocumentAIService()
