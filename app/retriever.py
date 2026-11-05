import math

from embeddings import create_embedding
from vector_store import load_embeddings


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(vector_a, vector_b):

    dot_product = 0.0
    magnitude_a = 0.0
    magnitude_b = 0.0

    for a, b in zip(vector_a, vector_b):

        dot_product += a * b
        magnitude_a += a * a
        magnitude_b += b * b

    magnitude_a = math.sqrt(
        magnitude_a
    )

    magnitude_b = math.sqrt(
        magnitude_b
    )

    if magnitude_a == 0 or magnitude_b == 0:

        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# ============================================================
# SINGLE QUERY RETRIEVAL
# ============================================================

def retrieve(
    question,
    top_k=3
):

    embedded_chunks = load_embeddings()

    if not embedded_chunks:

        return []

    question_vector = create_embedding(
        question
    )

    results = []

    for chunk in embedded_chunks:

        chunk_embedding = chunk.get(
            "embedding"
        )

        if not chunk_embedding:

            continue

        score = cosine_similarity(
            question_vector,
            chunk_embedding
        )

        results.append({

            "document_id":
                chunk["document_id"],

            "document_name":
                chunk["document_name"],

            "chunk_id":
                chunk["chunk_id"],

            "text":
                chunk["text"],

            "score":
                score,

        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# MULTI-QUERY RETRIEVAL
# ============================================================

def retrieve_multiple(
    queries,
    top_k_per_query=8,
    final_top_k=12
):

    """
    Retrieve a larger candidate pool using multiple queries.

    Each query retrieves up to top_k_per_query chunks.

    Duplicate chunks are removed.

    The strongest similarity score for each chunk
    is preserved.
    """

    if not queries:

        return []

    merged_chunks = {}

    for query in queries:

        if not query or not query.strip():

            continue

        results = retrieve(
            query.strip(),
            top_k=top_k_per_query
        )

        for result in results:

            key = (
                result["document_id"],
                result["chunk_id"]
            )

            if key not in merged_chunks:

                merged_chunks[key] = result

            else:

                existing = merged_chunks[key]

                if (
                    result["score"]
                    > existing["score"]
                ):

                    merged_chunks[key] = result

    results = list(
        merged_chunks.values()
    )

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:final_top_k]


# ============================================================
# ADAPTIVE RETRIEVAL
# ============================================================

def retrieve_adaptive(
    question,
    reformulated_queries=None,
    top_k=12
):

    """
    Retrieve a broad candidate evidence set.

    The original question is always included.

    Reformulated queries are added when available.

    The result is intentionally larger than the final
    generator context. The reranker will later select
    the strongest evidence.
    """

    queries = [
        question
    ]

    if reformulated_queries:

        for query in reformulated_queries:

            if not query:

                continue

            query = query.strip()

            if not query:

                continue

            normalized_query = (
                query.lower()
            )

            existing_queries = {
                q.lower().strip()
                for q in queries
            }

            if (
                normalized_query
                not in existing_queries
            ):

                queries.append(
                    query
                )

    print(
        "\n    Retrieval queries:"
    )

    for number, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"    {number}. {query}"
        )

    results = retrieve_multiple(
        queries,
        top_k_per_query=8,
        final_top_k=top_k
    )

    return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    question = (
        "Who introduced reinforcement learning?"
    )

    reformulated_queries = [

        "Who developed reinforcement learning?",

        "Origins of reinforcement learning methodology",

    ]

    print(
        "=" * 60
    )

    print(
        "MULTI-QUERY RETRIEVAL TEST"
    )

    print(
        "=" * 60
    )

    print(
        "\nOriginal question:"
    )

    print(
        question
    )

    print(
        "\nReformulated queries:"
    )

    for query in reformulated_queries:

        print(
            f"- {query}"
        )

    results = retrieve_adaptive(
        question,
        reformulated_queries,
        top_k=12
    )

    print(
        f"\nFinal candidate count: "
        f"{len(results)}"
    )

    for number, result in enumerate(
        results,
        start=1
    ):

        print(
            "\n" + "-" * 60
        )

        print(
            f"Candidate {number}"
        )

        print(
            "Document:",
            result["document_name"]
        )

        print(
            "Chunk:",
            result["chunk_id"]
        )

        print(
            "Similarity:",
            round(
                result["score"],
                4
            )
        )

        print(
            "Text:"
        )

        print(
            result["text"][:400],
            "..."
        )