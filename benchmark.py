import requests
import time

MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"


tests = [
    {
        "name": "TEST 1 - Answer exists",
        "context": """
The company was founded in 2018.
It initially had 12 employees.
The company develops AI-powered medical software.
""",
        "question": "When was the company founded?",
    },
    {
        "name": "TEST 2 - Answer does NOT exist",
        "context": """
The company was founded in 2018.
It initially had 12 employees.
The company develops AI-powered medical software.
""",
        "question": "Who is the CEO of the company?",
    },
    {
        "name": "TEST 3 - Partial information",
        "context": """
The research study included 200 participants.
The participants were between 18 and 35 years old.
The study lasted for six months.
""",
        "question": "What was the gender distribution of the participants?",
    },
    {
        "name": "TEST 4 - Conflicting information",
        "context": """
Document A:
The experiment lasted for 12 weeks.

Document B:
The experiment lasted for 8 weeks.
""",
        "question": "How long did the experiment last?",
    },
]


def ask_model(prompt):
    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=300,
    )

    elapsed = time.perf_counter() - start

    if response.status_code != 200:
        print("ERROR:", response.text)
        return

    data = response.json()

    print("Response:")
    print(data["response"].strip())
    print(f"\nTime: {elapsed:.2f} seconds")


for test in tests:

    print("\n" + "=" * 70)
    print(test["name"])
    print("=" * 70)

    prompt = f"""
You are a document research assistant.

IMPORTANT RULES:
- Answer ONLY using the provided context.
- Do not use outside knowledge.
- Do not guess.
- If the answer is not supported by the context, say:
  "NOT ENOUGH EVIDENCE"
- If the documents contain conflicting information, clearly state
  that the information conflicts.

CONTEXT:
{test["context"]}

QUESTION:
{test["question"]}

Give a concise answer.
"""

    ask_model(prompt)