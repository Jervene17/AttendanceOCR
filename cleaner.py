import re

# =====================================================
# Noise Filtering
# =====================================================
#
# Zoom screenshots contain UI text and room/org labels
# that get OCR'd as if they were attendee names. These
# should never be treated as recognized or unknown
# attendees.
#
# NOTE: names here are compared AFTER normalize_name()
# has already run (uppercased, punctuation stripped),
# so write them in that normalized form.

NOISE_PHRASES = {
    "LGC PHILIPPINES",
    "LGC TECH",
    "LGC TECH ONSITE",
    "IN THE MEETING",
    "PARTICIPANTS",
    "ME",
    "HOST",
    "CO HOST",
    "UNMUTE",
    "STOP VIDEO",
}

NOISE_PREFIXES = (
    "LGC TECH",
    "LGC PHILIPPINES",
)


def is_noise(name):
    """
    Returns True if the normalized text is known Zoom UI
    chrome, a room/org label, or too short to be a real
    name (e.g. an avatar initial for someone with no
    profile picture).

    IMPORTANT: only call this on text that has ALREADY
    failed to match a real member via find_member(). Some
    real display names are only 2 characters long (e.g.
    "PK", "MA"), so filtering by length before matching
    would incorrectly drop real attendees.
    """

    if not name:
        return True

    if name in NOISE_PHRASES:
        return True

    if name.startswith(NOISE_PREFIXES):
        return True

    # Likely an avatar initial (participant with no
    # profile picture) rather than an actual name
    if len(name) <= 2:
        return True

    return False

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