# MemoMind — FastAPI Backend

A REST API backend for MemoMind, a memory-aware AI chatbot powered by Google's Gemini API. It provides chat endpoints, conversation IDs, structured validation errors, health checks, and Server-Sent Events (SSE) streaming.

## Features

- `GET /health` — checks whether the API is running.
- `POST /chat` — generates a chatbot response.
- `POST /chat/stream` — streams responses using Server-Sent Events (SSE).
- Pydantic models for request and response validation.
- Structured JSON errors for invalid requests and service failures.
- In-memory conversation history for multi-turn conversations.
- Automated tests using pytest and FastAPI TestClient.

## Requirements

- Python 3.11 or newer
- A Google Gemini API key
- Dependencies listed in `requirements.txt`

## Setup

Run these commands in PowerShell from the `api` directory:

```powershell
cd E:\MemoMind\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Environment Configuration

The backend loads its configuration from the `.env` file in the MemoMind project root.

Add these entries to `E:\MemoMind\.env` if they are not already present:

```text
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_gemini_model
```

Replace the placeholder values with your own configuration. Never commit your actual API key to GitHub.

## Run the API

From `E:\MemoMind\api`, activate the virtual environment and run:

```powershell
python -m uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API Endpoints

### 1. Health Check

**Request**

```http
GET /health
```

**Example response**

```json
{
  "status": "healthy"
}
```

### 2. Chat

**Request**

```http
POST /chat
Content-Type: application/json
```

**Example body**

```json
{
  "message": "Explain prompt engineering in simple words."
}
```

A conversation ID can optionally be supplied to continue an existing conversation:

```json
{
  "message": "Give me an example.",
  "conversation_id": "your-existing-conversation-id"
}
```

The response includes a conversation ID and the generated answer.

### 3. Streaming Chat

**Request**

```http
POST /chat/stream
Content-Type: application/json
```

**Example body**

```json
{
  "message": "Explain prompt engineering in three sentences."
}
```

The response uses `text/event-stream`. Events include:

- `conversation` — provides the conversation ID.
- `data` — carries a response text chunk.
- `done` — indicates successful completion.
- `error` — indicates a streaming failure.

## Error Handling

The API validates request data and returns structured errors.

Common status codes:

| Status | Meaning |
|---|---|
| `200` | Request succeeded |
| `422` | Request validation failed |
| `503` | Chatbot service is unavailable or misconfigured |
| `502` | The chatbot service failed to generate a response |

Streaming errors are sent as SSE error events because the HTTP response may already have started.

## Run Automated Tests

Activate the API virtual environment, then run:

```powershell
python -m pytest -v
```

The tests mock chatbot functions so that endpoint tests do not require real Gemini API calls.

## Limitations

- Conversation history is stored in server memory and is cleared when the server restarts.
- The current in-memory store is intended for demonstration and development, not multi-worker production deployment.
- Conversation expiration, persistent storage, authentication, and per-user access controls are not implemented.

## Project Structure

```text
api/
├── main.py
├── models.py
├── chatbot.py
├── requirements.txt
├── README.md
└── tests/
    └── test_api.py
```
