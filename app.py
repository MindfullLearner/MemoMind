
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

TOKEN_BUDGET = 4000
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

    # Convert our history into Gemini's expected format
    contents = []

    for message in st.session_state.messages:
        gemini_role = (
            "model"
            if message["role"] == "assistant"
            else "user"
        )

        contents.append(
            {
                "role": gemini_role,
                "parts": [{"text": message["content"]}],
            }
        )
    token_result = client.models.count_tokens(
        model=MODEL_NAME,
        contents=contents,
    )

    current_tokens = token_result.total_tokens
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
