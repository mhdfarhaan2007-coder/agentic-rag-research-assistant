from claim_verifier import verify_claim_against_chunk


chunk = {
    "document_id": "test",
    "document_name": "test.pdf",
    "chunk_id": 3,
    "text": """
    Machine Learning is one of the applications of AI where
    machines are not explicitly programmed to perform certain
    tasks; rather, they learn and improve from experience
    automatically.

    Deep Learning is a subset of machine learning based on
    artificial neural networks for predictive analysis.
    """
}


tests = [
    "Machine learning allows machines to learn and improve from experience automatically.",
    "Deep Learning is a subset of machine learning.",
    "Machine learning was invented in 1950.",
]


for claim in tests:

    print("=" * 60)
    print("CLAIM:")
    print(claim)

    result = verify_claim_against_chunk(
        claim,
        chunk
    )

    print("\nRESULT:")
    print(result)