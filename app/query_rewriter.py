from llm import ask_llm


SYSTEM_PROMPT = """
You are a query reformulation component inside an evidence-grounded
Retrieval-Augmented Generation (RAG) system.

Your job is to rewrite a user's question into better search queries
for retrieving relevant document chunks.

IMPORTANT RULES:

1. Do NOT answer the question.
2. Do NOT invent facts.
3. Do NOT add names, dates, organizations, or historical claims
   that are not present in the user's question.
4. Preserve the original meaning.
5. Generate queries that target different aspects of the same question.
6. Focus on terminology likely to appear in research documents.
7. If the question asks "who", emphasize people, researchers,
   pioneers, introduced, developed, originated, or history ONLY when
   those concepts are already implied by the question.
8. If the question asks "when", emphasize dates, history, timeline,
   origin, or development.
9. If the question asks "what", emphasize definitions, concepts,
   methods, characteristics, or descriptions.
10. Keep each query concise.

Return EXACTLY 2 search queries.

Format:

QUERY 1
<query>

QUERY 2
<query>

Do not output anything else.
"""


def reformulate_query(question: str) -> list[str]:

    if not question or not question.strip():
        return []

    response = ask_llm(
        SYSTEM_PROMPT,
        question.strip()
    )

    queries = []

    for line in response.splitlines():

        line = line.strip()

        if not line:
            continue

        upper = line.upper()

        if upper.startswith("QUERY 1"):
            continue

        if upper.startswith("QUERY 2"):
            continue

        if line.startswith("-"):
            line = line[1:].strip()

        if line.startswith(":"):
            line = line[1:].strip()

        if line:
            queries.append(line)

    # Remove duplicates while preserving order.
    unique_queries = []

    for query in queries:

        normalized = query.lower().strip()

        if normalized and normalized not in {
            q.lower().strip()
            for q in unique_queries
        }:

            unique_queries.append(query)

    return unique_queries[:2]


if __name__ == "__main__":

    questions = [
        "Who invented machine learning?",
        "When was machine learning first developed?",
        "What is deep learning?",
        "What are the applications of AI?",
    ]

    print("=" * 60)
    print("QUERY REFORMULATOR TEST")
    print("=" * 60)

    for question in questions:

        print("\nQuestion:")
        print(question)

        print("\nReformulated queries:")

        queries = reformulate_query(question)

        if not queries:
            print("No reformulated queries.")

        else:

            for number, query in enumerate(
                queries,
                start=1
            ):

                print(
                    f"{number}. {query}"
                )