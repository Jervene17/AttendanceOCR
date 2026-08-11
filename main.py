print("=" * 50)
print("ATTENDANCE OCR V2")
print("Commit: e1a89a9")
print("=" * 50)

import os
import asyncio
import functools

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
    USER_GROUP_MAP,
    ORGANIZER_IDS,
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
# USER_GROUP_MAP (Sunday checker -> department) comes from members.py,
# which re-exports it from config.py — the single source of truth.
retro_pending = {}

# Active checker report-in-progress, keyed by checker's user_id:
# { "organizer_id": <int>, "group": <str>, "images": [...], "text_names": [...] }
checker_sessions = {}

# =====================================================
# Session Stages
# =====================================================

STAGE_ONLINE = "online"
STAGE_ONSITE = "onsite"
STAGE_WAITING_CHECKERS = "waiting_checkers"
STAGE_REVIEW = "review"

STAGE_VISITOR = "visitor"
STAGE_NEWCOMER = "newcomer"

# Standing service options shown on the selection menu.
SERVICE_OPTIONS = ["Predawn", "Sunday", "Wednesday", "Friday"]

def is_organizer(user_id):
    return user_id in ORGANIZER_IDS

async def send_service_menu(message, user_id):

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"svc:{name}")]
        for name in SERVICE_OPTIONS
    ]

    keyboard.append(
        [InlineKeyboardButton("✨ Special Service/Event", callback_data="svc:special")]
    )

    if is_organizer(user_id):
        keyboard.append(
            [InlineKeyboardButton("🕒 Retro Submission", callback_data="retro_menu")]
        )

    await message.reply_text(
        "Attendance Bot V2 is ready.\n\n"
        "Select a service:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_service_menu(update.message, update.effective_user.id)

async def retro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_organizer(user_id):
        await update.message.reply_text(
            "🚫 Retro submissions are limited to organizers."
        )
        return

    await update.message.reply_text(
        "🕒 Retro Submission — select the service:",
        reply_markup=build_service_keyboard("rsvc"),
    )
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
        "newcomer_pending_name": None,

        # Department verification
        "current_department": None,

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


async def send_service_menu(message):

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
    await send_service_menu(update.message)


async def retro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕒 Retro Submission — select the service:",
        reply_markup=build_service_keyboard("rsvc"),
    )


# Kept as direct shortcuts so existing habits/automation still work,
# in addition to the new inline-keyboard menu.
async def start_service(update, context, service):
    user_id = update.effective_user.id
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

    if user_id in checker_sessions:
        await receive_checker_photo(update, context)
        return

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


async def receive_checker_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    checker = checker_sessions[user_id]

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

    checker["images"].append(filename)

    await update.message.reply_text(
        f"✅ Screenshot saved for {checker['group']}.\n"
        f"Total: {len(checker['images'])}\n\n"
        "Upload another image, type names, or type /done."
    )


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    text = update.message.text

    if not text:
        return

    # Sunday department checker typing names for their group.
    if user_id in checker_sessions:

        checker = checker_sessions[user_id]

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        checker["text_names"].extend(lines)

        await update.message.reply_text(
            f"✅ Added {len(lines)} name(s) for {checker['group']}.\n"
            f"Total from text: {len(checker['text_names'])}\n\n"
            "Send more names, upload screenshots, or type /done."
        )
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
    session = user_sessions[user_id]

    # -----------------------------
    # VISITOR NAME / "FROM" ENTRY
    # -----------------------------
    if session["stage"] == STAGE_VISITOR:

        name = text.strip()

        if not name:
            return

        if session.get("visitor_pending_name") is None:

            session["visitor_pending_name"] = name

            await update.message.reply_text(
                f"The visitor \"{name}\" is from?"
            )

        else:

            pending_name = session["visitor_pending_name"]

            session["visitors"].append({
                "name": pending_name,
                "from": name,
            })

            session["visitor_pending_name"] = None

            await update.message.reply_text(
                f"✅ Visitor added: {pending_name} (from {name})\n\n"
                "Type another visitor's name, or /done to return to the review."
            )

        return

    # -----------------------------
    # NEWCOMER NAME ENTRY
    # -----------------------------
    if session["stage"] == STAGE_NEWCOMER:

        if session.get("newcomer_pending_name") is not None:

            await update.message.reply_text(
                "Please choose a department using the buttons above, "
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

    # Sunday department checker submitting their group's report.
    if user_id in checker_sessions:
        await handle_checker_done(update, context)
        return

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

        # -----------------------------
        # SUNDAY: hand off onsite attendance to department checkers
        # -----------------------------
        if session["service"] == "Sunday":

            session["stage"] = STAGE_WAITING_CHECKERS

            await notify_checkers(context, user_id, session)

            pending_groups = sorted(
                USER_GROUP_MAP[c] for c in session["checkers_pending"]
            )

            msg_lines = [
                "✅ Online attendance completed.",
                "",
                "Onsite attendance will be collected from department checkers:",
            ]
            msg_lines += [f"• {g}" for g in pending_groups]

            if session.get("checkers_failed"):
                failed_groups = sorted(
                    USER_GROUP_MAP[c] for c in session["checkers_failed"]
                )
                msg_lines.append("")
                msg_lines.append(
                    "⚠️ Could not reach: " + ", ".join(failed_groups)
                    + " (they may need to message the bot first)."
                )

            msg_lines.append("")
            msg_lines.append(
                "You'll be notified as each department reports. "
                "Type /done anytime to view the review with whatever "
                "has been reported so far."
            )

            await update.message.reply_text("\n".join(msg_lines))

            return

        # -----------------------------
        # ALL OTHER SERVICES: organizer uploads onsite directly
        # -----------------------------
        session["stage"] = STAGE_ONSITE

        await update.message.reply_text(

            "✅ Online attendance completed.\n\n"

            "Now upload ONSITE screenshots, or type/paste names "

            "(one per line) directly in chat.\n\n"

            "When finished, type /done."

        )

        return

    # -----------------------------
        # SUNDAY (live only): hand off onsite attendance to department checkers
        # -----------------------------
        if session["service"] == "Sunday" and not session["is_retro"]:

            session["stage"] = STAGE_WAITING_CHECKERS

            await notify_checkers(context, user_id, session)

            pending_groups = sorted(
                USER_GROUP_MAP[c] for c in session["checkers_pending"]
            )

            msg_lines = [
                "✅ Online attendance completed.",
                "",
                "Onsite attendance will be collected from department checkers:",
            ]
            msg_lines += [f"• {g}" for g in pending_groups]

            if session.get("checkers_failed"):
                failed_groups = sorted(
                    USER_GROUP_MAP[c] for c in session["checkers_failed"]
                )
                msg_lines.append("")
                msg_lines.append(
                    "⚠️ Could not reach: " + ", ".join(failed_groups)
                    + " (they may need to message the bot first)."
                )

            msg_lines.append("")
            msg_lines.append(
                "You'll be notified as each department reports. "
                "Type /done anytime to view the review with whatever "
                "has been reported so far."
            )

            await update.message.reply_text("\n".join(msg_lines))

            return

        # -----------------------------
        # ALL OTHER SERVICES, and Sunday RETRO: organizer uploads
        # onsite directly (no checker DMs for retro submissions)
        # -----------------------------
        session["stage"] = STAGE_ONSITE

        await update.message.reply_text(

            "✅ Online attendance completed.\n\n"

            "Now upload ONSITE screenshots, or type/paste names "

            "(one per line) directly in chat.\n\n"

            "When finished, type /done."

        )

        return

    # -----------------------------
    # SUNDAY: organizer forcing the review early, whether or not
    # every checker has reported yet
    # -----------------------------
    if session["stage"] == STAGE_WAITING_CHECKERS:

        await finalize_sunday_onsite(
            update.message.reply_text,
            session,
            forced=True,
        )

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

        session["stage"] = STAGE_REVIEW

        await show_review(update, context)

        return

    # -----------------------------
    # VISITOR / NEWCOMER ENTRY DONE
    # -----------------------------
    if session["stage"] in (STAGE_VISITOR, STAGE_NEWCOMER):

        session["stage"] = STAGE_REVIEW
        session["visitor_pending_name"] = None
        session["newcomer_pending_name"] = None

        await show_review(update, context)

        return


# =====================================================
# Sunday: Department Checker Flow
# =====================================================

async def notify_checkers(context, organizer_id, session):
    """
    DMs every checker in USER_GROUP_MAP asking them to report onsite
    attendance for their group, and opens a checker_sessions entry
    for each so their next photo/text/done is routed here instead
    of treated as a normal message.
    """

    session["checkers_pending"] = set()
    session["checkers_done"] = set()
    session["checkers_failed"] = set()

    for checker_id, group in USER_GROUP_MAP.items():

        checker_sessions[checker_id] = {
            "organizer_id": organizer_id,
            "group": group,
            "images": [],
            "text_names": [],
        }

        try:
            await context.bot.send_message(
                chat_id=checker_id,
                text=(
                    f"📋 {session['service']} Attendance — {session['service_date']}\n\n"
                    f"Please report ONSITE attendance for {group}.\n\n"
                    "Upload screenshots and/or type names (one per line).\n\n"
                    "When finished, type /done.\n"
                    f"If nobody from {group} attended onsite, type /skip."
                ),
            )
            session["checkers_pending"].add(checker_id)

        except Exception as e:
            print(f"Failed to notify checker {checker_id} ({group}):", repr(e))
            session["checkers_failed"].add(checker_id)
            checker_sessions.pop(checker_id, None)


async def handle_checker_done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    checker = checker_sessions.get(user_id)

    if not checker:
        await update.message.reply_text("No active report to submit.")
        return

    group = checker["group"]
    images = checker["images"]
    text_names = checker["text_names"]

    if not images and not text_names:
        await update.message.reply_text(
            f"No screenshots or names received yet for {group}.\n\n"
            f"Upload a screenshot or type names, or type /skip if "
            f"nobody from {group} attended onsite."
        )
        return

    await update.message.reply_text(f"Processing {group} attendance...")

    results_to_merge = []

    if images:
        image_result = await asyncio.to_thread(recognize_multiple_images, images)
        results_to_merge.append(image_result)

    if text_names:
        text_result = recognize_text_names(text_names)
        results_to_merge.append(text_result)

    result = merge_results(*results_to_merge)

    await finish_checker_report(update, context, user_id, checker, result)


async def finish_checker_report(update, context, checker_id, checker, result):
    """
    Merges a checker's OCR/text result into their organizer's
    session, marks the checker as done, and — once every checker has
    reported — auto-finalizes the onsite stage for the organizer.
    """

    organizer_id = checker["organizer_id"]
    group = checker["group"]
    session = user_sessions.get(organizer_id)

    checker_sessions.pop(checker_id, None)

    if not session:
        await update.message.reply_text(
            "The attendance session this was for is no longer active. "
            "Your report was not saved."
        )
        return

    update_master_attendance(session, result, "onsite")
    reported_count = len(result["recognized"])

    session.setdefault("checkers_pending", set()).discard(checker_id)
    session.setdefault("checkers_done", set()).add(checker_id)

    await update.message.reply_text(
        f"✅ {group} attendance submitted ({reported_count}). Thank you!"
    )

    organizer_notify = functools.partial(context.bot.send_message, chat_id=organizer_id)

    remaining = sorted(
        USER_GROUP_MAP[c] for c in session.get("checkers_pending", set())
    )

    if remaining:
        await organizer_notify(
            text=(
                f"✅ {group} reported onsite attendance.\n"
                f"⏳ Still waiting on: {', '.join(remaining)}"
            )
        )

    else:
        await organizer_notify(text=f"✅ {group} reported onsite attendance.")

        # Every checker has reported — automatically move the
        # organizer's session into the review stage.
        await finalize_sunday_onsite(organizer_notify, session)


async def finalize_sunday_onsite(reply_func, session, forced=False):
    """
    Closes out the checker-collection stage and shows the organizer
    the onsite verification summary + the review card. reply_func
    must accept (text, reply_markup=None) — either
    update.message.reply_text or a functools.partial of
    context.bot.send_message with chat_id already bound.
    """

    session["stage"] = STAGE_REVIEW

    text = "🟡 ONSITE — Verification (from department checkers)\n\n" + onsite_summary_text(session)

    if forced:
        pending_groups = sorted(
            USER_GROUP_MAP[c] for c in session.get("checkers_pending", set())
        )
        if pending_groups:
            text += "\n\n⚠️ Not yet reported: " + ", ".join(pending_groups)

    await reply_func(text=text)

    await reply_func(
        text=render_review_text(session),
        reply_markup=build_review_keyboard(session)
    )


def onsite_summary_text(session):

    names = sorted(session["onsite_members"])

    lines = [f"Identified onsite: {len(names)}"]

    for name in names:
        lines.append(f"• {name}")

    if session["unknown"]:
        lines.append("")
        lines.append("❓ Unknown / Unmatched Names")

        for name in sorted(session["unknown"]):
            lines.append(f"• {name}")

    return "\n".join(lines)


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

    for department, members in MEMBER_LISTS.items():

        if name in members:

            return {
                "name": name,
                "department": department,
                "type": "Member"
            }

    return None


async def show_review(update, context):

    user_id = update.effective_user.id
    session = user_sessions[user_id]

    await update.message.reply_text(
        render_review_text(session),
        reply_markup=build_review_keyboard(session)
    )


def render_review_text(session):

    recognized = session["recognized"]

    lines = []

    lines.append(f"📊 {session['service']} Attendance Review")
    lines.append("")

    total_expected = 0
    total_present = 0

    for department, members in MEMBER_LISTS.items():

        expected = len(members)

        present = sum(
            1
            for member in members
            if member in recognized
        )

        total_expected += expected
        total_present += present

        if present == expected:
            icon = "🟢"
        elif present == 0:
            icon = "🔴"
        else:
            icon = "🟡"

        lines.append(
            f"{icon} {department}: {present}/{expected}"
        )

        missing = [
            member_name
            for member_name in members
            if member_name not in recognized
        ]

        if missing:
            for member in missing:
                lines.append(f"   • {member}")

    lines.append("")
    lines.append(f"👥 Total Present: {total_present}/{total_expected}")

    pending_checkers = session.get("checkers_pending")

    if pending_checkers:
        pending_groups = sorted(USER_GROUP_MAP[c] for c in pending_checkers)
        lines.append("")
        lines.append("⏳ Awaiting onsite report from: " + ", ".join(pending_groups))

    if session["unknown"]:
        lines.append("")
        lines.append("❓ Unknown Names")

        for name in sorted(session["unknown"]):
            lines.append(f"• {name}")

    if session["visitors"]:
        lines.append("")
        lines.append("👥 Visitors")

        for visitor in session["visitors"]:
            lines.append(f"• {visitor['name']} (from {visitor['from']})")

    if session["newcomers"]:
        lines.append("")
        lines.append("🌱 Newcomers")

        for newcomer in session["newcomers"]:
            lines.append(f"• {newcomer['name']} ({newcomer['department']})")

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

    recognized = session["recognized"]

    keyboard = []

    lines = []

    lines.append(f"📋 {department}")
    lines.append("")

    members = MEMBER_LISTS[department]

    present = 0

    for member in members:

        if member in recognized:

            present += 1

            lines.append(f"✅ {member}")

        else:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"➕ {member}",
                        callback_data=f"present:{member}"
                    )
                ]
            )

    lines.append("")
    lines.append(
        f"Present: {present}/{len(members)}"
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

    keyboard = []

    for department in MEMBER_LISTS:
        keyboard.append(
            [InlineKeyboardButton(department, callback_data=f"adept:{department}")]
        )

    keyboard.append(
        [InlineKeyboardButton("⬅ Back", callback_data="resolve")]
    )

    text = session.get("resolving_text", "")

    await query.edit_message_text(
        f"Resolving: \"{text}\"\n\nChoose their department:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_resolve_members(query, session, department):

    keyboard = []

    for member in MEMBER_LISTS[department]:
        keyboard.append(
            [InlineKeyboardButton(member, callback_data=f"aassign:{member}")]
        )

    keyboard.append(
        [InlineKeyboardButton("⬅ Departments", callback_data="resolve")]
    )

    text = session.get("resolving_text", "")

    await query.edit_message_text(
        f"Resolving: \"{text}\"\n\n{department} — who is this?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_review_callback(query, session):

    await query.edit_message_text(
        render_review_text(session),
        reply_markup=build_review_keyboard(session)
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

    payload = {

        "service": session["service"],

        "service_date": session["service_date"],

        "members": members,

        "visitors": session["visitors"],

        "newcomers": session["newcomers"],

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

    if action == "retro_menu":

        if not is_organizer(user_id):
            await query.edit_message_text(
                "🚫 Retro submissions are limited to organizers."
            )
            return

        await query.edit_message_text(
            "🕒 Retro Submission — select the service:",
            reply_markup=build_service_keyboard("rsvc"),
        )
        return

    if action.startswith("rsvc:"):

        if not is_organizer(user_id):
            await query.edit_message_text(
                "🚫 Retro submissions are limited to organizers."
            )
            return

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

        await show_resolve_departments(query, session)

        return

    elif action.startswith("adept:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]

        await show_resolve_members(query, session, department)

        return

    elif action.startswith("aassign:"):

        member = action.split(":", 1)[1]

        session = user_sessions[user_id]

        resolved_text = session.get("resolving_text")

        session["recognized"].add(member)

        if resolved_text:

            session["unknown"].discard(resolved_text)

            src = session["unknown_sources"].pop(resolved_text, None)

            # Onsite overrides online here too.
            if src in ("onsite", "both"):
                session["onsite_members"].add(member)
                session["online_members"].discard(member)

            elif src == "online":
                session["online_members"].add(member)

        session.pop("resolving_text", None)

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

        # Add member to attendance
        session["recognized"].add(member)

        # Remove from unknown if OCR had it there
        session["unknown"].discard(member)

        # Refresh department screen
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

        await query.message.reply_text(

            "Enter the visitor's name.\n\n"

            "When finished adding visitors, type /done."

        )

        return

    elif action == "newcomer":

        session = user_sessions[user_id]

        session["stage"] = STAGE_NEWCOMER
        session["newcomer_pending_name"] = None

        await query.message.reply_text(

            "Enter the newcomer's name.\n\n"

            "When finished adding newcomers, type /done."

        )

        return

    elif action.startswith("ndept:"):

        department = action.split(":", 1)[1]

        session = user_sessions[user_id]

        name = session.get("newcomer_pending_name")

        if name:

            session["newcomers"].append({
                "name": name,
                "department": department,
            })

            session["newcomer_pending_name"] = None

            await query.edit_message_text(
                f"✅ Newcomer added: {name} ({department})"
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

                await query.edit_message_text(

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
        session["newcomer_pending_name"] = None

        await show_review_callback(query, session)

        return


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /skip — for a Sunday checker: "nobody from my group attended
    onsite". For an organizer mid-onsite (non-Sunday): "nobody
    attended onsite at all", moves straight to review.
    """

    user_id = update.effective_user.id

    if user_id in checker_sessions:
        checker = checker_sessions[user_id]
        await finish_checker_report(
            update, context, user_id, checker,
            {"recognized": [], "unknown": []}
        )
        return

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


print("=== BUILD 3 ===")
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("service", start))  # alias to bring up the menu again mid-conversation
app.add_handler(CommandHandler("predawn", predawn))
app.add_handler(CommandHandler("sunday", sunday))
app.add_handler(CommandHandler("wednesday", wednesday))
app.add_handler(CommandHandler("friday", friday))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("skip", skip))
app.add_handler(CommandHandler("retro", retro))

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