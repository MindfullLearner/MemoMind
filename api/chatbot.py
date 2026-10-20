
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load the existing MemoMind .env file
ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL")

# Temporary in-memory conversation storage
conversation_store: dict[str, list[types.Content]] = {}


def generate_reply(conversation_id: str, message: str) -> str:
    """Generate a Gemini response using conversation history."""

    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    if not MODEL_NAME:
        raise RuntimeError("GEMINI_MODEL is not configured.")

    client = genai.Client(api_key=API_KEY)
    history = conversation_store.get(conversation_id, [])

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)],
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[*history, user_message],
    )

    reply = response.text

    if not reply:
        raise RuntimeError("Gemini returned an empty response.")

    assistant_message = types.Content(
        role="model",
        parts=[types.Part.from_text(text=reply)],
    )

    conversation_store[conversation_id] = [
        *history,
        user_message,
        assistant_message,
    ]

    return reply

def stream_reply(conversation_id: str, message: str):
    """Stream a Gemini response and save the completed exchange."""

    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    if not MODEL_NAME:
        raise RuntimeError("GEMINI_MODEL is not configured.")

    client = genai.Client(api_key=API_KEY)
    history = conversation_store.get(conversation_id, [])

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)],
    )

    chunks = []

    for chunk in client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=[*history, user_message],
    ):
        text = chunk.text
        if text:
            chunks.append(text)
            yield text

    if not chunks:
        raise RuntimeError("Gemini returned an empty response.")

    reply = "".join(chunks)

    assistant_message = types.Content(
        role="model",
        parts=[types.Part.from_text(text=reply)],
    )

    conversation_store[conversation_id] = [
        *history,
        user_message,
        assistant_message,
    ]
