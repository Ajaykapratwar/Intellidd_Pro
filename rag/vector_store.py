"""
rag/vector_store.py — ChromaDB vector store operations.

Uses ChromaDB's DefaultEmbeddingFunction (onnxruntime-based).
No torch, no torchvision, no GPU needed.
Same all-MiniLM-L6-v2 model, CPU-only, ~22MB download on first run.

Usage:
    from rag.vector_store import VectorStore
    vs = VectorStore(run_id="abc123")
    vs.add_chunks(chunks)
    results = vs.query("What is the company's revenue model?", n_results=5)
"""

from pathlib import Path
from typing import Optional

import config
from rag.document_processor import DocumentChunk


class VectorStore:
    """
    Per-run ChromaDB collection with onnxruntime-based embeddings.

    Each run gets its own isolated collection named:
        "intellidd_{run_id}"
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.collection_name = f"intellidd_{run_id}"
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._initialized = False

    def _initialize(self) -> None:
        """Lazy initialization — only loads ChromaDB + model when first needed."""
        if self._initialized:
            return

        print(f"  🗄️  [VectorStore] Initializing ChromaDB collection: {self.collection_name}")

        try:
            import chromadb
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        except ImportError:
            raise ImportError("ChromaDB not installed. Run: uv sync")

        # Persistent client — data survives restarts
        self._client = chromadb.PersistentClient(path=config.CHROMA_PATH)

        # DefaultEmbeddingFunction uses onnxruntime — no torch, no torchvision
        # Downloads all-MiniLM-L6-v2 (~22MB) on first call, then caches it
        print(f"  🧠 [VectorStore] Loading embedding model (onnxruntime)...")
        self._embedding_fn = DefaultEmbeddingFunction()

        # Get or create isolated collection for this run
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_fn,
            metadata={"run_id": self.run_id, "hnsw:space": "cosine"},
        )

        self._initialized = True
        print(f"  ✅ [VectorStore] Ready. Collection: {self.collection_name}")

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """
        Embed and store document chunks in ChromaDB.

        Args:
            chunks: List of DocumentChunk objects from document_processor.py

        Returns:
            Number of chunks successfully stored.
        """
        self._initialize()

        if not chunks:
            print("  ⚠️  [VectorStore] No chunks to add")
            return 0

        print(f"  📥 [VectorStore] Embedding {len(chunks)} chunks...")

        ids        = []
        documents  = []
        metadatas  = []

        for chunk in chunks:
            chunk_id = f"{self.run_id}_{chunk.source_file}_{chunk.chunk_index}"
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append(chunk.to_chroma_metadata())

        # Add in batches of 100 to avoid memory issues with large documents
        batch_size  = 100
        total_added = 0

        for i in range(0, len(ids), batch_size):
            batch_ids  = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]

            self._collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
            )
            total_added += len(batch_ids)
            print(
                f"  📦 [VectorStore] Batch {i // batch_size + 1}: "
                f"{total_added}/{len(ids)} chunks stored"
            )

        print(f"  ✅ [VectorStore] All {total_added} chunks embedded and stored")
        return total_added

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        Retrieve the most semantically similar chunks for a query.

        Args:
            query_text: Natural language query string
            n_results:  Number of chunks to return (default 5)
            where:      Optional ChromaDB metadata filter

        Returns:
            List of dicts: text, source_file, page_or_sheet, chunk_index, distance
        """
        self._initialize()

        try:
            count = self._collection.count()
            if count == 0:
                return []

            results = self._collection.query(
                query_texts=[query_text],
                n_results=min(n_results, count),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            output = []
            if results and results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    output.append({
                        "text":          doc,
                        "source_file":   meta.get("source_file", "unknown"),
                        "page_or_sheet": meta.get("page_or_sheet", ""),
                        "chunk_index":   meta.get("chunk_index", 0),
                        "distance":      round(float(dist), 4),
                    })

            return output

        except Exception as e:
            print(f"  ⚠️  [VectorStore] Query failed: {e}")
            return []

    def query_to_context(self, query_text: str, n_results: int = 5) -> str:
        """
        Query and return results as a formatted string for LLM prompts.

        Usage:
            doc_context = vs.query_to_context("revenue model and pricing")
        """
        results = self.query(query_text, n_results=n_results)

        if not results:
            return "No relevant document content found for this query."

        parts = []
        for i, r in enumerate(results, 1):
            parts.append(
                f"[Doc Chunk {i} | {r['source_file']} | {r['page_or_sheet']}]\n"
                f"{r['text']}"
            )

        return "\n\n".join(parts)

    def count(self) -> int:
        """Return total number of chunks stored in this collection."""
        self._initialize()
        return self._collection.count()

    def delete_collection(self) -> None:
        """Delete this run's collection from ChromaDB."""
        self._initialize()
        self._client.delete_collection(self.collection_name)
        print(f"  🗑️  [VectorStore] Deleted collection: {self.collection_name}")

    @property
    def is_populated(self) -> bool:
        """Returns True if the collection has at least one chunk."""
        try:
            self._initialize()
            return self._collection.count() > 0
        except Exception:
            return False


if __name__ == "__main__":
    # Quick test — run: uv run python rag/vector_store.py
    from rag.document_processor import DocumentChunk

    print("Testing VectorStore with dummy chunks...\n")

    test_chunks = [
        DocumentChunk(
            text="Stripe is a payments company that processes billions of dollars annually.",
            chunk_index=0,
            source_file="test_pitch.pdf",
            page_or_sheet="Page 1",
            total_chunks=3,
        ),
        DocumentChunk(
            text="The company's revenue grew 50% year over year reaching $1B ARR.",
            chunk_index=1,
            source_file="test_pitch.pdf",
            page_or_sheet="Page 2",
            total_chunks=3,
        ),
        DocumentChunk(
            text="Founders Patrick and John Collison started Stripe in 2010.",
            chunk_index=2,
            source_file="test_pitch.pdf",
            page_or_sheet="Page 3",
            total_chunks=3,
        ),
    ]

    vs = VectorStore(run_id="test001")
    vs.add_chunks(test_chunks)

    print(f"\nCollection size: {vs.count()} chunks")
    print("\nQuerying: 'What is the revenue?'")
    results = vs.query("What is the revenue?", n_results=2)
    for r in results:
        print(f"  [{r['distance']:.3f}] {r['text'][:80]}...")

    vs.delete_collection()
    print("\n✅ VectorStore test complete")