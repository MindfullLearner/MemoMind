
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL")

if not api_key or not model_name:
    raise ValueError(
        "Check GEMINI_API_KEY and GEMINI_MODEL in .env"
    )

client = genai.Client(api_key=api_key)

sample_text = (
    "Hello! My name is Alex. "
    "I am building a memory-aware chatbot."
)

try:
    result = client.models.count_tokens(
        model=model_name,
        contents=sample_text,
    )

    print("Sample text:", sample_text)
    print("Token count:", result.total_tokens)

except Exception as error:
    print("Token counting failed.")
    print("Error type:", type(error).__name__)
    print("Error details:", error)
