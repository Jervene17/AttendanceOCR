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
# Display-name / alias -> member lookup
# =====================================================
# Built once at import time: every alias (and the display
# name and official name themselves) maps to the member's
# full record, so find_member() is an O(1) dict lookup.

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
        DISPLAY_NAME_TO_MEMBER[name] = _member

    # Write the enriched copy back so MEMBERS[id] also carries
    # member_id, matching what DISPLAY_NAME_TO_MEMBER holds.
    MEMBERS[_member_id] = _member


def find_member(text):
    """
    Looks up raw OCR/typed text against every known alias /
    display name / official name. Returns the member dict
    (with member_id) or None if there's no match.
    """
    if not text:
        return None

    return DISPLAY_NAME_TO_MEMBER.get(text.strip())


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