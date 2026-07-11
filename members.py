import re

from config import *


def normalize_alias(text):
    """
    Normalize text for matching.

    Example:
        "Franz Javier Jr." -> "franz javier jr"
        "M. Sarah" -> "m sarah"
    """

    if not text:
        return ""

    text = text.lower().strip()

    # Replace punctuation with spaces
    text = re.sub(r"[^\w\s]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text


# =====================================================
# Alias Lookup
# =====================================================

ALIAS_LOOKUP = {}

for member_id, member in MEMBERS.items():

    aliases = member.get("aliases", [])

    for alias in aliases:

        key = normalize_alias(alias)

        if key:
            ALIAS_LOOKUP[key] = member_id

def find_member(text):

    if not text:
        return None

    key = normalize_alias(text)

    member_id = ALIAS_LOOKUP.get(key)

    if member_id is None:
        return None

    return MEMBERS[member_id]


def find_member_id(text):

    if not text:
        return None

    return ALIAS_LOOKUP.get(
    normalize_alias(text)
)

def member_exists(text):

    return find_member_id(text) is not None


def get_display_name_from_alias(text):

    member = find_member(text)

    if member is None:
        return None

    return member["display_name"]


def get_official_name_from_alias(text):

    member = find_member(text)

    if member is None:
        return None

    return member["official_name"]

# =====================================================
# Service Attendance
# =====================================================

def get_service_members(service, mode=None, active_only=True):
    """
    service = "Sunday", "Wednesday", "Predawn"

    mode:
        None      -> everyone expected
        ONLINE    -> online-only
        ONSITE    -> onsite-capable
        BOTH      -> both online and onsite capable
    """

    members = []

    service = service.lower()

    for member in MEMBERS.values():

        if active_only and member["status"] != ACTIVE:
            continue

        attendance = member["attendance"].get(service)

        if attendance is None:
            continue

        if mode is None:
            members.append(member)

        elif mode == ONLINE:
            if attendance in (ONLINE, BOTH):
                members.append(member)

        elif mode == ONSITE:
            if attendance in (ONSITE, BOTH):
                members.append(member)

        elif mode == BOTH:
            if attendance == BOTH:
                members.append(member)

    members.sort(key=lambda x: (
        x["department"],
        x["sort_order"]
    ))

    return members

def get_department_service_members(
    department,
    service,
    mode=None
):

    members = []

    for member in get_service_members(service, mode):

        if member["department"] == department:
            members.append(member)

    return members


def get_online_only_members():

    members = []

    for member in MEMBERS.values():

        if member["status"] != ACTIVE:
            continue

        if all(
            value == ONLINE
            for value in member["attendance"].values()
        ):
            members.append(member)

    return members


def get_onsite_members():

    members = []

    for member in MEMBERS.values():

        if member["status"] != ACTIVE:
            continue

        if any(
            value in (ONSITE, BOTH)
            for value in member["attendance"].values()
        ):
            members.append(member)

    return members


def is_expected_online(member, service):
    """
    Returns True if the member is expected to attend online
    for the given service.
    """

    service = service.lower()

    mode = member["attendance"].get(service)

    return mode in (ONLINE, BOTH)


def is_expected_onsite(member, service):
    """
    Returns True if the member is allowed to attend onsite
    for the given service.
    """

    service = service.lower()

    mode = member["attendance"].get(service)

    return mode in (ONSITE, BOTH)


def get_attendance_mode(member, service):
    """
    Returns:
        ONLINE
        ONSITE
        BOTH
        None
    """

    return member["attendance"].get(service.lower())


def get_member(member_id):
    return MEMBERS.get(member_id)


def get_display_name(member_id):
    member = MEMBERS.get(member_id)
    return member["display_name"] if member else None


def get_official_name(member_id):
    member = MEMBERS.get(member_id)
    return member["official_name"] if member else None


def get_department(member_id):
    member = MEMBERS.get(member_id)
    return member["department"] if member else None


def get_status(member_id):
    member = MEMBERS.get(member_id)
    return member["status"] if member else None


def get_attendance(member_id):
    member = MEMBERS.get(member_id)
    return member["attendance"] if member else None

def get_active_members():
    return {
        member_id: member
        for member_id, member in MEMBERS.items()
        if member["status"] == ACTIVE
    }

def get_department_members(department, active_only=True):

    members = {}

    for member_id, member in MEMBERS.items():

        if member["department"] != department:
            continue

        if active_only and member["status"] != ACTIVE:
            continue

        members[member_id] = member

    return members


def get_sorted_department_members(department):

    members = list(
        get_department_members(department).values()
    )

    members.sort(key=lambda x: x["sort_order"])

    return members

