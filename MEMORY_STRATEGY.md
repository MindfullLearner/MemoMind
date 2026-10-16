# MemoMind — Memory Strategy

## 1. Project Overview

MemoMind is a conversational AI chatbot built with Streamlit and Google's Gemini API. It maintains conversation history across multiple turns and compresses older conversation exchanges into a summary when a configured token threshold is exceeded.

The goal is to preserve useful conversational context while reducing the amount of history sent to the language model.

## 2. Conversation History

MemoMind stores conversation messages in Streamlit's `st.session_state.messages`.

Each message contains:
- `role`: identifies the message as `user` or `assistant`.
- `content`: contains the text of the message.

Session state allows conversation history to persist across Streamlit reruns during the current session.

## 3. Token Counting and Budget

The application uses Gemini's `count_tokens()` method to estimate the token count of the conversation context.

- **Target token budget:** 4,000 tokens.
- **Testing summarization threshold:** 100 tokens.
- **Token counting:** Performed before generating a response and again after successful summarization.
- **Error handling:** If token counting fails, the application displays an unavailable status and skips automatic summarization for that turn.

The 100-token threshold is used to test summarization quickly. It should be adjusted for normal use.

The 4,000-token value currently serves as a configured target and display reference. The application does not yet guarantee that every request remains below this limit.

## 4. Summarization Strategy

When the estimated conversation token count exceeds the summarization threshold, MemoMind checks whether older conversation exchanges are available.

The application then:

1. Groups user messages with their corresponding assistant responses.
2. Separates older exchanges from the four most recent exchanges.
3. Sends the older exchanges and any existing summary to Gemini.
4. Requests a concise, updated summary that preserves important information.
5. Stores the new summary in `st.session_state.conversation_summary`.
6. Retains recent exchanges and rebuilds the context sent to Gemini.

The summary prioritizes user goals, preferences, project details, important facts, decisions, and unresolved tasks. It is instructed not to invent information.

If summarization fails, the application displays a helpful error message and preserves the original history.

## 5. Memory Injection

The saved summary is included in the first user message when constructing the conversation context for Gemini.

This allows the model to use information from older exchanges even after those exchanges have been compressed and removed from the active message history.

Recent conversation messages are retained alongside the summary to preserve immediate context.

## 6. Error Handling

MemoMind handles common API errors, including:

- **429 — Resource exhausted:** informs the user that a quota or rate limit has been reached.
- **503 — Service unavailable:** indicates that Gemini may be temporarily unavailable.
- **Timeout errors:** informs the user that the request timed out.
- **Token-counting errors:** records diagnostic information in the terminal and marks the token count as unavailable.

Detailed errors are printed to the terminal for debugging. API keys are loaded from environment variables rather than hard-coded into the application.

## 7. Reset Conversation

The Reset Conversation button clears:

- Conversation messages.
- The saved conversation summary.
- The last recorded token count.

This provides a fresh conversation without carrying over memory from the previous session state.

## 8. Current Limitations and Future Improvements

Potential improvements include:

1. Enforcing the 4,000-token budget after accounting for both the summary and recent conversation.
2. Using Gemini response usage metadata to report prompt, response, and total token usage for each turn when available.
3. Adding tests for exchange splitting, summarization failures, and token-counting failures.
4. Improving recovery when response generation fails.
5. Evaluating summary quality across longer conversations to reduce the loss of important information.

## 9. Conclusion

MemoMind demonstrates session-based conversational memory, token counting, automatic summarization of older exchanges, memory injection, and basic API error handling.

Its memory strategy aims to retain useful context while reducing the amount of conversation history sent to the language model. Further testing and token-budget enforcement will improve its reliability for longer conversations.