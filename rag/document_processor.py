"""
rag/document_processor.py — Document ingestion pipeline.

Converts uploaded files into text chunks for ChromaDB embedding.

Supported formats:
  PDF  → PyMuPDF (fitz) text extraction
  CSV  → pandas tabular summary
  XLSX → pandas sheet-by-sheet summary
  TXT  → plain text splitting

Usage:
    from rag.document_processor import process_document
    chunks = process_document("/path/to/pitch_deck.pdf")
    for chunk in chunks:
        print(chunk.text, chunk.metadata)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Chunk settings ────────────────────────────────────────────────────────────
CHUNK_SIZE       = 512    # tokens (approx — we use chars/4 as proxy)
CHUNK_OVERLAP    = 64     # tokens overlap between chunks
CHARS_PER_TOKEN  = 4      # rough approximation: 1 token ≈ 4 chars
CHUNK_SIZE_CHARS = CHUNK_SIZE   * CHARS_PER_TOKEN   # 2048 chars
OVERLAP_CHARS    = CHUNK_OVERLAP * CHARS_PER_TOKEN  # 256 chars
MIN_CHUNK_CHARS  = 100    # discard chunks shorter than this


@dataclass
class DocumentChunk:
    """A single text chunk ready for embedding."""
    text: str                         # the actual text content
    chunk_index: int                  # position in document
    source_file: str                  # original filename
    page_or_sheet: str = ""           # page number (PDF) or sheet name (XLSX)
    total_chunks: int = 0             # total chunks in this document
    metadata: dict = field(default_factory=dict)

    def to_chroma_metadata(self) -> dict:
        """Convert to a flat dict for ChromaDB metadata storage."""
        return {
            "source_file":    self.source_file,
            "chunk_index":    self.chunk_index,
            "page_or_sheet":  self.page_or_sheet,
            "total_chunks":   self.total_chunks,
            **{k: str(v) for k, v in self.metadata.items()},
        }


# ── Text cleaning ─────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Normalize whitespace and remove junk characters."""
    text = re.sub(r'\n{3,}', '\n\n', text)   # max 2 newlines
    text = re.sub(r' {2,}', ' ', text)        # max 1 space
    text = re.sub(r'[^\S\n]+', ' ', text)     # collapse horizontal whitespace
    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────

def _split_into_chunks(
    text: str,
    source_file: str,
    page_or_sheet: str = "",
) -> list[DocumentChunk]:
    """
    Split a long text string into overlapping chunks.

    Uses a sliding window approach:
    - Window size: CHUNK_SIZE_CHARS
    - Step size: CHUNK_SIZE_CHARS - OVERLAP_CHARS
    - Tries to break at sentence boundaries where possible
    """
    text = _clean_text(text)
    if len(text) < MIN_CHUNK_CHARS:
        return []

    chunks = []
    start = 0
    step = CHUNK_SIZE_CHARS - OVERLAP_CHARS

    while start < len(text):
        end = start + CHUNK_SIZE_CHARS

        # Try to break at a sentence boundary within the last 20% of the window
        if end < len(text):
            boundary_search_start = start + int(CHUNK_SIZE_CHARS * 0.8)
            # Look for sentence endings: ". ", "! ", "? ", "\n\n"
            for pattern in ['. ', '! ', '? ', '\n\n', '\n']:
                idx = text.rfind(pattern, boundary_search_start, end)
                if idx != -1:
                    end = idx + len(pattern)
                    break

        chunk_text = text[start:end].strip()

        if len(chunk_text) >= MIN_CHUNK_CHARS:
            chunks.append(DocumentChunk(
                text=chunk_text,
                chunk_index=len(chunks),
                source_file=source_file,
                page_or_sheet=page_or_sheet,
            ))

        start += step

    # Set total_chunks on all chunks
    for chunk in chunks:
        chunk.total_chunks = len(chunks)

    return chunks


# ── PDF extraction ────────────────────────────────────────────────────────────

def _process_pdf(file_path: Path) -> list[DocumentChunk]:
    """
    Extract text from PDF using PyMuPDF (fitz).

    Processes page by page, then chunks each page's text.
    If a page has <50 chars (scanned/image PDF), logs a warning.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: uv sync")

    print(f"  📄 [DocProcessor] Processing PDF: {file_path.name}")
    all_chunks = []
    doc = fitz.open(str(file_path))

    full_text_parts = []
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text()
        if len(page_text.strip()) < 50:
            print(f"  ⚠️  Page {page_num} appears to be an image/scanned page — limited text")
        full_text_parts.append(f"[Page {page_num}]\n{page_text}")

    doc.close()

    # Join all pages and chunk as one document
    # (better for cross-page context than chunking page-by-page)
    full_text = "\n\n".join(full_text_parts)
    chunks = _split_into_chunks(
        full_text,
        source_file=file_path.name,
        page_or_sheet=f"PDF ({len(full_text_parts)} pages)",
    )

    print(f"  ✅ [DocProcessor] PDF → {len(chunks)} chunks from {len(full_text_parts)} pages")
    return chunks


# ── CSV extraction ────────────────────────────────────────────────────────────

def _process_csv(file_path: Path) -> list[DocumentChunk]:
    """
    Convert CSV to a readable text summary for embedding.

    Includes: column names, data types, first 20 rows, and basic stats.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas not installed. Run: uv sync")

    print(f"  📊 [DocProcessor] Processing CSV: {file_path.name}")
    df = pd.read_csv(file_path)

    # Build a structured text representation
    lines = [
        f"File: {file_path.name}",
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        f"Columns: {', '.join(df.columns.tolist())}",
        "",
        "=== Data Types ===",
        df.dtypes.to_string(),
        "",
        "=== Basic Statistics ===",
        df.describe(include='all').to_string(),
        "",
        "=== First 20 Rows ===",
        df.head(20).to_string(index=False),
    ]

    # Add any remaining rows as a summary
    if len(df) > 20:
        lines.append(f"\n... and {len(df) - 20} more rows")

    full_text = "\n".join(lines)
    chunks = _split_into_chunks(
        full_text,
        source_file=file_path.name,
        page_or_sheet="CSV Data",
    )

    print(f"  ✅ [DocProcessor] CSV → {len(chunks)} chunks ({df.shape[0]} rows)")
    return chunks


# ── XLSX extraction ───────────────────────────────────────────────────────────

def _process_xlsx(file_path: Path) -> list[DocumentChunk]:
    """
    Convert Excel workbook to text — processes each sheet separately.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas not installed. Run: uv sync")

    print(f"  📊 [DocProcessor] Processing XLSX: {file_path.name}")
    all_chunks = []

    xl = pd.ExcelFile(file_path)
    for sheet_name in xl.sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if df.empty:
                continue

            lines = [
                f"File: {file_path.name} | Sheet: {sheet_name}",
                f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
                f"Columns: {', '.join(str(c) for c in df.columns.tolist())}",
                "",
                "=== Data ===",
                df.head(30).to_string(index=False),
            ]
            if len(df) > 30:
                lines.append(f"\n... and {len(df) - 30} more rows")

            sheet_text = "\n".join(lines)
            sheet_chunks = _split_into_chunks(
                sheet_text,
                source_file=file_path.name,
                page_or_sheet=f"Sheet: {sheet_name}",
            )
            all_chunks.extend(sheet_chunks)

        except Exception as e:
            print(f"  ⚠️  Could not process sheet '{sheet_name}': {e}")

    print(f"  ✅ [DocProcessor] XLSX → {len(all_chunks)} chunks from {len(xl.sheet_names)} sheets")
    return all_chunks


# ── TXT extraction ────────────────────────────────────────────────────────────

def _process_txt(file_path: Path) -> list[DocumentChunk]:
    """Plain text file — read and chunk directly."""
    print(f"  📄 [DocProcessor] Processing TXT: {file_path.name}")
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    chunks = _split_into_chunks(text, source_file=file_path.name, page_or_sheet="Text")
    print(f"  ✅ [DocProcessor] TXT → {len(chunks)} chunks")
    return chunks


# ── Public interface ──────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {
    ".pdf":  _process_pdf,
    ".csv":  _process_csv,
    ".xlsx": _process_xlsx,
    ".xls":  _process_xlsx,
    ".txt":  _process_txt,
}


def process_document(file_path: str | Path) -> list[DocumentChunk]:
    """
    Process any supported document into text chunks for ChromaDB.

    Args:
        file_path: Path to the document file.

    Returns:
        List of DocumentChunk objects ready for embedding.

    Raises:
        ValueError: If the file type is not supported.
        FileNotFoundError: If the file doesn't exist.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    processor_fn = SUPPORTED_EXTENSIONS[ext]
    return processor_fn(path)


def get_document_summary(chunks: list[DocumentChunk]) -> str:
    """
    Returns a short summary of a processed document for display in UI.
    """
    if not chunks:
        return "No content extracted"

    source = chunks[0].source_file
    total = chunks[0].total_chunks
    total_chars = sum(len(c.text) for c in chunks)
    return (
        f"📄 {source} — {total} chunks, "
        f"~{total_chars // 4:,} tokens extracted"
    )


if __name__ == "__main__":
    # Quick test — run: uv run python rag/document_processor.py
    import sys
    if len(sys.argv) < 2:
        print("Usage: uv run python rag/document_processor.py <file_path>")
        sys.exit(1)

    test_path = sys.argv[1]
    print(f"\nTesting document processor on: {test_path}\n")
    try:
        result_chunks = process_document(test_path)
        print(f"\n✅ Success: {len(result_chunks)} chunks produced")
        print(f"   Summary: {get_document_summary(result_chunks)}")
        print(f"\n   First chunk preview:")
        print(f"   {result_chunks[0].text[:300]}...")
    except Exception as err:
        print(f"❌ Error: {err}")