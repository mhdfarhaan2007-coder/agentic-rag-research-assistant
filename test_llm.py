from app.llm import ask_llm


response = ask_llm(
    "You are a helpful assistant.",
    "What is the capital of France?"
)

print("LLM response:")
print(response)