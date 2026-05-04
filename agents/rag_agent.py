"""
agents/rag_agent.py — Document RAG Agent.

Queries the ChromaDB vector store with section-specific questions
to extract relevant context from uploaded documents.

This agent runs ONLY when documents have been uploaded.
If no documents exist, it's a no-op and the pipeline continues normally.

Node name in graph: "rag_node"
Writes to state: doc_context, chroma_collection_id
"""

from pipeline.state import DDState
from rag.vector_store import VectorStore

AGENT_NAME = "DocumentRAG"

# Queries to run against the uploaded documents — one per report section.
# These are designed to retrieve the most relevant chunks for each synthesis section.
SECTION_QUERIES = [
    "company description business model products services",
    "founding team founders CEO CTO leadership background",
    "funding investors venture capital raise amount",
    "revenue ARR MRR growth financials metrics",
    "technology tech stack infrastructure architecture",
    "market size TAM SAM competitors competitive landscape",
    "customers clients partnerships case studies",
    "risks challenges problems concerns",
    "roadmap product vision future plans milestones",
    "team size hiring employees headcount",
]


def run_rag_agent(state: DDState) -> dict:
    """
    Query uploaded documents and extract relevant context for synthesis.

    Args:
        state: DDState (reads: run_id, chroma_collection_id)

    Returns:
        Partial state update: {doc_context}
        Returns empty doc_context if no documents were uploaded.
    """
    run_id = state.get("run_id", "")
    chroma_collection_id = state.get("chroma_collection_id", "")

    # Skip entirely if no documents were uploaded
    if not chroma_collection_id:
        print(f"  ℹ️  [{AGENT_NAME}] No documents uploaded — skipping RAG")
        return {"doc_context": ""}

    print(f"\n  🔍 [{AGENT_NAME}] Querying uploaded documents for research context...")

    try:
        vs = VectorStore(run_id=chroma_collection_id)

        # Check if the collection actually has documents
        if not vs.is_populated:
            print(f"  ⚠️  [{AGENT_NAME}] Collection exists but is empty — skipping RAG")
            return {"doc_context": ""}

        # Query across all section dimensions and collect unique chunks
        all_results = {}  # key: chunk_id, value: result dict (deduplication)

        for query in SECTION_QUERIES:
            results = vs.query(query, n_results=3)
            for r in results:
                # Use text as dedup key (same chunk may appear for multiple queries)
                chunk_key = r["text"][:100]
                if chunk_key not in all_results:
                    all_results[chunk_key] = r

        # Sort by relevance (lower distance = more relevant) and take top 15
        unique_results = sorted(all_results.values(), key=lambda x: x["distance"])[:15]

        if not unique_results:
            print(f"  ⚠️  [{AGENT_NAME}] No relevant content found in documents")
            return {"doc_context": ""}

        # Format as a structured context block for the synthesis prompt
        context_parts = [
            "=== UPLOADED DOCUMENT CONTEXT ===",
            "The following content was extracted from documents uploaded by the user.",
            "Cross-reference this with the web research findings when writing the report.",
            "",
        ]

        for i, r in enumerate(unique_results, 1):
            context_parts.append(
                f"[Document Excerpt {i} | {r['source_file']} | {r['page_or_sheet']}]\n"
                f"{r['text']}\n"
            )

        doc_context = "\n".join(context_parts)

        print(
            f"  ✅ [{AGENT_NAME}] Retrieved {len(unique_results)} relevant chunks "
            f"from uploaded documents"
        )

        return {"doc_context": doc_context}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error querying documents: {str(e)}"
        print(f"  ❌ {error_msg}")
        return {"doc_context": ""}