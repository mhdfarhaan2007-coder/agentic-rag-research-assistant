from router import route_question
from retriever import retrieve
from generator import (
    generate_answer,
    is_historical_question,
    has_explicit_historical_evidence,
)
from verifier import verify_answer
from llm import ask_llm
from reranker import rerank_chunks
from claim_extractor import extract_claims
from agent_controller import decide_next_action, MAX_RETRIES


# ============================================================
# DIRECT ANSWER
# ============================================================

DIRECT_SYSTEM_PROMPT = """
You are a helpful AI assistant.
Answer the user's question directly using general knowledge.
Be concise and factual.
Do not claim that information came from uploaded documents.
"""


def generate_direct_answer(question):
    return ask_llm(DIRECT_SYSTEM_PROMPT, question)


# ============================================================
# QUERY REFORMULATION
# ============================================================

def reformulate_query(question):
    system_prompt = """
You are a query reformulation component in an evidence-grounded
RAG system.

Create exactly TWO concise alternative search queries.

Rules:
1. Do not answer the question.
2. Do not invent facts.
3. Do not add unsupported names, dates, or organizations.
4. Preserve the original meaning.
5. Focus on terminology likely to appear in research documents.

Return only the two queries, one per line.
Do not number them or explain them.
"""

    response = ask_llm(system_prompt, question)
    queries = []

    for line in response.splitlines():
        line = line.strip()

        if not line:
            continue

        line = line.lstrip("-*0123456789. ").strip()

        if line.lower().startswith("<query>"):
            line = line[7:]

        if line.lower().endswith("</query>"):
            line = line[:-8]

        line = line.strip()

        if line:
            queries.append(line)

    unique_queries = []
    seen = set()

    for query in queries:
        normalized = query.lower().strip()

        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_queries.append(query)

    return unique_queries[:2]


# ============================================================
# ADAPTIVE RETRIEVAL
# ============================================================

def adaptive_retrieve(question, additional_queries, retry_count=0):
    print(f"\n    Retrieval attempt: {retry_count + 1}")

    top_k = 3 + retry_count * 2
    all_chunks = []

    # Retrieve using the original question.
    all_chunks.extend(
        retrieve(question, top_k=top_k)
    )

    # Retrieve using alternative queries.
    for query in additional_queries:
        all_chunks.extend(
            retrieve(query, top_k=top_k)
        )

    # Deduplicate chunks and retain the strongest similarity.
    unique_chunks = {}

    for chunk in all_chunks:
        key = (
            chunk["document_id"],
            chunk["chunk_id"],
        )

        if key not in unique_chunks:
            unique_chunks[key] = chunk
        elif chunk["score"] > unique_chunks[key]["score"]:
            unique_chunks[key] = chunk

    return list(unique_chunks.values())


# ============================================================
# RERANK EVIDENCE
# ============================================================

def rerank_evidence(question, chunks):
    print("\n    Evidence reranking...")

    reranked_chunks = rerank_chunks(question, chunks)

    return reranked_chunks[:5]


def print_reranked_evidence(reranked_chunks):
    print("\n    Reranked evidence:")

    for rank, chunk in enumerate(reranked_chunks, start=1):
        similarity = chunk.get("score", 0)
        rerank_score = chunk.get("rerank_score", 0)

        print(
            f"    {rank}. {chunk['document_name']} "
            f"| Chunk {chunk['chunk_id']} "
            f"| Similarity: {similarity:.4f} "
            f"| Rerank: {rerank_score:.1f}"
        )


# ============================================================
# CLAIM VERIFICATION DISPLAY
# ============================================================

def print_claim_verification(verification):
    print("\nClaim-level verification:")

    claims = verification.get("claims", [])

    if not claims:
        print("No factual claims to verify.")
        return

    for number, item in enumerate(claims, start=1):
        print(f"\n{number}. {item['verification']}")
        print(f"   {item['claim']}")
        print("   Supporting evidence:")

        evidence = item.get("supporting_evidence", [])

        if not evidence:
            print("   None")
            continue

        for source in evidence:
            print(
                f"   - {source['document_name']} "
                f"| Chunk {source['chunk_id']}"
            )


# ============================================================
# GENERATE AND VERIFY
# ============================================================

def generate_and_verify(question, reranked_chunks):
    print("[10] Generation starting...")

    answer = generate_answer(question, reranked_chunks)

    print("[11] Generation finished")

    # The generator has already rejected the answer.
    # Do not treat the rejection text as a factual claim.
    if answer.strip().upper() == "NOT ENOUGH EVIDENCE":

        gate_rejected = (
            is_historical_question(question)
            and not any(
                has_explicit_historical_evidence(
                    question,
                    chunk.get("text", ""),
                )
                for chunk in reranked_chunks
            )
        )

        stop_reason = (
            "EVIDENCE_GATE_REJECTED"
            if gate_rejected
            else None
        )

        if gate_rejected:
            print(
                "[AGENT] Historical evidence gate rejected "
                "the question."
            )

        return {
            "answer": "NOT ENOUGH EVIDENCE",
            "claims": [],
            "stop_reason": stop_reason,
            "verification": {
                "overall_verification": "UNSUPPORTED",
                "claims": [],
            },
        }

    # Extract factual claims from the generated answer.
    claims = extract_claims(answer)

    print("[12] Verification starting...")

    verification = verify_answer(
        claims,
        reranked_chunks,
    )

    print("[13] Verification finished")

    print(
        "     Overall verification:",
        verification.get(
            "overall_verification",
            "UNSUPPORTED",
        ),
    )

    return {
        "answer": answer,
        "claims": claims,
        "stop_reason": None,
        "verification": verification,
    }


# ============================================================
# MAIN AGENTIC RAG PIPELINE
# ============================================================

def run_agentic_rag(question):
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    # --------------------------------------------------------
    # 1. ROUTER
    # --------------------------------------------------------

    decision = route_question(question)

    print("\n[1] Router decision:", decision)

    # --------------------------------------------------------
    # 2. DIRECT ANSWER PATH
    # --------------------------------------------------------

    if decision == "NO_RETRIEVE":
        print("[2] Retrieval skipped")
        print("[3] Direct generation starting...")

        answer = generate_direct_answer(question)

        print("[4] Direct generation finished")

        return {
            "decision": decision,
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "answer": answer,
            "verification": None,
            "agent_decision": "DIRECT_ANSWER",
            "retry_count": 0,
        }

    # --------------------------------------------------------
    # 3. INITIAL RETRIEVAL
    # --------------------------------------------------------

    print("\n[2] Initial retrieval starting...")

    initial_chunks = retrieve(question, top_k=3)

    print(
        f"[3] Initial retrieval returned "
        f"{len(initial_chunks)} chunks"
    )

    # --------------------------------------------------------
    # 4. QUERY REFORMULATION
    # --------------------------------------------------------

    print("[4] Query reformulation starting...")

    additional_queries = reformulate_query(question)

    print("[5] Query reformulation finished")

    if additional_queries:
        print("    Additional queries:")

        for query in additional_queries:
            print(f"    - {query}")
    else:
        print("    No additional queries generated.")

    # --------------------------------------------------------
    # 5. AGENT STATE
    # --------------------------------------------------------

    retry_count = 0

    final_adaptive_chunks = []
    final_reranked_chunks = []

    final_answer = "NOT ENOUGH EVIDENCE"

    final_verification = {
        "overall_verification": "UNSUPPORTED",
        "claims": [],
    }

    final_agent_decision = "INSUFFICIENT_EVIDENCE"

    # --------------------------------------------------------
    # 6. AGENT LOOP
    # --------------------------------------------------------

    while True:

        # Retrieve evidence for this attempt.
        print(
            f"\n[6] Adaptive retrieval "
            f"(attempt {retry_count + 1})..."
        )

        adaptive_chunks = adaptive_retrieve(
            question,
            additional_queries,
            retry_count,
        )

        print("[7] Adaptive retrieval finished")

        print(
            f"    Final evidence candidates: "
            f"{len(adaptive_chunks)} chunks"
        )

        # Rerank the evidence.
        print("[8] Evidence reranking starting...")

        reranked_chunks = rerank_evidence(
            question,
            adaptive_chunks,
        )

        print("[9] Evidence reranking finished")

        print_reranked_evidence(reranked_chunks)

        # Generate and verify.
        result = generate_and_verify(
            question,
            reranked_chunks,
        )

        answer = result["answer"]
        verification = result["verification"]

        verification_status = verification.get(
            "overall_verification",
            "UNSUPPORTED",
        )

        # Pass both verification status and stop reason
        # to the controller.
        controller_result = {
            "verification": verification_status,
            "claims": verification.get("claims", []),
            "stop_reason": result.get("stop_reason"),
        }

        agent_decision = decide_next_action(
            controller_result,
            retry_count,
        )

        print("\n[14] Agent decision:", agent_decision)

        # ----------------------------------------------------
        # ACCEPT
        # ----------------------------------------------------

        if agent_decision == "ACCEPT":
            final_answer = answer
            final_verification = verification
            final_adaptive_chunks = adaptive_chunks
            final_reranked_chunks = reranked_chunks
            final_agent_decision = "ACCEPT"

            print("     Answer accepted.")
            break

        # ----------------------------------------------------
        # INSUFFICIENT EVIDENCE
        # ----------------------------------------------------

        if agent_decision == "INSUFFICIENT_EVIDENCE":
            final_answer = "NOT ENOUGH EVIDENCE"
            final_verification = verification
            final_adaptive_chunks = adaptive_chunks
            final_reranked_chunks = reranked_chunks
            final_agent_decision = "INSUFFICIENT_EVIDENCE"

            if result.get("stop_reason") == "EVIDENCE_GATE_REJECTED":
                print("     Evidence gate rejected the question.")
                print(
                    "     Stopping without further retrieval retries."
                )
            else:
                print("     Maximum retrieval attempts reached.")
                print("     Evidence is insufficient.")

            break

        # ----------------------------------------------------
        # RETRIEVE AGAIN
        # ----------------------------------------------------

        if agent_decision == "RETRIEVE_AGAIN":

            retry_count += 1

            print(
                f"     Retrieval retry "
                f"{retry_count}/{MAX_RETRIES}"
            )

            print("     Generating new retrieval queries...")

            retry_queries = reformulate_query(question)

            if retry_queries:
                print("     New queries:")

                existing_queries = {
                    query.lower().strip()
                    for query in additional_queries
                }

                for query in retry_queries:
                    print(f"       - {query}")

                    normalized_query = query.lower().strip()

                    if normalized_query not in existing_queries:
                        additional_queries.append(query)
                        existing_queries.add(normalized_query)

            # Keep the query set bounded.
            additional_queries = additional_queries[:4]

            print(
                f"     Total retrieval queries: "
                f"{len(additional_queries) + 1}"
            )

            continue

        # ----------------------------------------------------
        # REGENERATE
        # ----------------------------------------------------

        if agent_decision == "REGENERATE":

            print("     Regeneration requested.")

            # Regenerate using the same evidence.
            result = generate_and_verify(
                question,
                reranked_chunks,
            )

            answer = result["answer"]
            verification = result["verification"]

            controller_result = {
                "verification": verification.get(
                    "overall_verification",
                    "UNSUPPORTED",
                ),
                "claims": verification.get("claims", []),
                "stop_reason": result.get("stop_reason"),
            }

            agent_decision = decide_next_action(
                controller_result,
                retry_count,
            )

            print(
                "     Decision after regeneration:",
                agent_decision,
            )

            if agent_decision == "ACCEPT":
                final_answer = answer
                final_verification = verification
                final_adaptive_chunks = adaptive_chunks
                final_reranked_chunks = reranked_chunks
                final_agent_decision = "ACCEPT"
                break

            if agent_decision == "INSUFFICIENT_EVIDENCE":
                final_answer = "NOT ENOUGH EVIDENCE"
                final_verification = verification
                final_adaptive_chunks = adaptive_chunks
                final_reranked_chunks = reranked_chunks
                final_agent_decision = "INSUFFICIENT_EVIDENCE"

                if result.get("stop_reason") == "EVIDENCE_GATE_REJECTED":
                    print("     Evidence gate rejected the question.")
                    print(
                        "     Stopping without further retrieval retries."
                    )
                else:
                    print("     Evidence is insufficient.")

                break

            # If regeneration remains unsupported, use the
            # normal retrieval retry policy when available.
            if retry_count < MAX_RETRIES:
                retry_count += 1
                continue

            final_answer = "NOT ENOUGH EVIDENCE"
            final_verification = verification
            final_adaptive_chunks = adaptive_chunks
            final_reranked_chunks = reranked_chunks
            final_agent_decision = "INSUFFICIENT_EVIDENCE"
            break

        # ----------------------------------------------------
        # UNKNOWN DECISION: SAFE FALLBACK
        # ----------------------------------------------------

        print("     Unknown agent decision.")
        print("     Safely stopping.")

        final_answer = "NOT ENOUGH EVIDENCE"
        final_verification = verification
        final_adaptive_chunks = adaptive_chunks
        final_reranked_chunks = reranked_chunks
        final_agent_decision = "INSUFFICIENT_EVIDENCE"

        break

    # --------------------------------------------------------
    # 7. FINAL RESULT
    # --------------------------------------------------------

    return {
        "decision": decision,
        "retrieved_chunks": final_adaptive_chunks,
        "reranked_chunks": final_reranked_chunks,
        "answer": final_answer,
        "verification": final_verification,
        "agent_decision": final_agent_decision,
        "retry_count": retry_count,
    }


# ============================================================
# TERMINAL ENTRY POINT
# ============================================================

if __name__ == "__main__":

    question = input("\nEnter your question: ").strip()

    if not question:
        print("Question cannot be empty.")
    else:
        result = run_agentic_rag(question)

        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)

        print("\nAnswer:")
        print(result["answer"])

        print("\nAgent decision:", result["agent_decision"])
        print("Retrieval retries:", result["retry_count"])

        if result["verification"]:
            print(
                "\nVerification:",
                result["verification"].get(
                    "overall_verification",
                    "UNKNOWN",
                ),
            )

            print_claim_verification(result["verification"])