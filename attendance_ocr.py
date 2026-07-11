import easyocr

from cleaner import (
    normalize_name,
    clean_names,
    remove_duplicates,
)
from members import find_member
print("Loading EasyOCR...")

reader = easyocr.Reader(["en"])

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

            member_name = member["name"]

            if member_name not in seen:
                recognized.append(member)
                seen.add(member_name)
            else:
                duplicates.append(member_name)

        else:
            unknown.append(text)

    return {
        "recognized": recognized,
        "unknown": unknown,
        "duplicates": duplicates,
    }
def get_attendee_names(result, sort=True):
    """
    Returns the recognized attendee names.

    Args:
        result: Output from recognize_members()
        sort: If True, return names alphabetically.
              If False, preserve the OCR detection order.
    """

    names = [member["name"] for member in result["recognized"]]

    if sort:
        names.sort()

    return names

def recognize_multiple_images(image_paths):
    """
    Process multiple screenshots and combine the results.
    """

    recognized = []
    unknown = []
    duplicates = []

    seen = set()

    for image_path in image_paths:

        result = process_image(image_path)

        for member in result["recognized"]:

            if member["name"] not in seen:

                recognized.append(member)
                seen.add(member["name"])

            else:

                duplicates.append(member["name"])

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