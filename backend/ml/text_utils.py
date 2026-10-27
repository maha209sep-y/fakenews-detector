"""Text preprocessing (kept in its own module so the saved model can always be unpickled)."""
import re


def clean_text(text: str) -> str:
    """Light cleaning; lowercase and drop urls."""
    text = str(text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()