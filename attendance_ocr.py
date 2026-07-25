import easyocr

from cleaner import (
    normalize_name,
    clean_names,
    remove_duplicates,
    is_noise,
)
from members import find_member
print("Loading EasyOCR...")

reader = easyocr.Reader(["en", "ko"])

print("EasyOCR Ready!")

def read_image(image_path):
    results = reader.readtext(image_path)
    return results

def extract_text(image_path):
    results = read_image(image_path)
    return [text for _, text, _ in results]

def extract_clean_text(image_path):
    raw = extract_text(image_path)
    cleaned = clean_names(raw)
    cleaned = remove_duplicates(cleaned)
    return cleaned

def recognize_members(image_path):
    """
    Reads an image and returns:
        - recognized members
        - unknown names
        - duplicate names
    """
    cleaned_names = extract_clean_text(image_path)

    recognized = []
    unknown = []
    duplicates = []
    seen = set()

    for text in cleaned_names:

        member = find_member(text)

        if member:
            member_name = member["display_name"]

            if member_name not in seen:
                recognized.append(member)
                seen.add(member_name)
            else:
                duplicates.append(member_name)

            continue

        if is_noise(text):
            continue

        unknown.append(text)

    return {
        "recognized": recognized,
        "unknown": unknown,
        "duplicates": duplicates,
    }

def get_attendee_names(result, sort=True):
    """
    Returns the recognized attendee names.
    """
    names = [member["display_name"] for member in result["recognized"]]

    if sort:
        names.sort()

    return names

def recognize_multiple_images(image_paths):
    recognized = []
    unknown = []
    duplicates = []
    seen = set()

    for i, image_path in enumerate(image_paths, 1):

        print(f"[{i}/{len(image_paths)}] OCR processing {image_path}...")

        result = process_image(image_path)

        print(f"[{i}/{len(image_paths)}] done: {len(result['recognized'])} recognized, {len(result['unknown'])} unknown")

        for member in result["recognized"]:
            if member["display_name"] not in seen:
                recognized.append(member)
                seen.add(member["display_name"])
            else:
                duplicates.append(member["display_name"])

        unknown.extend(result["unknown"])

    return {
        "recognized": recognized,
        "unknown": sorted(set(unknown)),
        "duplicates": sorted(set(duplicates)),
    }

def attendance_summary(result):
    """
    Creates a readable attendance summary.
    """
    names = get_attendee_names(result)

    lines = []
    lines.append(f"Recognized: {len(names)}")

    if names:
        lines.append("")
        lines.extend(names)

    if result["unknown"]:
        lines.append("")
        lines.append("Unknown:")
        lines.extend(result["unknown"])

    return "\n".join(lines)

def process_image(image_path):
    """
    Process a single image and return OCR results.
    """
    return recognize_members(image_path)

def recognize_text_names(lines):
    """
    Matches a list of raw text lines (e.g. names typed or
    pasted into Telegram chat) against known members,
    without OCR.
    """

    cleaned_names = clean_names(lines)
    cleaned_names = remove_duplicates(cleaned_names)

    recognized = []
    unknown = []
    duplicates = []
    seen = set()

    for text in cleaned_names:

        member = find_member(text)

        if member:
            member_name = member["display_name"]

            if member_name not in seen:
                recognized.append(member)
                seen.add(member_name)
            else:
                duplicates.append(member_name)

            continue

        if is_noise(text):
            continue

        unknown.append(text)

    return {
        "recognized": recognized,
        "unknown": unknown,
        "duplicates": duplicates,
    }


def merge_results(*results):
    """
    Combines multiple recognize_* result dicts (e.g. one
    from screenshots, one from typed text) into a single
    result.
    """

    recognized = []
    unknown = []
    duplicates = []
    seen = set()

    for result in results:

        for member in result["recognized"]:

            name = member["display_name"]

            if name not in seen:
                recognized.append(member)
                seen.add(name)
            else:
                duplicates.append(name)

        unknown.extend(result["unknown"])
        duplicates.extend(result["duplicates"])

    return {
        "recognized": recognized,
        "unknown": sorted(set(unknown)),
        "duplicates": sorted(set(duplicates)),
    }