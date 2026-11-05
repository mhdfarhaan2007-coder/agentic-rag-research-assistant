from llm import ask_llm


# ============================================================
# CLAIM VERIFICATION PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an evidence verification component inside an Agentic RAG system.

Your task is to determine whether ONE factual claim is directly
supported by ONE document chunk.

Return exactly ONE label:

SUPPORTED
UNSUPPORTED

Rules:

1. SUPPORTED means the document chunk directly supports the claim.

2. UNSUPPORTED means the chunk does not directly support the claim.

3. Use ONLY the information contained in the document chunk.

4. Do NOT use outside knowledge.

5. Do NOT infer missing facts.

6. A chunk being about the same topic is NOT enough.

7. The chunk must contain actual evidence supporting the claim.

8. For historical claims such as "invented", "introduced",
   "developed", "discovered", or "founded", require explicit
   evidence for the person/event relationship.

9. If only part of a claim is supported, return UNSUPPORTED.

10. Return ONLY:
SUPPORTED
or
UNSUPPORTED

Do not explain your decision.
"""


# ============================================================
# VERIFY ONE CLAIM AGAINST ONE CHUNK
# ============================================================

def verify_claim_against_chunk(
    claim,
    chunk
):
    if not claim or not claim.strip():
        return "UNSUPPORTED"

    if not chunk or not chunk.get("text"):
        return "UNSUPPORTED"

    evidence = chunk["text"].strip()

    response = ask_llm(
        SYSTEM_PROMPT,
        f"""
CLAIM:

{claim.strip()}


DOCUMENT CHUNK:

{evidence}


Does this document chunk directly support the claim?

Return only:

SUPPORTED

or

UNSUPPORTED
"""
    )

    result = response.strip().upper()

    if "SUPPORTED" in result and "UNSUPPORTED" not in result:
        return "SUPPORTED"

    return "UNSUPPORTED"


# ============================================================
# VERIFY CLAIM AGAINST ALL RETRIEVED CHUNKS
# ============================================================

def verify_claim(
    claim,
    retrieved_chunks
):
    supporting_evidence = []

    if not claim or not claim.strip():
        return {
            "verification": "UNSUPPORTED",
            "supporting_evidence": [],
        }

    if not retrieved_chunks:
        return {
            "verification": "UNSUPPORTED",
            "supporting_evidence": [],
        }

    for chunk in retrieved_chunks:

        result = verify_claim_against_chunk(
            claim,
            chunk
        )

        if result != "SUPPORTED":
            continue

        supporting_evidence.append({

            "document_id":
                chunk.get("document_id"),

            "document_name":
                chunk.get("document_name"),

            "chunk_id":
                chunk.get("chunk_id"),

            "rerank_score":
                chunk.get("rerank_score"),

            "similarity":
                chunk.get("score"),

            "text":
                chunk.get("text"),
        })

    if supporting_evidence:

        return {
            "verification": "SUPPORTED",
            "supporting_evidence":
                supporting_evidence,
        }

    return {
        "verification": "UNSUPPORTED",
        "supporting_evidence": [],
    }


# ============================================================
# VERIFY ALL CLAIMS
# ============================================================

def verify_answer(
    claims,
    retrieved_chunks
):
    """
    Verify every extracted claim against the reranked
    evidence set.

    A claim is SUPPORTED only when at least one document
    chunk directly supports it.

    Evidence shown to the user contains ONLY chunks that
    actually supported that claim.
    """

    if not claims:
        return {
            "overall_verification": "UNSUPPORTED",
            "claims": [],
        }

    verified_claims = []

    all_supported = True

    for claim in claims:

        result = verify_claim(
            claim,
            retrieved_chunks
        )

        verification = result[
            "verification"
        ]

        if verification != "SUPPORTED":
            all_supported = False

        verified_claims.append({

            "claim":
                claim,

            "verification":
                verification,

            "supporting_evidence":
                result[
                    "supporting_evidence"
                ],
        })

    if all_supported:

        overall_verification = (
            "SUPPORTED"
        )

    else:

        overall_verification = (
            "UNSUPPORTED"
        )

    return {
        "overall_verification":
            overall_verification,

        "claims":
            verified_claims,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_chunks = [

        {
            "document_id":
                "research",

            "document_name":
                "AIResearchareasresearchgate-2025.pdf",

            "chunk_id":
                9,

            "rerank_score":
                10.0,

            "score":
                0.6472,

            "text":
                (
                    "Reinforcement learning is a research "
                    "area in artificial intelligence. "
                    "Sutton and Barto introduced "
                    "reinforcement learning."
                ),
        },

        {
            "document_id":
                "research",

            "document_name":
                "AIResearchareasresearchgate-2025.pdf",

            "chunk_id":
                62,

            "rerank_score":
                8.0,

            "score":
                0.6542,

            "text":
                (
                    "Reinforcement learning enables "
                    "agents to learn suitable actions "
                    "through rewards. Sutton and Barto "
                    "introduced reinforcement learning."
                ),
        },

        {
            "document_id":
                "test",

            "document_name":
                "test.pdf",

            "chunk_id":
                3,

            "rerank_score":
                4.0,

            "score":
                0.6523,

            "text":
                (
                    "Reinforcement learning allows "
                    "machines to learn suitable actions "
                    "through rewards."
                ),
        },

        {
            "document_id":
                "research",

            "document_name":
                "AIResearchareasresearchgate-2025.pdf",

            "chunk_id":
                20,

            "rerank_score":
                2.0,

            "score":
                0.6533,

            "text":
                (
                    "Artificial intelligence is used "
                    "across many different industries."
                ),
        },
    ]

    claim = (
        "Sutton and Barto introduced "
        "reinforcement learning."
    )

    print("=" * 60)
    print("CLAIM VERIFICATION TEST")
    print("=" * 60)

    print("\nClaim:")
    print(claim)

    result = verify_claim(
        claim,
        test_chunks
    )

    print(
        "\nOverall:",
        result["verification"]
    )

    print(
        "\nSupporting evidence:"
    )

    for evidence in result[
        "supporting_evidence"
    ]:

        print(
            f"- "
            f"{evidence['document_name']} "
            f"| Chunk {evidence['chunk_id']} "
            f"| Rerank: "
            f"{evidence['rerank_score']}"
        )