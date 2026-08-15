print("=" * 50)
print("ATTENDANCE OCR V2")
print("Commit: e1a89a9")
print("=" * 50)

import os
import asyncio
import html

print(os.getcwd())

import uuid
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from attendance_ocr import (
    recognize_multiple_images,
    recognize_text_names,
    merge_results,
    attendance_summary,
)

from members import (
    MEMBER_LISTS,
    MEMBERS,
    ORGANIZER_IDS,
    get_member_type,
    DISPLAY_NAME_TO_MEMBER,
)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

print(BOT_TOKEN)
print(WEBHOOK_URL)


user_sessions = {}

# Users who have selected "Special Service/Event" and are expected to
# type the name of that service/event as their next text message.
awaiting_special_service = set()

# Retro-submission flow, keyed by user_id:
# {"service": <str or None>, "awaiting": "name" | "date"}
retro_pending = {}

# =====================================================
# Session Stages
# =====================================================

STAGE_ONLINE = "online"
STAGE_ONSITE = "onsite"
STAGE_REVIEW = "review"

STAGE_VISITOR = "visitor"
STAGE_NEWCOMER = "newcomer"

# Standing service options shown on the selection menu.
SERVICE_OPTIONS = ["Predawn", "Sunday", "Wednesday", "Friday"]

# Colors cycled through for each department's bullet in the review
# summary — purely visual separation, not a status indicator.
DEPARTMENT_COLORS = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤"]


# =====================================================
# Organizer / permission helpers
# =====================================================

def is_organizer(user_id):
    """
    Attendance recording — for every service, including Sunday —
    is limited to the organizer allowlist (config.py: ORGANIZER_IDS).
    There is no longer a separate per-department checker role; the
    2 organizers handle both online and onsite entry themselves.
    """
    return user_id in ORGANIZER_IDS


async def require_organizer(reply_func, user_id):
    """
    Sends a rejection message and returns False if user_id is not
    an organizer; returns True (and sends nothing) if they are.
    """
    if is_organizer(user_id):
        return True

    await reply_func(
        "🚫 Attendance recording is limited to organizers."
    )
    return False


# =====================================================
# Session bootstrap
# =====================================================

async def begin_session(user_id, service, reply_func, service_date=None, is_retro=False):
    """
    Creates a new attendance session for user_id and sends the
    opening instructions via reply_func (a callable that takes a
    string and returns an awaitable, e.g. message.reply_text).

    service_date: "YYYY-MM-DD" override for retro submissions.
    Defaults to today (Asia/Manila) when not given.
    """

    user_sessions[user_id] = {

        "service": service,

        "service_date": service_date or datetime.now(
            ZoneInfo("Asia/Manila")
        ).strftime("%Y-%m-%d"),

        "is_retro": is_retro,

        "stage": STAGE_ONLINE,

        # Uploaded screenshots
        "online_images": [],
        "onsite_images": [],
        "onsite_text_names": [],

        # OCR Results
        "online_result": None,
        "onsite_result": None,

        # Master Attendance
        "recognized": set(),
        "online_members": set(),
        "onsite_members": set(),
        "unknown": set(),
        "unknown_sources": {},

        # Manual additions
        "newcomers": [],
        "visitors": [],
        "visitor_pending_name": None,
        "visitor_pending_from": None,
        "newcomer_pending_name": None,
        "newcomer_pending_department": None,

        # Department verification
        "current_department": None,

        # Resolve-triggered visitor/newcomer entry (converting an
        # unrecognized OCR/text name into a visitor or newcomer
        # instead of matching it to a member)
        "resolve_as": None,
        "resolve_visitor_name": None,
        "resolve_newcomer_name": None,

    }

    header = f"{service} Attendance"

    if is_retro:
        header += f" — 🕒 RETRO ({user_sessions[user_id]['service_date']})"

    await reply_func(
        f"{header}\n\n"
        "Please upload ONLINE participant screenshots.\n\n"
        "When finished, type:\n"
        "/done"
    )


def build_service_keyboard(prefix):

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"{prefix}:{name}")]
        for name in SERVICE_OPTIONS
    ]

    keyboard.append(
        [InlineKeyboardButton("✨ Special Service/Event", callback_data=f"{prefix}:special")]
    )

    return InlineKeyboardMarkup(keyboard)


async def send_service_menu(message, user_id):

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"svc:{name}")]
        for name in SERVICE_OPTIONS
    ]

    keyboard.append(
        [InlineKeyboardButton("✨ Special Service/Event", callback_data="svc:special")]
    )

    keyboard.append(
        [InlineKeyboardButton("🕒 Retro Submission", callback_data="retro_menu")]
    )

    await message.reply_text(
        "Attendance Bot V2 is ready.\n\n"
        "Select a service:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await require_organizer(update.message.reply_text, user_id):
        return

    await send_service_menu(update.message, user_id)


async def retro(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await require_organizer(update.message.reply_text, user_id):
        return

    await update.message.reply_text(
        "🕒 Retro Submission — select the service:",
        reply_markup=build_service_keyboard("rsvc"),
    )


# Kept as direct shortcuts so existing habits/automation still work,
# in addition to the new inline-keyboard menu.
async def start_service(update, context, service):

    user_id = update.effective_user.id

    if not await require_organizer(update.message.reply_text, user_id):
        return

    await begin_session(user_id, service, update.message.reply_text)


async def predawn(update, context):
    await start_service(update, context, "Predawn")


async def sunday(update, context):
    await start_service(update, context, "Sunday")


async def wednesday(update, context):
    await start_service(update, context, "Wednesday")


async def friday(update, context):
    await start_service(update, context, "Friday")


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "No active attendance session. Start one with /start."
        )
        return

    session = user_sessions[user_id]

    if update.message.photo:
        photo_file = update.message.photo[-1]

    elif update.message.document:
        photo_file = update.message.document

    else:
        await update.message.reply_text("Please send an image.")
        return

    try:
        file = await photo_file.get_file()
    except Exception as e:
        print("GET_FILE ERROR:", repr(e))
        raise

    os.makedirs("temp", exist_ok=True)

    filename = f"temp/{uuid.uuid4()}.jpg"

    await file.download_to_drive(filename)

    if session["stage"] == STAGE_ONLINE:
        session["online_images"].append(filename)

        await update.message.reply_text(
            f"✅ Online screenshot saved.\n"
            f"Total: {len(session['online_images'])}\n\n"
            "Upload another image or type /done."
        )

    elif session["stage"] == STAGE_ONSITE:
        session["onsite_images"].append(filename)

        await update.message.reply_text(
            f"✅ Onsite screenshot saved.\n"
            f"Total: {len(session['onsite_images'])}\n\n"
            "Upload another image or type /done."
        )

    else:
        await update.message.reply_text("Not currently expecting a screenshot.")


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    text = update.message.text

    if not text:
        return

    # User previously tapped "Special Service/Event" and is now
    # typing the name of that service/event.
    if user_id in awaiting_special_service:

        awaiting_special_service.discard(user_id)

        service_name = text.strip()

        if not service_name:
            await update.message.reply_text(
                "Please type a valid name for the Service/Event."
            )
            awaiting_special_service.add(user_id)
            return

        # Retro flow: still need a date before starting the session.
        if user_id in retro_pending:
            retro_pending[user_id]["service"] = service_name
            retro_pending[user_id]["awaiting"] = "date"

            await update.message.reply_text(
                f"🕒 Retro: {service_name}\n\n"
                "Please type the date this attendance is for (YYYY-MM-DD):"
            )
            return

        await begin_session(user_id, service_name, update.message.reply_text)
        return

    # Retro flow: user is typing the date for their retro submission.
    if user_id in retro_pending and retro_pending[user_id].get("awaiting") == "date":

        date_text = text.strip()

        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid date in YYYY-MM-DD format (e.g. 2026-08-09)."
            )
            return

        service = retro_pending.pop(user_id)["service"]

        await begin_session(
            user_id,
            service,
            update.message.reply_text,
            service_date=parsed_date.strftime("%Y-%m-%d"),
            is_retro=True,
        )
        return

    if user_id not in user_sessions:
        return

    session = user_sessions[user_id]

    # -----------------------------
    # RESOLVE-TRIGGERED VISITOR / NEWCOMER ENTRY
    # (an unrecognized OCR/text name being converted into a
    # visitor or newcomer instead of matched to a member)
    # -----------------------------
    if session.get("resolve_as") == "visitor":

        typed = text.strip()

        if not typed:
            return

        if session.get("resolve_visitor_name") is None:

            session["resolve_visitor_name"] = typed

            await update.message.reply_text(
                f"The visitor \"{typed}\" is from?"
            )

        else:

            resolved_text = session.pop("resolving_text", None)
            src = session["unknown_sources"].pop(resolved_text, None) if resolved_text else None
            source = "Online" if src == "online" else "Onsite"

            session["visitors"].append({
                "name": session.pop("resolve_visitor_name"),
                "from": typed,
                "source": source,
            })

            if resolved_text:
                session["unknown"].discard(resolved_text)

            session["resolve_as"] = None
            session.pop("resolve_added_members", None)

            await update.message.reply_text(f"✅ Visitor added ({source}).")

            if "resolve_continue" in session:

                still_pending = await advance_resolve_queue(update.message.reply_text, session)

                if not still_pending:
                    tag = session.pop("resolve_continue", None)
                    session.pop("resolve_queue", None)

                    if tag == "post_online":
                        await continue_after_online(update.message.reply_text, context, user_id, session)

                    elif tag == "post_onsite":
                        session["stage"] = STAGE_REVIEW
                        await send_review(update.message.reply_text, session)

            else:
                await send_review(update.message.reply_text, session)

        return

    if session.get("resolve_as") == "newcomer":

        typed = text.strip()

        if not typed:
            return

        if session.get("resolve_newcomer_name") is None:

            session["resolve_newcomer_name"] = typed

            await update.message.reply_text(
                f"Department for \"{typed}\"?",
                reply_markup=build_department_picker("rndept")
            )

        else:

            await update.message.reply_text(
                "Please choose a department using the buttons above."
            )

        return

    # -----------------------------
    # VISITOR NAME / "FROM" / SOURCE ENTRY
    # -----------------------------
    if session["stage"] == STAGE_VISITOR:

        typed = text.strip()

        if not typed:
            return

        if session.get("visitor_pending_name") is None:

            session["visitor_pending_name"] = typed

            await update.message.reply_text(
                f"The visitor \"{typed}\" is from?"
            )

        elif session.get("visitor_pending_from") is None:

            session["visitor_pending_from"] = typed

            await update.message.reply_text(
                f"Was {session['visitor_pending_name']} Online or Onsite?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("💻 Online", callback_data="vsrc:Online"),
                        InlineKeyboardButton("🏛 Onsite", callback_data="vsrc:Onsite"),
                    ]
                ])
            )

        else:

            # Name and "from" are both captured — we're just
            # waiting on the Online/Onsite button tap.
            await update.message.reply_text(
                "Please tap Online or Onsite above, or /done to return to the review."
            )

        return

    # -----------------------------
    # NEWCOMER NAME / DEPARTMENT / SOURCE ENTRY
    # -----------------------------
    if session["stage"] == STAGE_NEWCOMER:

        if session.get("newcomer_pending_name") is not None:

            await update.message.reply_text(
                "Please choose an option using the buttons above, "
                "or type /done to return to the review."
            )
            return

        name = text.strip()

        if not name:
            return

        session["newcomer_pending_name"] = name

        await update.message.reply_text(
            f"Department for \"{name}\"?",
            reply_markup=build_department_picker("ndept")
        )

        return

    if session["stage"] != STAGE_ONSITE:
        return

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    session["onsite_text_names"].extend(lines)

    await update.message.reply_text(
        f"✅ Added {len(lines)} name(s) from text.\n"
        f"Total from text: {len(session['onsite_text_names'])}\n\n"
        "Send more names, upload screenshots, or type /done."
    )


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "No active attendance session."
        )
        return

    session = user_sessions[user_id]

    # -----------------------------
    # ONLINE COMPLETE
    # -----------------------------
    if session["stage"] == STAGE_ONLINE:
        print("ONLINE IMAGES =", session["online_images"])
        print("STAGE =", session["stage"])
        if not session["online_images"]:
            await update.message.reply_text(
                "Please upload at least one online screenshot."
            )
            return

        await update.message.reply_text(
            "Processing online screenshots..."
        )

        result = await asyncio.to_thread(recognize_multiple_images, session["online_images"])

        session["online_result"] = result

        update_master_attendance(
            session,
            result,
            "online"
        )

        # This summary is its own standalone message (not edited
        # later), so it stays visible in the chat permanently.
        await update.message.reply_text(
            "🟢 ONLINE — Verification\n\n" + attendance_summary(result)
        )

        # Some OCR "unknown" reads are just noise, not real names —
        # let the organizer pick which ones actually need to be
        # matched to a member. Anything left unselected is ignored.
        if session["unknown"]:
            session["resolve_continue"] = "post_online"
            await start_verify_selection(update.message.reply_text, session)
            return

        await continue_after_online(update.message.reply_text, context, user_id, session)
        return

    # -----------------------------
    # ONSITE COMPLETE
    # -----------------------------
    if session["stage"] == STAGE_ONSITE:

        has_images = bool(session["onsite_images"])
        has_text = bool(session["onsite_text_names"])

        if not has_images and not has_text:

            await update.message.reply_text(

                "No onsite screenshots or names uploaded.\n\n"

                "If nobody attended onsite,\n"

                "type /skip"

            )

            return

        await update.message.reply_text(
            "Processing onsite attendance..."
        )

        results_to_merge = []

        if has_images:
            image_result = await asyncio.to_thread(
                recognize_multiple_images,
                session["onsite_images"]
            )
            results_to_merge.append(image_result)

        if has_text:
            text_result = recognize_text_names(session["onsite_text_names"])
            results_to_merge.append(text_result)

        result = merge_results(*results_to_merge)

        session["onsite_result"] = result

        update_master_attendance(
            session,
            result,
            "onsite"
        )

        # Same as online: a standalone message showing exactly who
        # was identified from the onsite screenshots/names, so it
        # can be checked against and stays in the chat permanently.
        await update.message.reply_text(
            "🟡 ONSITE — Verification\n\n" + attendance_summary(result)
        )

        # Same selection step as online: pick which unrecognized
        # names actually need matching; the rest are ignored.
        if session["unknown"]:
            session["resolve_continue"] = "post_onsite"
            await start_verify_selection(update.message.reply_text, session)
            return

        session["stage"] = STAGE_REVIEW
        await send_review(update.message.reply_text, session)
        return

    # -----------------------------
    # VISITOR / NEWCOMER ENTRY DONE
    # -----------------------------
    if session["stage"] in (STAGE_VISITOR, STAGE_NEWCOMER):

        session["stage"] = STAGE_REVIEW
        session["visitor_pending_name"] = None
        session["visitor_pending_from"] = None
        session["newcomer_pending_name"] = None
        session["newcomer_pending_department"] = None

        await send_review(update.message.reply_text, session)

        return


# =====================================================
# Unknown-name resolution (right after OCR)
# =====================================================
# Not every OCR "unknown" is actually a name that needs verifying —
# some are just noise. So first, the organizer picks which unknown
# entries are worth resolving; anything left unselected is ignored
# entirely. Only the selected ones then go through the mandatory
# department -> specific-member matching flow before the stage can
# proceed. A "Skip" escape hatch also exists per selected name in
# case it's genuinely not a member (a visitor, a bad OCR read),
# leaving that one name in the Unknown list for the review screen.
#
# Each name can be matched to MORE THAN ONE member — for the case
# where two (or three) people are sharing a single Zoom account —
# via "➕ Add Another Member" before confirming Done.

def build_verify_selection_text(session):
    return (
        "❓ Some names weren't recognized.\n\n"
        "Select which ones actually need to be matched to a member — "
        "anything left unselected will be ignored."
    )


def build_verify_selection_keyboard(session):

    keyboard = []

    for i, name in enumerate(session["verify_candidates"]):

        checked = name in session["verify_selected"]

        keyboard.append(
            [InlineKeyboardButton(
                f"{'☑️' if checked else '☐'} {name}",
                callback_data=f"vtoggle:{i}"
            )]
        )

    keyboard.append(
        [
            InlineKeyboardButton("☑️ Select All", callback_data="vall"),
            InlineKeyboardButton("☐ Clear All", callback_data="vnone"),
        ]
    )

    keyboard.append(
        [InlineKeyboardButton("✅ Confirm Selection", callback_data="vconfirm")]
    )

    return InlineKeyboardMarkup(keyboard)


async def start_verify_selection(send_func, session):

    session["verify_candidates"] = sorted(session["unknown"])
    session["verify_selected"] = set()

    await send_func(
        text=build_verify_selection_text(session),
        reply_markup=build_verify_selection_keyboard(session)
    )


def build_resolve_prompt_text(session):
    name = session.get("resolving_text", "")
    return f"❓ Unrecognized name: \"{name}\"\n\nWhich department do they belong to?"


async def advance_resolve_queue(send_func, session):
    """
    Pops the next unresolved name and prompts for its department.
    Returns True if a prompt was sent (still resolving), False if
    the queue is now empty.
    """

    queue = session.get("resolve_queue")

    if queue:
        session["resolving_text"] = queue.pop(0)
        session["resolve_added_members"] = set()

        await send_func(
            text=build_resolve_prompt_text(session),
            reply_markup=build_department_picker("adept")
        )
        return True

    return False


async def continue_after_online(send_func, context, user_id, session):
    """
    Every service (including Sunday) now follows the same path:
    the organizer uploads/types onsite attendance directly. There
    is no longer a department-checker handoff.
    """

    session["stage"] = STAGE_ONSITE

    await send_func(
        text=(
            "✅ Online attendance completed.\n\n"
            "Now upload ONSITE screenshots, or type/paste names "
            "(one per line) directly in chat.\n\n"
            "When finished, type /done."
        )
    )


async def send_review(send_func, session):
    await send_func(
        text=render_review_text(session),
        reply_markup=build_review_keyboard(session),
        parse_mode="HTML",
    )


async def show_review(update, context):
    user_id = update.effective_user.id
    session = user_sessions[user_id]
    await send_review(update.message.reply_text, session)


def build_department_picker(prefix):
    """
    Inline keyboard of departments, each posting back
    "{prefix}:{department}" when tapped.
    """

    keyboard = [
        [InlineKeyboardButton(department, callback_data=f"{prefix}:{department}")]
        for department in MEMBER_LISTS
    ]

    return InlineKeyboardMarkup(keyboard)


def update_master_attendance(session, result, source):
    """
    Update the master attendance sets from an OCR result.

    source:
        "online"
        "onsite"

    Onsite always overrides online: if a member is recognized
    onsite, they are treated as physically present onsite even if
    they were also seen joining the Zoom link (source is set to
    "onsite" and any prior "online" mark for them is removed).
    """

    for member in result["recognized"]:

        name = member["display_name"]

        session["recognized"].add(name)

        if source == "online":
            # Don't downgrade someone already confirmed onsite.
            if name not in session["onsite_members"]:
                session["online_members"].add(name)

        elif source == "onsite":
            session["onsite_members"].add(name)
            session["online_members"].discard(name)

    for name in result["unknown"]:

        session["unknown"].add(name)

        existing_source = session["unknown_sources"].get(name)

        if existing_source and existing_source != source:
            session["unknown_sources"][name] = "both"
        else:
            session["unknown_sources"].setdefault(name, source)


def get_member_info(name):
    """
    Looks up a display name in the master MEMBERS registry (for
    accurate department + type -- e.g. "Missionary", "Head Leader",
    "Newcomer"), falling back to MEMBER_LISTS if somehow not found
    there.
    """

    member = DISPLAY_NAME_TO_MEMBER.get(name)

    if member:
        return {
            "name": member["display_name"],
            "department": member["department"],
            "type": get_member_type(member),
        }

    for department, members in MEMBER_LISTS.items():

        if name in members:

            return {
                "name": name,
                "department": department,
                "type": "Member"
            }

    return None


def render_review_text(session):

    recognized = session["recognized"]
    online_members = session["online_members"]
    onsite_members = session["onsite_members"]

    lines = []

    service_date = session["service_date"]
    day_name = datetime.strptime(service_date, "%Y-%m-%d").strftime("%A")

    lines.append(f"📊 {html.escape(session['service'])} Attendance Review")
    lines.append(f"🗓 {day_name}, {service_date}")
    lines.append("")

    total_present = 0
    total_online = 0
    total_onsite = 0

    for i, (department, members) in enumerate(MEMBER_LISTS.items()):

        color = DEPARTMENT_COLORS[i % len(DEPARTMENT_COLORS)]

        present_members = [
            member_name
            for member_name in members
            if member_name in recognized
        ]

        total_present += len(present_members)

        lines.append(f"{color} {html.escape(department)}: {len(present_members)}")

        for member in present_members:

            if member in onsite_members:
                # Onsite attendees are bolded so they stand out at a
                # glance against the Online ones.
                tag_display = "<b>Onsite</b>"
                total_onsite += 1
            elif member in online_members:
                tag_display = "Online"
                total_online += 1
            else:
                # No explicit online/onsite source recorded (e.g.
                # added manually via "Verify Department") — default
                # to Onsite, same as before.
                tag_display = "<b>Onsite</b>"
                total_onsite += 1

            lines.append(f"   • {html.escape(member)} ({tag_display})")

    for visitor in session["visitors"]:
        total_present += 1
        if visitor.get("source") == "Online":
            total_online += 1
        else:
            total_onsite += 1

    for newcomer in session["newcomers"]:
        total_present += 1
        if newcomer.get("source") == "Online":
            total_online += 1
        else:
            total_onsite += 1

    lines.append("")
    lines.append(f"👥 Total Present: {total_present}")
    lines.append(f"💻 Total Online: {total_online}")
    lines.append(f"🏛 Total Onsite: {total_onsite}")

    if session["unknown"]:
        lines.append("")
        lines.append("❓ Unknown Names")

        for name in sorted(session["unknown"]):
            lines.append(f"• {html.escape(name)}")

    if session["visitors"]:
        lines.append("")
        lines.append("👥 Visitors")

        for visitor in session["visitors"]:
            source = visitor.get("source", "")
            source_part = f", {html.escape(source)}" if source else ""
            lines.append(
                f"• {html.escape(visitor['name'])} (from {html.escape(visitor['from'])}{source_part})"
            )

    if session["newcomers"]:
        lines.append("")
        lines.append("🌱 Newcomers")

        for newcomer in session["newcomers"]:
            source = newcomer.get("source", "")
            source_part = f", {html.escape(source)}" if source else ""
            lines.append(
                f"• {html.escape(newcomer['name'])} ({html.escape(newcomer['department'])}{source_part})"
            )

    return "\n".join(lines)


def build_review_keyboard(session):

    keyboard = [
        [
            InlineKeyboardButton(
                "✔ Verify Department",
                callback_data="verify"
            )
        ],
    ]

    if session["unknown"]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔍 Resolve Unknown",
                    callback_data="resolve"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ Visitor",
                callback_data="visitor"
            ),
            InlineKeyboardButton(
                "➕ Newcomer",
                callback_data="newcomer"
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "✅ Submit",
                callback_data="submit"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel"
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


async def show_departments(query, session):

    keyboard = []

    for department in MEMBER_LISTS:

        keyboard.append(
            [
                InlineKeyboardButton(
                    department,
                    callback_data=f"dept:{department}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="review"
            )
        ]
    )

    await query.edit_message_text(

        "Choose a department to verify.",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


async def show_department_members(
    query,
    session,
    department,
):
    """
    Verify-Department screen for one department. Each member is a
    toggle button (tap to mark present, tap again to unmark), plus
    Select All / Clear All so a mostly-full department can be marked
    present in one tap and the few absentees un-tapped individually,
    instead of typing/tapping every name in.
    """

    recognized = session["recognized"]

    keyboard = []

    lines = []

    lines.append(f"📋 {department}")
    lines.append("")

    members = MEMBER_LISTS[department]

    present = 0

    for member in members:

        checked = member in recognized

        if checked:
            present += 1

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{'✅' if checked else '➕'} {member}",
                    callback_data=f"present:{member}"
                )
            ]
        )

    lines.append(
        f"Present: {present}/{len(members)}"
    )
    lines.append("")
    lines.append(
        "Tap a name to toggle present/absent. Use Select All to mark "
        "everyone present, then untap the few who are absent."
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "☑️ Select All",
                callback_data=f"deptall:{department}"
            ),
            InlineKeyboardButton(
                "☐ Clear All",
                callback_data=f"deptnone:{department}"
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅ Departments",
                callback_data="verify"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🏠 Attendance Review",
                callback_data="review"
            )
        ]
    )

    await query.edit_message_text(

        "\n".join(lines),

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


async def show_unknown_list(query, session):

    unknown_sorted = sorted(session["unknown"])
    session["unknown_sorted"] = unknown_sorted

    if not unknown_sorted:
        await query.edit_message_text(
            "No unknown names to resolve.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Attendance Review", callback_data="review")]
            ])
        )
        return

    keyboard = []

    for i, name in enumerate(unknown_sorted):
        keyboard.append(
            [InlineKeyboardButton(name, callback_data=f"unk:{i}")]
        )

    keyboard.append(
        [InlineKeyboardButton("🏠 Attendance Review", callback_data="review")]
    )

    await query.edit_message_text(
        "❓ Select an unknown name to resolve:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_resolve_departments(query, session):

    keyboard = [
        [InlineKeyboardButton("👋 Mark as Visitor", callback_data="rvisitor")],
        [InlineKeyboardButton("🌱 Mark as Newcomer", callback_data="rnewcomer")],
    ]

    for department in MEMBER_LISTS:
        keyboard.append(
            [InlineKeyboardButton(department, callback_data=f"adept:{department}")]
        )

    keyboard.append(
        [InlineKeyboardButton("⬅ Back", callback_data="resolve")]
    )

    text = session.get("resolving_text", "")

    await query.edit_message_text(
        f"Resolving: \"{text}\"\n\nChoose their department, or mark as Visitor/Newcomer if they're not a member:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_resolve_members(query, session, department):

    keyboard = []
    added = session.get("resolve_added_members", set())

    for member in MEMBER_LISTS[department]:

        label = f"✅ {member}" if member in added else member

        keyboard.append(
            [InlineKeyboardButton(label, callback_data=f"aassign:{member}")]
        )

    keyboard.append(
        [InlineKeyboardButton("⏭ Skip (leave unresolved)", callback_data="askip")]
    )

    keyboard.append(
        [InlineKeyboardButton("⬅ Departments", callback_data="resolve")]
    )

    text = session.get("resolving_text", "")

    await query.edit_message_text(
        f"Resolving: \"{text}\"\n\n{department} — who is this?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_resolve_confirm(query, session):
    """
    Shown after at least one member has been matched to the current
    unrecognized name — lets the organizer add another member (for
    two/three people sharing one Zoom account) or confirm Done.
    """

    added = session.get("resolve_added_members", set())
    text = session.get("resolving_text", "")

    lines = [f"Resolving: \"{text}\"", "", "Matched to:"]

    for member in sorted(added):
        lines.append(f"• {member}")

    lines.append("")
    lines.append(
        "If another person is sharing this same account, add them too. "
        "Otherwise, tap Done."
    )

    keyboard = [
        [InlineKeyboardButton("➕ Add Another Member", callback_data="raddmore")],
        [InlineKeyboardButton("✅ Done", callback_data="adone")],
    ]

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_review_callback(query, session):

    await query.edit_message_text(
        render_review_text(session),
        reply_markup=build_review_keyboard(session),
        parse_mode="HTML",
    )


async def submit_attendance(session):

    members = []

    for name in sorted(session["recognized"]):

        info = get_member_info(name)

        if not info:
            continue

        if (
            name in session["online_members"]
            and name in session["onsite_members"]
        ):
            source = "Both"

        elif name in session["onsite_members"]:
            source = "Onsite"

        elif name in session["online_members"]:
            source = "Online"

        else:
            source = "Onsite"

        members.append({

            "name": info["name"],

            "department": info["department"],

            "type": info["type"],

            "source": source,

        })

    # Visitors and newcomers are folded into the same "members"
    # list as regular attendees (type="Visitor"/"Newcomer"), so
    # they get a real "source" (Online/Onsite) in the sheet
    # instead of showing up blank/unknown, and newcomers count
    # together with manually-added ones.
    for visitor in session["visitors"]:
        members.append({
            "name": visitor["name"],
            "department": visitor["from"],
            "type": "Visitor",
            "source": visitor.get("source", "Onsite"),
        })

    for newcomer in session["newcomers"]:
        members.append({
            "name": newcomer["name"],
            "department": newcomer["department"],
            "type": "Newcomer",
            "source": newcomer.get("source", "Onsite"),
        })

    payload = {

        "service": session["service"],

        "service_date": session["service_date"],

        "members": members,

    }

    response = await asyncio.to_thread(
        requests.post,
        WEBHOOK_URL,
        json=payload,
        timeout=30,
    )

    return response


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    action = query.data

    if not is_organizer(user_id):
        await query.edit_message_text(
            "🚫 Attendance recording is limited to organizers."
        )
        return

    # -----------------------------
    # Service selection menu
    # -----------------------------
    if action.startswith("svc:"):

        choice = action.split(":", 1)[1]

        if choice == "special":

            awaiting_special_service.add(user_id)

            await query.edit_message_text(
                "Please type the name of the Service/Event:"
            )

        else:

            await query.edit_message_text(
                f"Starting {choice} Attendance..."
            )

            await begin_session(user_id, choice, query.message.reply_text)

        return

    # -----------------------------
    # Retro submission menu
    # -----------------------------
    if action == "retro_menu":

        await query.edit_message_text(
            "🕒 Retro Submission — select the service:",
            reply_markup=build_service_keyboard("rsvc"),
        )
        return

    if action.startswith("rsvc:"):

        choice = action.split(":", 1)[1]

        if choice == "special":

            awaiting_special_service.add(user_id)
            retro_pending[user_id] = {"service": None, "awaiting": "name"}

            await query.edit_message_text(
                "Please type the name of the Service/Event:"
            )

        else:

            retro_pending[user_id] = {"service": choice, "awaiting": "date"}

            await query.edit_message_text(
                f"🕒 Retro: {choice}\n\n"
                "Please type the date this attendance is for (YYYY-MM-DD):"
            )

        return

    if user_id not in user_sessions:

        await query.edit_message_text(
            "This attendance session has already ended."
        )
        return

    # -----------------------------
    # Which unknown names actually need verifying
    # -----------------------------
    if action.startswith("vtoggle:"):

        session = user_sessions[user_id]

        if "verify_candidates" not in session:
            return

        idx = int(action.split(":", 1)[1])
        name = session["verify_candidates"][idx]
        selected = session.setdefault("verify_selected", set())

        if name in selected:
            selected.discard(name)
        else:
            selected.add(name)

        await query.edit_message_text(
            build_verify_selection_text(session),
            reply_markup=build_verify_selection_keyboard(session)
        )

        return

    if action == "vall":

        session = user_sessions[user_id]

        if "verify_candidates" not in session:
            return

        session["verify_selected"] = set(session["verify_candidates"])

        await query.edit_message_text(
            build_verify_selection_text(session),
            reply_markup=build_verify_selection_keyboard(session)
        )

        return

    if action == "vnone":

        session = user_sessions[user_id]

        if "verify_candidates" not in session:
            return

        session["verify_selected"] = set()

        await query.edit_message_text(
            build_verify_selection_text(session),
            reply_markup=build_verify_selection_keyboard(session)
        )

        return

    if action == "vconfirm":

        session = user_sessions[user_id]

        if "verify_candidates" not in session:
            return

        candidates = session.pop("verify_candidates", [])
        selected = session.pop("verify_selected", set())
        ignored = [n for n in candidates if n not in selected]

        # Ignored names are dropped entirely — not resolved, not
        # left sitting in the Unknown list either.
        for name in ignored:
            session["unknown"].discard(name)
            session["unknown_sources"].pop(name, None)

        await query.edit_message_text(
            f"✅ {len(selected)} name(s) selected for verification. "
            f"{len(ignored)} ignored."
        )

        if selected:
            session["resolve_queue"] = sorted(selected)
            await advance_resolve_queue(query.message.reply_text, session)
            return

        # Nothing selected — nothing to resolve, proceed straight
        # to whatever comes after this stage.
        tag = session.pop("resolve_continue", None)
        session.pop("resolve_queue", None)

        if tag == "post_online":
            await continue_after_online(query.message.reply_text, context, user_id, session)

        elif tag == "post_onsite":
            session["stage"] = STAGE_REVIEW
            await send_review(query.message.reply_text, session)

        return

    if action == "verify":

        await show_departments(query, user_sessions[user_id])

        return

    elif action == "resolve":

        await show_unknown_list(query, user_sessions[user_id])

        return

    elif action.startswith("unk:"):

        session = user_sessions[user_id]

        idx = int(action.split(":", 1)[1])

        session["resolving_text"] = session["unknown_sorted"][idx]
        session["resolve_added_members"] = set()

        await show_resolve_departments(query, session)

        return

    elif action.startswith("adept:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]

        await show_resolve_members(query, session, department)

        return

    elif action == "raddmore":

        session = user_sessions[user_id]

        await show_resolve_departments(query, session)

        return

    elif action == "rvisitor":

        session = user_sessions[user_id]

        session["resolve_as"] = "visitor"

        await query.message.reply_text(
            f"Enter the visitor's correct name (OCR read: \"{session.get('resolving_text', '')}\"):"
        )

        return

    elif action == "rnewcomer":

        session = user_sessions[user_id]

        session["resolve_as"] = "newcomer"

        await query.message.reply_text(
            f"Enter the newcomer's correct name (OCR read: \"{session.get('resolving_text', '')}\"):"
        )

        return

    elif action.startswith("rndept:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]

        name = session.pop("resolve_newcomer_name", None)
        resolved_text = session.pop("resolving_text", None)

        if name:

            src = session["unknown_sources"].pop(resolved_text, None) if resolved_text else None
            source = "Online" if src == "online" else "Onsite"

            session["newcomers"].append({
                "name": name,
                "department": department,
                "source": source,
            })

            if resolved_text:
                session["unknown"].discard(resolved_text)

            session["resolve_as"] = None
            session.pop("resolve_added_members", None)

            await query.edit_message_text(
                f"✅ Newcomer added: {name} ({department}, {source})"
            )

        if "resolve_continue" in session:

            still_pending = await advance_resolve_queue(query.message.reply_text, session)

            if not still_pending:
                tag = session.pop("resolve_continue", None)
                session.pop("resolve_queue", None)

                if tag == "post_online":
                    await continue_after_online(query.message.reply_text, context, user_id, session)

                elif tag == "post_onsite":
                    session["stage"] = STAGE_REVIEW
                    await send_review(query.message.reply_text, session)

            return

        await show_review_callback(query, session)

        return

    elif action == "askip":

        session = user_sessions[user_id]

        session.pop("resolving_text", None)
        session.pop("resolve_added_members", None)

        if "resolve_continue" in session:

            still_pending = await advance_resolve_queue(query.message.reply_text, session)

            if not still_pending:
                tag = session.pop("resolve_continue", None)
                session.pop("resolve_queue", None)

                if tag == "post_online":
                    await continue_after_online(query.message.reply_text, context, user_id, session)

                elif tag == "post_onsite":
                    session["stage"] = STAGE_REVIEW
                    await send_review(query.message.reply_text, session)

            return

        await show_review_callback(query, session)

        return

    elif action.startswith("aassign:"):

        member = action.split(":", 1)[1]

        session = user_sessions[user_id]

        resolved_text = session.get("resolving_text")

        added_members = session.setdefault("resolve_added_members", set())

        if member not in added_members:

            added_members.add(member)

            session["recognized"].add(member)

            if resolved_text:

                src = session["unknown_sources"].get(resolved_text)

                # Onsite overrides online here too.
                if src in ("onsite", "both"):
                    session["onsite_members"].add(member)
                    session["online_members"].discard(member)

                elif src == "online":
                    session["online_members"].add(member)

        await show_resolve_confirm(query, session)

        return

    elif action == "adone":

        session = user_sessions[user_id]

        resolved_text = session.pop("resolving_text", None)
        session.pop("resolve_added_members", None)

        if resolved_text:
            session["unknown"].discard(resolved_text)
            session["unknown_sources"].pop(resolved_text, None)

        if "resolve_continue" in session:

            still_pending = await advance_resolve_queue(query.message.reply_text, session)

            if not still_pending:
                tag = session.pop("resolve_continue", None)
                session.pop("resolve_queue", None)

                if tag == "post_online":
                    await continue_after_online(query.message.reply_text, context, user_id, session)

                elif tag == "post_onsite":
                    session["stage"] = STAGE_REVIEW
                    await send_review(query.message.reply_text, session)

            return

        await show_review_callback(query, session)

        return

    elif action.startswith("dept:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]

        session["current_department"] = department

        await show_department_members(
            query,
            session,
            department
        )

        return

    elif action.startswith("present:"):

        member = action.split(":", 1)[1]

        session = user_sessions[user_id]

        department = session["current_department"]

        # Toggle: tap an absent member to mark present, tap a
        # present member to unmark them.
        if member in session["recognized"]:
            session["recognized"].discard(member)
            session["onsite_members"].discard(member)
            session["online_members"].discard(member)
        else:
            session["recognized"].add(member)
            # Manually marked via Verify Department -> treated as
            # onsite, same convention as before.
            session["onsite_members"].add(member)
            session["unknown"].discard(member)

        # Refresh department screen
        await show_department_members(
            query,
            session,
            department
        )

        return

    elif action.startswith("deptall:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]
        session["current_department"] = department

        for member in MEMBER_LISTS[department]:
            session["recognized"].add(member)
            session["onsite_members"].add(member)

        await show_department_members(
            query,
            session,
            department
        )

        return

    elif action.startswith("deptnone:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]
        session["current_department"] = department

        for member in MEMBER_LISTS[department]:
            session["recognized"].discard(member)
            session["onsite_members"].discard(member)
            session["online_members"].discard(member)

        await show_department_members(
            query,
            session,
            department
        )

        return

    elif action == "visitor":

        session = user_sessions[user_id]

        session["stage"] = STAGE_VISITOR
        session["visitor_pending_name"] = None
        session["visitor_pending_from"] = None

        await query.message.reply_text(

            "Enter the visitor's name.\n\n"

            "When finished adding visitors, type /done."

        )

        return

    elif action == "newcomer":

        session = user_sessions[user_id]

        session["stage"] = STAGE_NEWCOMER
        session["newcomer_pending_name"] = None
        session["newcomer_pending_department"] = None

        await query.message.reply_text(

            "Enter the newcomer's name.\n\n"

            "When finished adding newcomers, type /done."

        )

        return

    elif action.startswith("vsrc:"):

        source = action.split(":", 1)[1]

        session = user_sessions[user_id]

        pending_name = session.get("visitor_pending_name")
        pending_from = session.get("visitor_pending_from")

        if pending_name and pending_from:

            session["visitors"].append({
                "name": pending_name,
                "from": pending_from,
                "source": source,
            })

            session["visitor_pending_name"] = None
            session["visitor_pending_from"] = None

            await query.edit_message_text(
                f"✅ Visitor added: {pending_name} (from {pending_from}, {source})"
            )

            await query.message.reply_text(
                "Type another visitor's name, or /done to return to the review."
            )

        return

    elif action.startswith("ndept:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]

        name = session.get("newcomer_pending_name")

        if name:

            session["newcomer_pending_department"] = department

            await query.edit_message_text(
                f"Was {name} ({department}) Online or Onsite?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("💻 Online", callback_data="nsrc:Online"),
                        InlineKeyboardButton("🏛 Onsite", callback_data="nsrc:Onsite"),
                    ]
                ])
            )

        return

    elif action.startswith("nsrc:"):

        source = action.split(":", 1)[1]

        session = user_sessions[user_id]

        name = session.get("newcomer_pending_name")
        department = session.get("newcomer_pending_department")

        if name and department:

            session["newcomers"].append({
                "name": name,
                "department": department,
                "source": source,
            })

            session["newcomer_pending_name"] = None
            session["newcomer_pending_department"] = None

            await query.edit_message_text(
                f"✅ Newcomer added: {name} ({department}, {source})"
            )

            await query.message.reply_text(
                "Type another newcomer's name, or /done to return to the review."
            )

        return

    elif action == "submit":

        session = user_sessions[user_id]

        await query.message.reply_text(
            "Submitting attendance..."
        )
        try:

            response = await submit_attendance(session)

            if response.status_code == 200:

                del user_sessions[user_id]

                # Drop the buttons so the review card can't be
                # re-submitted, but keep the review text itself
                # visible in the chat instead of overwriting it.
                await query.edit_message_reply_markup(reply_markup=None)

                await query.message.reply_text(
                    "✅ Attendance successfully submitted."
                )

            else:

                await query.message.reply_text(

                    f"Submission failed.\n"
                    f"HTTP {response.status_code}"

                )

        except Exception as e:

            await query.message.reply_text(

                f"Submission failed.\n\n{e}"

            )

        return

    elif action == "cancel":

        del user_sessions[user_id]

        await query.edit_message_text(
            "❌ Attendance session cancelled."
        )

    elif action == "review":

        session = user_sessions[user_id]

        session["stage"] = STAGE_REVIEW
        session["visitor_pending_name"] = None
        session["visitor_pending_from"] = None
        session["newcomer_pending_name"] = None
        session["newcomer_pending_department"] = None

        await show_review_callback(query, session)

        return


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /skip — nobody attended onsite at all; moves straight to review.
    """

    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text("No active attendance session.")
        return

    session = user_sessions[user_id]

    if session["stage"] == STAGE_ONSITE:
        session["onsite_result"] = {"recognized": [], "unknown": []}
        session["stage"] = STAGE_REVIEW

        await update.message.reply_text(
            "🟡 Onsite attendance skipped — no onsite attendees recorded."
        )

        await show_review(update, context)
        return

    await update.message.reply_text("Nothing to skip right now.")


async def debug_any(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("UPDATE RECEIVED")
    print(update)


async def error_handler(update, context):
    print("EXCEPTION:", repr(context.error))
    import traceback
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)


print("=== BUILD 5 ===")
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("service", start))  # alias to bring up the menu again mid-conversation
app.add_handler(CommandHandler("predawn", predawn))
app.add_handler(CommandHandler("sunday", sunday))
app.add_handler(CommandHandler("wednesday", wednesday))
app.add_handler(CommandHandler("friday", friday))
app.add_handler(CommandHandler("retro", retro))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("skip", skip))

app.add_handler(
    MessageHandler(
        filters.ALL,
        debug_any,
    ),
    group=-1,
)

app.add_handler(
    MessageHandler(
        filters.PHOTO | filters.Document.IMAGE,
        receive_photo,
    )
)
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_text,
    )
)

app.add_handler(
    CallbackQueryHandler(button_handler)
)

app.add_error_handler(error_handler)

print("Attendance Bot V2 is running...")
app.run_polling()