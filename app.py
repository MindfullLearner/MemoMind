
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

TOKEN_BUDGET = 4000
SUMMARIZE_AT = 3200
KEEP_RECENT_MESSAGES = 9
# Load API configuration from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL")

# Configure the Streamlit page
st.set_page_config(
    page_title="MemoMind",
    page_icon="💬",
    layout="centered",
)

st.title("💬 MemoMind")
st.caption("A conversational AI assistant powered by Google Gemini")

# Validate configuration
if not API_KEY or not MODEL_NAME:
    st.error(
        "Configuration missing. Check GEMINI_API_KEY "
        "and GEMINI_MODEL in your .env file."
    )
    st.stop()

# Create the Gemini client
client = genai.Client(api_key=API_KEY)

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
- Facts needed for future responses
- Unresolved questions or ongoing tasks

Remove repetition and unnecessary small talk.
Do not invent facts. If information conflicts, preserve the
uncertainty rather than guessing.

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
        raise ValueError("Gemini returned an empty conversation summary.")

    return summary.strip()

def build_contents(messages, summary):
    """Build Gemini history with the summary included as context."""

    contents = []

    for index, message in enumerate(messages):
        text = message["content"]

        # Add older conversation memory to the first user message.
        if index == 0 and summary and message["role"] == "user":
            text = (
                "Context summary from earlier conversation:\n"
                f"{summary}\n\n"
                "Recent conversation:\n"
                f"{text}"
            )

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

# Initialize conversation history once per session

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_summary" not in st.session_state:
    st.session_state.conversation_summary = ""

if "last_token_count" not in st.session_state:
    st.session_state.last_token_count = 0

if st.button("Reset Conversation", type="secondary"):
    st.session_state.messages = []
    st.session_state.conversation_summary = ""
    st.session_state.last_token_count = 0
    st.rerun()


# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept a new message
if prompt := st.chat_input("Type your message here..."):

    # Save and display the user's message
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    
    # Count the current conversation, including any saved summary.
    contents = build_contents(
        st.session_state.messages,
        st.session_state.conversation_summary,
    )

    token_result = client.models.count_tokens(
        model=MODEL_NAME,
        contents=contents,
    )

    current_tokens = token_result.total_tokens

    # Summarize older complete exchanges when the threshold is reached.
    if (
        current_tokens > SUMMARIZE_AT
        and len(st.session_state.messages) > KEEP_RECENT_MESSAGES
    ):
        older_messages = st.session_state.messages[
            :-KEEP_RECENT_MESSAGES
        ]

        recent_messages = st.session_state.messages[
            -KEEP_RECENT_MESSAGES:
        ]

        try:
            with st.spinner("Updating conversation memory..."):
                updated_summary = summarize_messages(
                    older_messages,
                    st.session_state.conversation_summary,
                )

            # Update memory only after summarization succeeds.
            st.session_state.conversation_summary = updated_summary
            st.session_state.messages = recent_messages

            # Rebuild and recount the reduced conversation.
            contents = build_contents(
                st.session_state.messages,
                st.session_state.conversation_summary,
            )

            token_result = client.models.count_tokens(
                model=MODEL_NAME,
                contents=contents,
            )

            current_tokens = token_result.total_tokens

            st.info("Older conversation messages summarized successfully.")

        except Exception as error:
            # Keep the original history if summarization fails.
            st.warning(
                "Could not summarize older messages. "
                "The existing conversation history has been preserved."
            )
            print(
                f"Summarization failed: "
                f"{type(error).__name__}: {error}"
            )

    st.session_state.last_token_count = current_tokens

    st.caption(
        f"Estimated conversation tokens: "
        f"{current_tokens:,} / {TOKEN_BUDGET:,}"
    )
    

    # Generate the assistant's response
    with st.chat_message("assistant"):
        try:
            with st.spinner("MemoMind is thinking..."):
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                )

            answer = response.text

            if not answer:
                answer = "The model returned an empty response."

            st.markdown(answer)

            # Store the assistant's response
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as error:
            st.error(
                "Sorry, I couldn't generate a response. "
                "Check your model configuration and API access."
            )
            # Print diagnostic details in the terminal,
            # not the API key or other secrets.
            print(f"Gemini request failed: {type(error).__name__}: {error}")

# Show conversation memory on every Streamlit rerun.
with st.expander("🧠 View Conversation Memory", expanded=False):
    if st.session_state.conversation_summary:
        st.write(st.session_state.conversation_summary)
    else:
        st.caption(
            "No summary has been generated yet. "
            "Continue chatting until summarization is triggered."
        )
