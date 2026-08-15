# =====================================================
# members.py
#
# Thin layer on top of config.py: re-exports the raw
# roster data (MEMBERS, MEMBER_LISTS, USER_GROUP_MAP,
# ORGANIZER_IDS, ...) and adds lookup helpers used by
# attendance_ocr.py and main.py.
#
# IMPORTANT: this module must NOT import anything from
# attendance_ocr.py. attendance_ocr.py imports from this
# module (find_member), so an import the other way round
# creates a circular import at startup.
# =====================================================

from config import (
    MEMBER_LISTS,
    MEMBERS,
    USER_GROUP_MAP,
    USER_NAMES,
    ORGANIZER_IDS,
    ACTIVE,
    INACTIVE,
    NEWCOMER,
    GROUP_MEMBERS,
)


# =====================================================
# Text normalization for matching
# =====================================================
# attendance_ocr.py runs every OCR/typed name through
# cleaner.clean_names() -> normalize_name() BEFORE calling
# find_member(), so the text find_member() receives is
# already uppercased, punctuation-stripped, and digit/letter
# OCR-corrected (0->O, 1->I, 5->S, |->I).
#
# For find_member() to match anything, the alias index below
# must be built through that exact same normalize_name() —
# not a separate/approximate normalization — otherwise e.g.
# "D.Fatima" (alias) and "DFATIMA" (what clean_names produces
# from OCR/typed "D.Fatima") normalize to different strings
# and never match.
#
# normalize_name() is idempotent, so calling it again inside
# find_member() is safe for callers that pass in raw text
# directly (bypassing clean_names).

from cleaner import normalize_name


# =====================================================
# Display-name / alias -> member lookup
# =====================================================
# Built once at import time: every alias (and the display
# name and official name themselves) maps to the member's
# full record, so find_member() is an O(1) dict lookup on
# the normalized text.

DISPLAY_NAME_TO_MEMBER = {}

for _member_id, _member in MEMBERS.items():

    # Keep the member's own id on the record for convenience.
    _member = dict(_member)
    _member["member_id"] = _member_id

    names_to_index = set(_member.get("aliases", []))
    names_to_index.add(_member["display_name"])

    if _member.get("official_name"):
        names_to_index.add(_member["official_name"])

    for name in names_to_index:
        normalized = normalize_name(name)
        if normalized:
            DISPLAY_NAME_TO_MEMBER[normalized] = _member

    # Write the enriched copy back so MEMBERS[id] also carries
    # member_id, matching what DISPLAY_NAME_TO_MEMBER holds.
    MEMBERS[_member_id] = _member


def find_member(text):
    """
    Looks up OCR/typed text (already normalized by
    cleaner.normalize_name via clean_names(), or raw text —
    normalize_name is idempotent either way) against every
    known alias / display name / official name. Returns the
    member dict (with member_id) or None if there's no match.
    """
    if not text:
        return None

    return DISPLAY_NAME_TO_MEMBER.get(normalize_name(text))


def get_member_type(member):
    """
    Human-readable attendee type shown in the review summary,
    derived from the member's status.
    """
    status = member.get("status")

    if status == NEWCOMER:
        return "Newcomer"

    if status == INACTIVE:
        return "Inactive Member"

    return "Member"


def get_department(member_id):
    member = MEMBERS.get(member_id)
    return member["department"] if member else None


def get_members_by_department(department):
    return {
        member_id: member
        for member_id, member in MEMBERS.items()
        if member["department"] == department
    }