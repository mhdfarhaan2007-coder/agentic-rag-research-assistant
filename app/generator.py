import re

from llm import ask_llm


SYSTEM_PROMPT = """
You are a strict evidence-grounded RAG answer generator.

Answer the user's question using ONLY the provided document evidence.

RULES:

1. Never use outside knowledge or guess missing information.
2. Answer the exact question asked.
3. For historical questions, require explicit evidence of the
   requested historical relationship.
4. A citation mentioning a person's name alongside a topic does
   not prove that the person introduced, invented, or developed it.
5. If the evidence does not support the answer, return exactly:
NOT ENOUGH EVIDENCE
6. If supported, provide one concise, grammatical sentence.
7. Return only the final answer.

Example:

Question:
Who introduced reinforcement learning?

Evidence:
Sutton and Barto introduced reinforcement learning.

Answer:
Sutton and Barto introduced reinforcement learning.

Question:
Who introduced reinforcement learning?

Evidence:
Reinforcement learning enables agents to learn optimal actions.
Sutton and Barto (2018) is cited in the text.

Answer:
NOT ENOUGH EVIDENCE
"""


HISTORICAL_PATTERNS = (
    "introduced",
    "invented",
    "discovered",
    "developed",
    "created",
    "founded",
    "originated",
    "pioneered",
)


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_historical_question(question):
    question_lower = question.lower()

    asks_who = bool(
        re.search(r"\bwho\b", question_lower)
    )

    asks_historical_action = bool(
        re.search(
            r"\b(introduc\w*|invent\w*|discover\w*|"
            r"develop\w*|creat\w*|found\w*|"
            r"originat\w*|pioneer\w*)\b",
            question_lower,
        )
    )

    return asks_who and asks_historical_action


def extract_historical_topic(question):
    """
    Extract the concept from questions such as:
    'Who introduced reinforcement learning?'
    """

    match = re.search(
        r"\b(?:introduced|invented|discovered|developed|"
        r"created|founded|originated|pioneered)\b\s+"
        r"(.+?)\??$",
        question.lower().strip(),
    )

    if not match:
        return None

    topic = normalize_text(match.group(1))

    return topic or None


def has_explicit_historical_evidence(question, text):
    """
    Conservative lexical gate for historical questions.

    Requires a historical-action phrase and the requested topic
    to appear in the same chunk.

    This is a heuristic, not a semantic entailment model.
    """

    topic = extract_historical_topic(question)

    if not topic:
        return False

    normalized_text = normalize_text(text)

    historical_pattern = (
        r"\b(?:introduced|invented|discovered|developed|"
        r"created|founded|originated|pioneered)\b"
    )

    if not re.search(historical_pattern, normalized_text):
        return False

    return topic in normalized_text


def generate_answer(question, retrieved_chunks):

    if not retrieved_chunks:
        print("[GENERATOR] No retrieved chunks.")
        return "NOT ENOUGH EVIDENCE"

    context_parts = []

    for chunk in retrieved_chunks:
        text = chunk.get("text", "").strip()

        if text:
            context_parts.append(text)

    if not context_parts:
        print("[GENERATOR] Retrieved chunks contain no text.")
        return "NOT ENOUGH EVIDENCE"

    # ---------------------------------------------------------
    # HISTORICAL EVIDENCE GATE
    # ---------------------------------------------------------

    if is_historical_question(question):

        has_support = any(
            has_explicit_historical_evidence(
                question,
                chunk.get("text", ""),
            )
            for chunk in retrieved_chunks
        )

        if not has_support:
            print(
                "[GENERATOR] Historical evidence gate: "
                "no explicit supporting statement found."
            )
            return "NOT ENOUGH EVIDENCE"

        print(
            "[GENERATOR] Historical evidence gate: "
            "matching statement detected."
        )

    # ---------------------------------------------------------
    # GENERATION
    # ---------------------------------------------------------

    context = "\n\n".join(context_parts)

    user_prompt = f"""
DOCUMENT EVIDENCE:

{context}

USER QUESTION:

{question}

FINAL ANSWER:
"""

    print("[GENERATOR] Generating answer...")

    answer = ask_llm(
        SYSTEM_PROMPT,
        user_prompt,
    )

    answer = answer.strip()

    print(f"[GENERATOR] Raw answer: {answer!r}")

    if not answer:
        return "NOT ENOUGH EVIDENCE"

    if " ".join(answer.split()).upper() == "NOT ENOUGH EVIDENCE":
        return "NOT ENOUGH EVIDENCE"

    return answer


if __name__ == "__main__":

    test_cases = [
        {
            "question": "Who introduced reinforcement learning?",
            "evidence": (
                "Sutton and Barto introduced reinforcement learning."
            ),
            "expected": (
                "Sutton and Barto introduced reinforcement learning."
            ),
        },
        {
            "question": "Who introduced reinforcement learning?",
            "evidence": (
                "Reinforcement learning enables agents to learn "
                "optimal actions through rewards. "
                "Sutton and Barto (2018) is cited in the text."
            ),
            "expected": "NOT ENOUGH EVIDENCE",
        },
    ]

    for index, test in enumerate(test_cases, start=1):

        print("\n" + "=" * 60)
        print(f"TEST {index}")
        print("=" * 60)

        chunks = [
            {
                "document_id": "test",
                "document_name": "test.pdf",
                "chunk_id": index,
                "text": test["evidence"],
            }
        ]

        answer = generate_answer(
            test["question"],
            chunks,
        )

        print("Question:", test["question"])
        print("Expected:", test["expected"])
        print("Actual:  ", answer)

        if answer.strip() == test["expected"]:
            print("Result: PASS")
        else:
            print("Result: FAIL")
