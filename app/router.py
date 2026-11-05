from llm import ask_llm


# ============================================================
# ROUTER SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the routing classifier of an evidence-grounded
Retrieval-Augmented Generation (RAG) system.

Your ONLY task is to decide whether the uploaded documents
should be searched before answering the user's question.

Return EXACTLY ONE label:

RETRIEVE
NO_RETRIEVE


============================================================
DOCUMENT DOMAIN
============================================================

The uploaded documents primarily contain information about:

- Artificial Intelligence
- Machine Learning
- Deep Learning
- Reinforcement Learning
- AI applications
- AI research areas
- AI methods and algorithms
- AI systems
- AI research findings
- AI researchers
- AI authors
- AI-related technical concepts
- Research topics discussed in the uploaded papers


============================================================
WHEN TO RETURN RETRIEVE
============================================================

Return RETRIEVE when the user's question is related to the
subject matter or domain of the uploaded documents.

This includes questions about:

- Artificial Intelligence
- Machine Learning
- Deep Learning
- Reinforcement Learning
- Natural Language Processing
- AI applications
- AI algorithms
- AI methods
- AI research
- AI researchers
- AI authors
- AI systems
- AI research findings
- technical concepts discussed in the documents
- historical information specifically related to AI/ML
- dates or events specifically related to AI/ML
- people associated with AI/ML research


Examples:

Question:
What is machine learning?

Answer:
RETRIEVE


Question:
Who invented machine learning?

Answer:
RETRIEVE


Question:
When was machine learning first developed?

Answer:
RETRIEVE


Question:
What are the different types of machine learning?

Answer:
RETRIEVE


Question:
What is deep learning?

Answer:
RETRIEVE


Question:
What is reinforcement learning?

Answer:
RETRIEVE


Question:
Who introduced reinforcement learning?

Answer:
RETRIEVE


Question:
What are the applications of AI?

Answer:
RETRIEVE


Question:
What is natural language processing?

Answer:
RETRIEVE


Question:
What researchers are mentioned in the paper?

Answer:
RETRIEVE


Question:
According to the paper, what is machine learning?

Answer:
RETRIEVE


Question:
What does the document say about deep learning?

Answer:
RETRIEVE


============================================================
EXPLICIT DOCUMENT REFERENCES
============================================================

ALWAYS return RETRIEVE if the question explicitly refers to:

- the document
- the paper
- the uploaded paper
- the uploaded documents
- the research
- the researchers
- the authors
- according to the paper
- according to the document
- mentioned in the paper
- described in the paper
- based on the document
- based on the paper


Examples:

Question:
According to the paper, what is NLP?

Answer:
RETRIEVE


Question:
Which researchers are mentioned in the document?

Answer:
RETRIEVE


Question:
What methods are described in the paper?

Answer:
RETRIEVE


============================================================
WHEN TO RETURN NO_RETRIEVE
============================================================

Return NO_RETRIEVE when the question is clearly outside the
subject/domain of the uploaded documents and does not refer
to the documents.

Examples:

Question:
What is the capital of France?

Answer:
NO_RETRIEVE


Question:
Who is the president of the United States?

Answer:
NO_RETRIEVE


Question:
What is the boiling point of water?

Answer:
NO_RETRIEVE


Question:
Explain how a car engine works.

Answer:
NO_RETRIEVE


Question:
What is photosynthesis?

Answer:
NO_RETRIEVE


Question:
What is the population of India?

Answer:
NO_RETRIEVE


These questions are general knowledge but are clearly
unrelated to the AI/ML subject matter of the documents.


============================================================
CONVERSATIONAL QUESTIONS
============================================================

Return NO_RETRIEVE for simple conversational requests.

Examples:

Question:
Hello

Answer:
NO_RETRIEVE


Question:
Hi, how are you?

Answer:
NO_RETRIEVE


Question:
Thanks

Answer:
NO_RETRIEVE


Question:
Tell me a joke.

Answer:
NO_RETRIEVE


Question:
What can you do?

Answer:
NO_RETRIEVE


Question:
Can you help me?

Answer:
NO_RETRIEVE


============================================================
IMPORTANT DISTINCTION
============================================================

Do NOT use the rule:

"Every factual question must retrieve."

Instead use this rule:

"If the question is related to the subject matter of the
uploaded documents, retrieve."

If the question is clearly unrelated to the document domain,
do not retrieve.

For example:

"What is machine learning?"
→ RETRIEVE

"What is the capital of France?"
→ NO_RETRIEVE

"Who introduced reinforcement learning?"
→ RETRIEVE

"What is photosynthesis?"
→ NO_RETRIEVE


============================================================
UNCERTAINTY RULE
============================================================

If the question is ambiguous but could reasonably be related
to Artificial Intelligence, Machine Learning, Deep Learning,
Reinforcement Learning, or the uploaded research:

RETURN RETRIEVE.


============================================================
OUTPUT FORMAT
============================================================

Return ONLY one of:

RETRIEVE

NO_RETRIEVE

Never explain the decision.
Never answer the question.
Never output anything else.
"""


# ============================================================
# ROUTE QUESTION
# ============================================================

def route_question(question: str) -> str:

    if not question or not question.strip():

        return "NO_RETRIEVE"

    decision = ask_llm(
        SYSTEM_PROMPT,
        question.strip()
    )

    decision = decision.strip().upper()

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if decision == "RETRIEVE":

        return "RETRIEVE"

    if decision == "NO_RETRIEVE":

        return "NO_RETRIEVE"

    # --------------------------------------------------------
    # Safety fallback
    #
    # If the LLM produces an unexpected response,
    # retrieving is safer than silently skipping evidence.
    # --------------------------------------------------------

    return "RETRIEVE"


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    questions = [

        # ----------------------------------------------------
        # SHOULD RETRIEVE
        # ----------------------------------------------------

        "What is machine learning?",

        "Who invented machine learning?",

        "When was machine learning first developed?",

        "What are the different types of machine learning?",

        "What is deep learning?",

        "What is reinforcement learning?",

        "Who introduced reinforcement learning?",

        "What are the applications of AI?",

        "What is natural language processing?",

        "What researchers are mentioned in the paper?",

        "According to the paper, what is machine learning?",

        "What does the document say about deep learning?",


        # ----------------------------------------------------
        # SHOULD NOT RETRIEVE
        # ----------------------------------------------------

        "What is the capital of France?",

        "Who is the president of the United States?",

        "What is the boiling point of water?",

        "What is photosynthesis?",

        "What is the population of India?",

        "Explain how a car engine works.",

        "Hello",

        "Hi, how are you?",

        "Thanks",

        "Tell me a joke.",

        "What can you do?",

        "Can you help me?",
    ]


    print("=" * 60)

    print(
        "ROUTER TEST"
    )

    print("=" * 60)


    for question in questions:

        decision = route_question(
            question
        )

        print(
            "\nQuestion:"
        )

        print(
            question
        )

        print(
            "\nDecision:"
        )

        print(
            decision
        )