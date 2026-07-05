"""Generate sample SOP PDFs for the RAG demo (pure-Python minimal PDF writer,
no dependencies). Content mirrors backend/app/rag/knowledge_seed.py so demo
retrieval matches whether you ingest the PDFs or use the seed."""
import sys
import textwrap
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "samples" / "pdfs"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.rag.knowledge_seed import SEED_DOCUMENTS  # noqa: E402


def write_pdf(path: Path, title: str, body: str) -> None:
    lines = [title, ""] + textwrap.wrap(body, width=90)
    content_parts = ["BT /F1 11 Tf 50 780 Td 14 TL"]
    for line in lines:
        safe = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        content_parts.append(f"({safe}) Tj T*")
    content_parts.append("ET")
    stream = "\n".join(content_parts).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF").encode()
    path.write_bytes(bytes(out))


def main():
    for name, text in SEED_DOCUMENTS.items():
        pdf_name = name.replace(".md", ".pdf")
        title = pdf_name.replace("_", " ").replace(".pdf", "").upper()
        write_pdf(OUT / pdf_name, title, " ".join(text.split()))
        print(f"wrote {OUT / pdf_name}")


if __name__ == "__main__":
    main()
