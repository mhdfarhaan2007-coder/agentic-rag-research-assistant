import json
import re

from llm import ask_llm


RERANKER_SYSTEM_PROMPT = """
You are an evidence reranking component in an Agentic RAG system.

Rank chunks by how strongly their actual content supports answering
the user's exact question.

Score each chunk from 0 to 10.

10 = Explicitly contains the requested answer.
8-9 = Strong, direct evidence supporting the answer.
6-7 = Useful supporting information.
4-5 = Related context but does not establish the requested fact.
2-3 = Weakly related.
0-1 = Irrelevant.

RULES:

1. Evaluate the exact question, not just its general topic.
2. A definition is not proof of who invented or introduced something.
3. A citation containing a person's name is not proof that the
   person introduced, invented, or developed a concept.
4. For historical questions, require explicit evidence of the
   requested historical relationship.
5. Never use outside knowledge.
6. Never invent facts.
7. Rank every supplied chunk.
8. Return ONLY a valid JSON array.

Required format:
[
  {"index": 0, "score": 9},
  {"index": 1, "score": 3}
]
"""


HISTORICAL_VERBS = (
    "introduced",
    "invented",
    "discovered",
    "developed",
    "created",
    "founded",
    "originated",
    "pioneered",
)


def is_historical_question(question):
    question_lower = question.lower()

    return bool(
        re.search(r"\bwho\b", question_lower)
        and re.search(
            r"\b(introduc\w*|invent\w*|discover\w*|"
            r"develop\w*|creat\w*|found\w*|"
            r"originat\w*|pioneer\w*)\b",
            question_lower,
        )
    )


def has_explicit_historical_evidence(question, text):
    """
    Conservative heuristic:
    Require a historical-action verb and the question's topic
    to appear in the same chunk.

    This is a safeguard, not a complete semantic entailment test.
    """

    question_lower = question.lower()
    text_lower = re.sub(r"\s+", " ", text.lower())

    verbs = "|".join(HISTORICAL_VERBS)

    if not re.search(
        rf"\b(?:{verbs})\b",
        text_lower,
    ):
        return False

    # Extract the target concept from questions such as:
    # "Who introduced reinforcement learning?"
    match = re.search(
        rf"\b(?:{'|'.join(HISTORICAL_VERBS)})\s+"
        r"(.+?)\??$",
        question_lower,
    )

    if not match:
        return False

    topic = match.group(1).strip(" ?.!")

    # Require the requested topic to appear in the chunk.
    # This intentionally favors precision over recall.
    return topic in text_lower


def parse_rankings(response):
    response = response.strip()

    # Handle models that wrap JSON in Markdown fences.
    response = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        response,
        flags=re.IGNORECASE,
    ).strip()

    # Handle accidental text surrounding the JSON array.
    start = response.find("[")
    end = response.rfind("]")

    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON array found.")

    return json.loads(response[start:end + 1])


def rerank_chunks(question, chunks):

    if not chunks:
        return []

    chunk_text_parts = []

    for index, chunk in enumerate(chunks):
        chunk_text_parts.append(
            f"\nCHUNK INDEX: {index}\n"
            f"Document: {chunk.get('document_name', 'Unknown')}\n"
            f"Chunk ID: {chunk.get('chunk_id', 'Unknown')}\n"
            f"Text:\n{chunk.get('text', '')}\n"
        )

    prompt = f"""
USER QUESTION:
{question}

RETRIEVED CHUNKS:
{"".join(chunk_text_parts)}

Rank every chunk by how strongly it supports answering
the exact question. Return only a JSON array.
"""

    try:
        response = ask_llm(
            RERANKER_SYSTEM_PROMPT,
            prompt,
        )

        rankings = parse_rankings(response)

    except Exception as exc:
        print(f"[RERANKER] LLM ranking failed: {exc}")

        # Preserve original retrieval order if ranking fails.
        rankings = [
            {
                "index": index,
                "score": 5.0,
            }
            for index in range(len(chunks))
        ]

    scores = {}

    for item in rankings:
        if not isinstance(item, dict):
            continue

        index = item.get("index")
        score = item.get("score")

        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 0 <= index < len(chunks)
        ):
            continue

        try:
            score = float(score)
        except (TypeError, ValueError):
            continue

        if not 0 <= score <= 10:
            score = max(0.0, min(10.0, score))

        scores[index] = score

    reranked = []

    historical_question = is_historical_question(question)

    for index, chunk in enumerate(chunks):
        chunk_copy = dict(chunk)

        llm_score = scores.get(index, 0.0)
        text = chunk.get("text", "")

        if historical_question:
            explicit_support = has_explicit_historical_evidence(
                question,
                text,
            )

            chunk_copy["explicit_historical_evidence"] = (
                explicit_support
            )

            # A historical question must not receive a high
            # relevance score from topical similarity alone.
            if not explicit_support:
                llm_score = min(llm_score, 5.0)

        chunk_copy["rerank_score"] = llm_score
        reranked.append(chunk_copy)

    reranked.sort(
        key=lambda chunk: chunk["rerank_score"],
        reverse=True,
    )

    return reranked


if __name__ == "__main__":

    question = "Who introduced reinforcement learning?"

    test_chunks = [
        {
            "document_id": "test",
            "document_name": "definition.pdf",
            "chunk_id": 1,
            "text": (
                "Reinforcement learning enables agents to learn "
                "optimal actions through rewards. "
                "Sutton and Barto (2018)."
            ),
            "score": 0.85,
        },
        {
            "document_id": "test",
            "document_name": "direct.pdf",
            "chunk_id": 2,
            "text": (
                "Sutton and Barto introduced reinforcement learning."
            ),
            "score": 0.80,
        },
        {
            "document_id": "test",
            "document_name": "unrelated.pdf",
            "chunk_id": 3,
            "text": (
                "Artificial intelligence is used in many industries."
            ),
            "score": 0.75,
        },
    ]

    results = rerank_chunks(question, test_chunks)

    print("\nReranking results:")

    for rank, chunk in enumerate(results, start=1):
        print(
            f"{rank}. {chunk['document_name']} "
            f"| Chunk {chunk['chunk_id']} "
            f"| Score: {chunk['rerank_score']} "
            f"| Explicit historical evidence: "
            f"{chunk.get('explicit_historical_evidence', 'N/A')}"
        )
