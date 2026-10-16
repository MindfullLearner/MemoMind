
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai


# --------------------------------------------------
# Configuration
# --------------------------------------------------

TOKEN_BUDGET = 4000
SUMMARIZE_AT = 100  # Temporary testing threshold; increase later.
KEEP_RECENT_EXCHANGES = 4

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL")

st.set_page_config(
    page_title="MemoMind",
    page_icon="💬",
    layout="centered",
)

st.title("💬 MemoMind")
st.caption("A conversational AI assistant powered by Google Gemini")


# --------------------------------------------------
# Validate configuration
# --------------------------------------------------

if not API_KEY or not MODEL_NAME:
    st.error(
        "Configuration missing. Check GEMINI_API_KEY "
        "and GEMINI_MODEL in your .env file."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)


# --------------------------------------------------
# Friendly API error messages
# --------------------------------------------------

def get_friendly_error(error):
    """Convert common Gemini API errors into helpful messages."""

    error_text = str(error).lower()

    if "429" in error_text or "resource_exhausted" in error_text:
        if "quota exceeded" in error_text:
            return (
                "Gemini API quota reached. Please wait until "
                "your quota resets before trying again. "
                "Your conversation is still available."
            )

        return (
            "Gemini API rate limit reached. Please wait a "
            "little before trying again."
        )

    if "503" in error_text or "unavailable" in error_text:
        return (
            "Gemini is temporarily unavailable. "
            "Please try again later."
        )

    if "timeout" in error_text:
        return "The request timed out. Please try again later."

    return (
        "Sorry, something went wrong while contacting Gemini. "
        "Check the terminal for diagnostic details."
    )


# --------------------------------------------------
# Safe token counting
# --------------------------------------------------

def count_conversation_tokens(contents):
    """Return the token count, or None if counting fails."""

    try:
        result = client.models.count_tokens(
            model=MODEL_NAME,
            contents=contents,
        )
        return result.total_tokens

    except Exception as error:
        print(
            f"Token counting failed: "
            f"{type(error).__name__}: {error}"
        )
        return None


# --------------------------------------------------
# Conversation summarization
# --------------------------------------------------

def summarize_messages(older_messages, existing_summary):
    """Compress older conversation messages into a summary."""

    transcript = "\n".join(
        f"{'User' if message['role'] == 'user' else 'Assistant'}: "
        f"{message['content']}"
        for message in older_messages
    )

    summary_prompt = f"""
You maintain memory for a conversational chatbot.

Update the existing conversation summary using the older
messages below.

Preserve important:
- User goals and preferences
- Decisions and project details
- Important facts and personal preferences shared in chat
- Unresolved questions and ongoing tasks

Remove repetition and unnecessary small talk.
Do not invent facts. If information conflicts, preserve
the uncertainty rather than guessing.

Existing summary:
{existing_summary or "No previous summary."}

Older conversation messages:
{transcript}

Return only the updated, concise summary.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=summary_prompt,
    )

    summary = response.text

    if not summary or not summary.strip():
        raise ValueError(
            "Gemini returned an empty conversation summary."
        )

    return summary.strip()


# --------------------------------------------------
# Build Gemini conversation history
# --------------------------------------------------

def build_contents(messages, summary):
    """Build Gemini history with saved memory included."""

    contents = []
    summary_added = False

    for message in messages:
        text = message["content"]

        # Attach saved memory to the first user message.
        if (
            message["role"] == "user"
            and summary
            and not summary_added
        ):
            text = (
                "Important context from earlier conversation:\n"
                f"{summary}\n\n"
                "Current user message:\n"
                f"{text}"
            )
            summary_added = True

        gemini_role = (
            "model"
            if message["role"] == "assistant"
            else "user"
        )

        contents.append(
            {
                "role": gemini_role,
                "parts": [{"text": text}],
            }
        )

    return contents


# --------------------------------------------------
# Split conversation into complete exchanges
# --------------------------------------------------

def split_conversation(messages, keep_recent_exchanges=4):
    """Separate older exchanges from recent exchanges."""

    exchanges = []
    current_exchange = []

    for message in messages:
        if message["role"] == "user":
            if current_exchange:
                exchanges.append(current_exchange)

            current_exchange = [message]

        elif message["role"] == "assistant":
            if current_exchange:
                current_exchange.append(message)
                exchanges.append(current_exchange)
                current_exchange = []

    # Keep a pending user message if its response is not ready.
    if current_exchange:
        exchanges.append(current_exchange)

    if len(exchanges) <= keep_recent_exchanges:
        return [], messages[:]

    older_exchanges = exchanges[:-keep_recent_exchanges]
    recent_exchanges = exchanges[-keep_recent_exchanges:]

    older_messages = [
        message
        for exchange in older_exchanges
        for message in exchange
    ]

    recent_messages = [
        message
        for exchange in recent_exchanges
        for message in exchange
    ]

    return older_messages, recent_messages


# --------------------------------------------------
# Initialize session state
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_summary" not in st.session_state:
    st.session_state.conversation_summary = ""

if "last_token_count" not in st.session_state:
    st.session_state.last_token_count = None


# --------------------------------------------------
# Reset conversation
# --------------------------------------------------

if st.button("Reset Conversation", type="secondary"):
    st.session_state.messages = []
    st.session_state.conversation_summary = ""
    st.session_state.last_token_count = None
    st.rerun()


# --------------------------------------------------
# Display existing conversation
# --------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# Accept a new message
# --------------------------------------------------

if prompt := st.chat_input("Type your message here..."):

    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(prompt)

    # Build context using the current history and saved summary.
    contents = build_contents(
        st.session_state.messages,
        st.session_state.conversation_summary,
    )

    current_tokens = count_conversation_tokens(contents)

    if current_tokens is None:
        st.warning(
            "Token usage could not be calculated. "
            "The conversation can continue, but automatic "
            "summarization is skipped for this turn."
        )

    # Split history into complete exchanges.
    older_messages, recent_messages = split_conversation(
        st.session_state.messages,
        KEEP_RECENT_EXCHANGES,
    )

    # Summarize only when the count is available and threshold
    # is exceeded, and older exchanges are available.
    if (
        current_tokens is not None
        and current_tokens > SUMMARIZE_AT
        and older_messages
    ):
        try:
            with st.spinner("Updating conversation memory..."):
                updated_summary = summarize_messages(
                    older_messages,
                    st.session_state.conversation_summary,
                )

            # Commit the new summary and reduced history only
            # after summarization succeeds.
            st.session_state.conversation_summary = updated_summary
            st.session_state.messages = recent_messages

            # Rebuild context after compression.
            contents = build_contents(
                st.session_state.messages,
                st.session_state.conversation_summary,
            )

            current_tokens = count_conversation_tokens(contents)

            if current_tokens is None:
                st.warning(
                    "Token usage could not be calculated "
                    "after summarization."
                )

            st.info(
                "Older conversation messages summarized successfully."
            )

        except Exception as error:
            st.warning(
                "Could not update conversation memory. "
                + get_friendly_error(error)
            )

            print(
                f"Summarization failed: "
                f"{type(error).__name__}: {error}"
            )

            # The original history remains unchanged if
            # summarization itself fails.

    st.session_state.last_token_count = current_tokens

    # This count is taken before generating the new answer.
    if current_tokens is not None:
        st.caption(
            f"Estimated input conversation tokens: "
            f"{current_tokens:,} / {TOKEN_BUDGET:,}"
        )
    else:
        st.caption("Estimated input conversation tokens: unavailable")

    # Generate the assistant response.
    with st.chat_message("assistant"):
        try:
            with st.spinner("MemoMind is thinking..."):
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                )

            answer = response.text

            if not answer or not answer.strip():
                answer = "The model returned an empty response."

            st.markdown(answer)

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as error:
            st.error(get_friendly_error(error))

            print(
                f"Gemini request failed: "
                f"{type(error).__name__}: {error}"
            )

            # Remove the unanswered user message so a failed
            # request does not leave an incomplete exchange.
            if (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "user"
                and st.session_state.messages[-1]["content"] == prompt
            ):
                st.session_state.messages.pop()


# --------------------------------------------------
# Display saved conversation memory
# --------------------------------------------------

with st.expander("🧠 View Conversation Memory", expanded=False):
    if st.session_state.conversation_summary:
        st.write(st.session_state.conversation_summary)
    else:
        st.caption(
            "No summary has been generated yet. "
            "Continue chatting until summarization is triggered."
        )
