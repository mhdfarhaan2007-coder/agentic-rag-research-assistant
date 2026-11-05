import ollama


MODEL = "qwen3:8b"


def ask_llm(
    system_prompt: str,
    user_prompt: str,
    num_predict: int = 150
) -> str:

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        think=False,
        stream=False,
        options={
            "temperature": 0,
            "num_predict": num_predict,
        },
    )

    content = response["message"]["content"]

    if not content:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    return content.strip()