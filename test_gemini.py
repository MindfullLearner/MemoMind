
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")

if not api_key or not model:
    raise ValueError("Check GEMINI_API_KEY and GEMINI_MODEL in .env")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model,
        contents="Say hello in one short sentence."
    )
    print(response.text)

except Exception as error:
    print("Error type:", type(error).__name__)
    print("Error details:", str(error))
