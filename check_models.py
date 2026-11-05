import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={
        "Authorization": f"Bearer {api_key}"
    },
    timeout=30,
)

response.raise_for_status()

models = response.json()["data"]

print("=" * 70)
print("AVAILABLE FREE MODELS")
print("=" * 70)

for model in models:
    pricing = model.get("pricing", {})

    prompt_price = pricing.get("prompt")
    completion_price = pricing.get("completion")

    if prompt_price == "0" and completion_price == "0":
        print(model["id"])