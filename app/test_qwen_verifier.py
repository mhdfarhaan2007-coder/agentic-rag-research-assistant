import ollama


MODEL = "qwen3:8b"


SYSTEM_PROMPT = """
You are a strict claim verification component in a
Retrieval-Augmented Generation system.

Your ONLY task is to determine whether ONE factual claim
is directly supported by the provided document evidence.

Return exactly ONE label:

SUPPORTED
UNSUPPORTED

RULES:

1. Return SUPPORTED only when the evidence explicitly states
   the claim or clearly entails it.

2. Return UNSUPPORTED when the evidence does not contain
   enough information to establish the claim.

3. Do NOT use outside knowledge.

4. Do NOT assume facts because two concepts are mentioned
   together.

5. A document mentioning a person and a topic does NOT prove
   that the person invented, created, discovered, or developed
   that topic.

6. If the claim contains multiple factual parts, every important
   part must be supported.

7. If the evidence is merely related to the claim but does not
   establish the claim, return UNSUPPORTED.

8. When uncertain, return UNSUPPORTED.

9. Do not explain your decision.

10. Output ONLY:

SUPPORTED

or

UNSUPPORTED
"""


def verify_claim(claim, evidence):

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
CLAIM:

{claim}

DOCUMENT EVIDENCE:

{evidence}
""",
            },
        ],
        think=False,
        stream=False,
        options={
            "temperature": 0,
            "num_predict": 5,
        },
    )

    result = response["message"]["content"].strip().upper()

    if result == "SUPPORTED":
        return "SUPPORTED"

    return "UNSUPPORTED"


if __name__ == "__main__":

    tests = [

        {
            "name": "Directly supported",

            "claim": (
                "Machine learning allows machines to learn "
                "and improve from experience automatically."
            ),

            "evidence": """
Machine Learning is one of the applications of AI where
machines are not explicitly programmed to perform certain
tasks; rather, they learn and improve from experience
automatically.
"""
        },

        {
            "name": "Unsupported historical claim",

            "claim": (
                "Machine learning was invented in 1950."
            ),

            "evidence": """
Machine learning is a branch of artificial intelligence
where systems can learn from data and experience.
"""
        },

        {
            "name": "Directly supported",

            "claim": (
                "Deep Learning is a subset of machine learning."
            ),

            "evidence": """
Deep Learning is a subset of machine learning based on
artificial neural networks for predictive analysis.
"""
        },

        {
            "name": "Related but unsupported",

            "claim": (
                "Machine learning was first developed "
                "for medical diagnosis."
            ),

            "evidence": """
Machine learning is one of the applications of AI where
machines learn and improve from experience automatically.
Deep Learning is a subset of machine learning.
"""
        },

        {
            "name": "Important false-positive test",

            "claim": (
                "Sutton and Barto invented reinforcement learning."
            ),

            "evidence": """
Reinforcement learning enhances decision-making in dynamic
environments like robotics and game theory by enabling
agents to learn optimal actions through reward and punishment.
Sutton and Barto are mentioned in the document.
"""
        },

        {
            "name": "Direct invention claim",

            "claim": (
                "Sutton and Barto introduced reinforcement learning."
            ),

            "evidence": """
Sutton and Barto introduced reinforcement learning as a
framework for agents learning optimal actions through
reward and punishment.
"""
        },
    ]


    print("=" * 60)
    print("QWEN 3 8B CLAIM VERIFICATION TEST")
    print("=" * 60)


    for i, test in enumerate(tests, start=1):

        print("\n" + "=" * 60)
        print(f"TEST {i}")
        print("=" * 60)

        print("\nName:")
        print(test["name"])

        print("\nClaim:")
        print(test["claim"])

        print("\nVerifying...")

        result = verify_claim(
            test["claim"],
            test["evidence"]
        )

        print("\nResult:")
        print(result)