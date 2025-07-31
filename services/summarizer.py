from typing import List

def summarize_to_five_words(text: str) -> str:
    """Return the first five words of the given text."""
    words = text.strip().split()
    return " ".join(words[:5])

def apply_draft_summaries(observations: List[dict]) -> None:
    """Add a 'draft' key with a five-word summary for textual values."""
    for obs in observations:
        value = obs.get("value")
        if isinstance(value, str):
            obs["draft"] = summarize_to_five_words(value)

