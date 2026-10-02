"""Generate five study flashcards with a Hugging Face hosted model."""

import os
import time
from typing import Any

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

MODEL_1 = "openai/gpt-oss-120b"
MODEL_2 = "google/gemma-2-2b-it"

# ==================================================
# CHANGE ONLY THIS VALUE FOR MODEL COMPARISON
# ==================================================

MODEL_ID = MODEL_1

SYSTEM_PROMPT = (
    "You create concise study flashcards for a second-year computer science "
    "student. Follow the user's formatting instructions exactly."
)
USER_PROMPT_TEMPLATE = (
    "Create exactly 5 study flashcards about: {topic}\n\n"
    "Each flashcard must have one question and one short answer. Keep answers "
    "concise, avoid unnecessary explanations, and use this clear numbered "
    "format exactly:\n"
    "Flashcard 1\n"
    "Question: ...\n"
    "Answer: ...\n"
    "Flashcard 2\n"
    "Question: ...\n"
    "Answer: ...\n"
    "Flashcard 3\n"
    "Question: ...\n"
    "Answer: ...\n"
    "Flashcard 4\n"
    "Question: ...\n"
    "Answer: ...\n"
    "Flashcard 5\n"
    "Question: ...\n"
    "Answer: ..."
)

TEMPERATURE = 0.7
MAX_TOKENS = 600


def load_configuration() -> str | None:
    """Load HF_TOKEN from the environment or the local .env file."""
    load_dotenv()
    token = os.getenv("HF_TOKEN", "").strip()
    if not token or token.lower() == "your_token_here":
        return None
    return token


def create_client(hf_token: str) -> InferenceClient:
    """Create a client that automatically selects a supported provider."""
    return InferenceClient(api_key=hf_token, provider="auto")


def _read_field(value: Any, field_name: str) -> Any:
    if isinstance(value, dict):
        return value.get(field_name)
    return getattr(value, field_name, None)


def _extract_text(content: Any) -> str:
    """Extract text from string or structured chat-completion content."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, dict):
        text = content.get("text")
        return text.strip() if isinstance(text, str) else ""
    if isinstance(content, list):
        parts = [_extract_text(part) for part in content]
        return "\n".join(part for part in parts if part)
    text = getattr(content, "text", None)
    return text.strip() if isinstance(text, str) else ""


def _extract_response_text(response: Any) -> str:
    if isinstance(response, str):
        return response.strip()

    choices = _read_field(response, "choices")
    if isinstance(choices, (list, tuple)) and choices:
        message = _read_field(choices[0], "message")
        content = _read_field(message, "content")
        text = _extract_text(content)
        if text:
            return text

    for field_name in ("generated_text", "text", "content"):
        text = _extract_text(_read_field(response, field_name))
        if text:
            return text
    return ""


def generate_flashcards(client: InferenceClient, topic: str) -> tuple[str, float]:
    """Request flashcards and return the response text and request latency."""
    start_time = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(topic=topic),
            },
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    end_time = time.perf_counter()
    latency = end_time - start_time

    flashcards = _extract_response_text(response)
    if not flashcards:
        raise ValueError("The model returned an empty or unreadable response.")
    return flashcards, latency


def _show_api_error(error: Exception) -> None:
    """Show a useful error category without printing exception details."""
    status = getattr(getattr(error, "response", None), "status_code", None)
    error_name = type(error).__name__.lower()

    if status in (401, 403) or "auth" in error_name:
        message = (
            "Authentication failed. Check that HF_TOKEN is valid and has "
            "Inference Providers permission."
        )
    elif status == 404:
        message = (
            "The selected model or provider was not found. Check the model "
            "ID and try a currently supported model."
        )
    elif status == 429:
        message = "The service is busy or rate-limited. Wait a little and try again."
    elif "timeout" in error_name or "timedout" in error_name:
        message = "The request timed out. Check your connection and try again."
    elif any(word in error_name for word in ("connection", "network", "connect")):
        message = "A network connection error occurred. Check your internet and try again."
    elif isinstance(status, int) and status >= 500:
        message = "The model provider is temporarily unavailable. Try again later."
    elif isinstance(error, ValueError):
        message = str(error)
    else:
        message = (
            "The Hugging Face request could not be completed. Check your "
            "connection, token permissions, model ID, and provider status."
        )

    print(f"\nError: {message}")


def run_model(client: InferenceClient, topic: str) -> None:
    """Generate and print one model run in a copy-friendly format."""
    try:
        flashcards, latency = generate_flashcards(client, topic)
    except Exception as error:
        _show_api_error(error)
        return

    print("\nGenerated Flashcards:")
    print(f"Model ID: {MODEL_ID}")
    print(f"Response time: {latency:.2f} seconds")
    print("Flashcards:")
    print(flashcards)


def main() -> None:
    print("=" * 40)
    print("HUGGING FACE FLASHCARD GENERATOR")
    print("=" * 40)
    if MODEL_ID == MODEL_1:
        model_label = "Model 1"
    elif MODEL_ID == MODEL_2:
        model_label = "Model 2"
    else:
        model_label = "Selected model"
    print(f"\n{model_label}: {MODEL_ID}")

    hf_token = load_configuration()
    if hf_token is None:
        print(
            "\nHF_TOKEN is missing. Add your Hugging Face access token to "
            "the .env file, then run the program again."
        )
        return

    try:
        client = create_client(hf_token)
    except Exception:
        print("\nCould not initialize the Hugging Face client. Check the installation.")
        return

    topic = input("\nEnter a topic: ").strip()
    if not topic:
        print("Please enter a non-empty topic.")
        return

    run_model(client, topic)


if __name__ == "__main__":
    main()
