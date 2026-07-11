import re


def normalize_name(name):
    """
    Normalize OCR output into a consistent format.
    """

    if not name:
        return ""

    # Uppercase everything
    name = name.upper()

    # Common OCR mistakes
    replacements = {
        "0": "O",
        "1": "I",
        "5": "S",
        "|": "I",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    # Remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def clean_names(names):
    """
    Normalize every detected name.
    """

    return [
        normalize_name(name)
        for name in names
    ]


def remove_duplicates(names):
    """
    Remove duplicate names while preserving order.
    """

    seen = set()
    cleaned = []

    for name in names:

        if name in seen:
            continue

        seen.add(name)
        cleaned.append(name)

    return cleaned