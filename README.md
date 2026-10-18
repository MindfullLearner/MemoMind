# MemoMind — Memory-Aware AI Chatbot

MemoMind is a conversational AI chatbot built with **Python, Streamlit, and Google Gemini**. It maintains conversation history across multiple turns and summarizes older messages to preserve important context while reducing the amount of conversation history sent to the model.
[MemoMind](https://memomind-skqnuaax4qwfxhrussf6v3.streamlit.app/)


## Features

- **Multi-turn conversations:** Maintains chat history during the active Streamlit session.
- **Conversation memory:** Summarizes older exchanges instead of simply discarding them.
- **Token usage visibility:** Displays estimated input conversation tokens for each turn.
- **Configurable token budget:** Uses a 4,000-token reference budget and a configurable summarization threshold.
- **Memory viewer:** Allows users to view the saved conversation summary.
- **Reset conversation:** Clears the conversation history and saved summary.
- **Error handling:** Displays helpful messages for API quota, rate-limit, timeout, and availability errors.

## Technologies Used

- Python
- Streamlit
- Google Gen AI SDK
- Google Gemini API
- python-dotenv

## Project Structure

```text
MemoMind/
├── app.py
├── MEMORY_STRATEGY.md
├── README.md
├── .env
├── .gitignore
└── requirements.txt
```

The `.env` file contains local configuration and must not be committed to GitHub.

## Prerequisites

Before running MemoMind, make sure you have:

- Python installed
- A Google Gemini API key
- Git, if you want to clone the repository

## Setup and Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd MemoMind
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Replace the example values with your own API key and a model available to your Gemini API account. **Never upload your API key to GitHub.**

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will provide a local URL, usually `http://localhost:8501`, where you can open MemoMind in your browser.

## How Conversation Memory Works

1. The application stores messages in Streamlit session state.
2. It estimates the token count of the current conversation context.
3. When the configured summarization threshold is exceeded and older exchanges are available, the application asks Gemini to summarize those exchanges.
4. The summary preserves relevant information, such as user goals, preferences, decisions, and ongoing tasks.
5. Recent exchanges remain in the active history, while the summary provides context from earlier messages.
6. Users can inspect the saved summary or reset the conversation.

See **[MEMORY_STRATEGY.md](MEMORY_STRATEGY.md)** for further details.

## Token Budget Note

The application uses a **4,000-token reference budget**. The summarization threshold is configured separately in `app.py` and may be lowered for testing.

The current implementation uses token estimates to trigger summarization; it does not guarantee a strict 4,000-token maximum for every complete API request. Token usage displayed by the app represents the estimated input conversation context before response generation, not necessarily the model's complete reported usage for the turn.

## Current Limitations

- Conversation history is stored in Streamlit session state and is not a permanent database.
- Conversation memory may be lost when the session is reset or the application session ends.
- Summarization and token counting require Gemini API access and may be affected by API quotas or rate limits.
- The application is a learning project and is not designed for production deployment.

## Learning Objectives

This project demonstrates practical use of:

- Prompt engineering
- Multi-turn conversational context
- Token-budget awareness
- Conversation summarization
- API integration and error handling
- Streamlit UI development
- Environment-variable management

## Author

Nayab Maryam
Developed as part of the **Neurofive Generative AI & Prompt Engineering Internship**.

