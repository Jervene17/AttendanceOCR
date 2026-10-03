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
    WebAppInfo,
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
    find_member,
)
from cleaner import normalize_name
import sermon_portal

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

print("Bot token configured:", bool(BOT_TOKEN))
print("Attendance webhook configured:", bool(WEBHOOK_URL))


def parse_id_allowlist(variable_name, fallback_ids):
    """Read a comma-separated Telegram ID allowlist from the environment."""
    configured = os.getenv(variable_name, "").strip()
    if not configured:
        return set(fallback_ids)
    try:
        return {int(value.strip()) for value in configured.split(",") if value.strip()}
    except ValueError as exc:
        raise RuntimeError(
            f"{variable_name} must be a comma-separated list of Telegram numeric IDs."
        ) from exc


# Attendance controls and sermon administration are separate roles.
# If omitted, each setting preserves the current organizer allowlist.
ATTENDANCE_LOGGER_IDS = parse_id_allowlist("ATTENDANCE_LOGGER_IDS", ORGANIZER_IDS)
SERMON_ADMIN_IDS = parse_id_allowlist("SERMON_ADMIN_IDS", ORGANIZER_IDS)


user_sessions = {}

# Users who have selected "Special Service/Event" and are expected to
# type the name of that service/event as their next text message.
awaiting_special_service = set()

# Retro-submission flow, keyed by user_id:
# {"service": <str or None>, "awaiting": "name" | "date"}
retro_pending = {}

# =====================================================
# Catch Up logging
# =====================================================
# "Catch up" = a member listened to / watched a service recording
# after the fact, rather than attending it live.
#
# Deliberately built the same way retro submission is: pick a
# service, type the date, then (for catch up specifically) type the
# name(s) who caught up. No dependency on any in-memory record of a
# prior submission -- the sheet itself is the source of truth, so
# this keeps working across bot restarts, unlike an approach that
# required looking up a previously-submitted session.
#
# Keyed by user_id:
# {
#   "service": <str or None>,
#   "awaiting": "name" | "date" | "names",
#   "date": <"YYYY-MM-DD", set once the date step is done>,
#   "names": [<typed lines>],
# }
catchup_pending = {}

# =====================================================
# Pull Summary
# =====================================================
# Pulls the attendance summary for a given service + date directly
# from the Google Sheet (via a GET to the same WEBHOOK_URL), rather
# than from any in-memory session. This means it reflects manual
# edits made in the sheet after submission, and works even after a
# bot restart or for services submitted from a different device.
#
# Built the same way retro/catch-up are: pick a service, then type
# a date. Keyed by user_id:
# {"service": <str or None>, "awaiting": "name" | "date"}
summary_pending = {}

# =====================================================
# Correct Attendance
# =====================================================
# Same starting shape as Pull Summary (pick service, type date),
# but instead of just rendering the log, it's fetched into
# `entries` (each carrying its sheet `row`) so individual entries
# can be removed, and Member/Newcomer/Visitor entries that were
# missed can be added — all applied directly against the sheet via
# the webhook's "correction" entry_type, not against any
# in-memory session.
#
# Keyed by user_id:
# {
#   "service": <str or None>,
#   "awaiting": "name" | "date" | "menu"
#             | "add_member_name" | "add_member_source"
#             | "add_newcomer" (sub-steps use newcomer_pending_* keys)
#             | "add_visitor_name" | "add_visitor_from" | "add_visitor_source",
#   "date": <"YYYY-MM-DD", set once the date step is done>,
#   "entries": [{"row": int, "department": str, "name": str,
#                "source": str, "type": str}, ...],
#   "page": <int, 0-based index of the currently displayed page
#            of entries>,
# }
correction_pending = {}

# Message-library registration and organizer PDF upload flows.
signup_waiting = set()
sermon_upload_waiting = set()
roster_match_waiting = {}
portal_attendance_cache = {}
portal_attendance_lock = asyncio.Lock()

# How many logged entries are shown per page in the Correct
# Attendance menu -- keeps the inline keyboard well under Telegram's
# button limit even for a service/date with 50+ entries.
CORRECTION_PAGE_SIZE = 20

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
    Attendance recording and attendance-management commands are
    limited to ATTENDANCE_LOGGER_IDS (Railway environment variable).
    """
    return user_id in ATTENDANCE_LOGGER_IDS


def is_sermon_admin(user_id):
    return user_id in SERMON_ADMIN_IDS


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


async def require_sermon_admin(reply_func, user_id):
    if is_sermon_admin(user_id):
        return True
    await reply_func("🚫 Sermon uploads and message-access approvals are limited to sermon administrators.")
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
        "newcomer_names": None,
        "newcomer_names_by_church": None,

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
        "/done\n\n"
        "If nobody attended online, type /skip."
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

    keyboard.append(
        [InlineKeyboardButton("🎧 Log Catch Up", callback_data="catchup_menu")]
    )

    keyboard.append(
        [InlineKeyboardButton("📊 Pull Summary", callback_data="summary_menu")]
    )

    keyboard.append(
        [InlineKeyboardButton("✏️ Correct Attendance", callback_data="correct_menu")]
    )

    keyboard.append(
        [InlineKeyboardButton("📚 Sermon messages", web_app=WebAppInfo(url=f"{PUBLIC_BASE_URL}/app"))]
        if PUBLIC_BASE_URL else
        [InlineKeyboardButton("📚 Sermon messages", callback_data="message_portal_unconfigured")]
    )
    keyboard.append(
        [InlineKeyboardButton("🔗 Sign up for message access through Telegram", callback_data="message_signup")]
    )

    if is_sermon_admin(user_id):
        keyboard.extend(sermon_admin_buttons())

    await message.reply_text(
        "Attendance Bot V2 is ready.\n\n"
        "Select a service:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if update.effective_chat.type != "private":
        await update.message.reply_text("Please open a private chat with the bot to sign up or read messages.")
        return

    if not is_organizer(user_id):
        await send_member_menu(update.message, user_id)
        return

    if not await require_organizer(update.message.reply_text, user_id):
        return

    # Recovery valve: hitting /start clears any stuck catch-up entry
    # flow for this user, same idea as an attendance session simply
    # getting overwritten by a fresh begin_session() call.
    catchup_pending.pop(user_id, None)
    summary_pending.pop(user_id, None)
    correction_pending.pop(user_id, None)

    await send_service_menu(update.message, user_id)


async def send_member_menu(message, user_id):
    link = sermon_portal.get_link_for_user(user_id)
    if link and link["status"] == "approved":
        account_status = f"Linked as {link['member_name']}."
    elif link and link["status"] == "pending":
        account_status = f"Your request to link as {link['member_name']} is waiting for an organizer."
    else:
        account_status = "Link your Telegram account once; an organizer will confirm the roster match."

    keyboard = [[InlineKeyboardButton(
        "🔗 Sign up for message access through Telegram", callback_data="message_signup"
    )]]
    if PUBLIC_BASE_URL:
        keyboard.append([InlineKeyboardButton(
            "📚 Open sermon messages", web_app=WebAppInfo(url=f"{PUBLIC_BASE_URL}/app")
        )])
    if is_sermon_admin(user_id):
        keyboard.extend(sermon_admin_buttons())

    text = f"Sermon message access\n\n{account_status}"
    if not PUBLIC_BASE_URL:
        text += "\n\nThe reading library will appear here after its secure web address is configured."
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


def sermon_admin_buttons():
    """Buttons shown only to users in SERMON_ADMIN_IDS."""
    return [
        [InlineKeyboardButton("📤 Upload sermon PDF", callback_data="sermon:upload")],
        [InlineKeyboardButton("👥 Review message sign-ups", callback_data="sermon:signups")],
    ]


async def service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_organizer(update.message.reply_text, user_id):
        return
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please use /service in a private chat with the bot.")
        return
    await send_service_menu(update.message, user_id)


async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please message me privately to sign up.")
        return
    user_id = update.effective_user.id
    existing = sermon_portal.get_link_for_user(user_id)
    if existing and existing["status"] == "approved":
        await update.message.reply_text(f"Your account is already linked as {existing['member_name']}.")
        return
    if existing and existing["status"] == "pending":
        await update.message.reply_text(f"Your request for {existing['member_name']} is waiting for organizer approval.")
        return
    signup_waiting.add(user_id)
    await update.message.reply_text(
        "Sign up for message access through Telegram\n\n"
        "Type the name you use. If it does not match the roster exactly, an organizer will match it before approving access."
    )


async def upload_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_sermon_admin(update.message.reply_text, user_id):
        return
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please upload sermon PDFs in a private chat with the bot.")
        return
    await begin_sermon_upload(update.message.reply_text, user_id)


async def begin_sermon_upload(reply_text, user_id):
    sermon_upload_waiting.add(user_id)
    await reply_text(
        "Upload the sermon PDF as a document. Put this in its caption:\n"
        "Sunday | YYYY-MM-DD\n"
        "or\n"
        "Wednesday | YYYY-MM-DD\n\n"
        "The library needs an unlocked PDF so readers do not get a password prompt. "
        "Open the protected source with its current password and save an unlocked copy before uploading."
    )


async def message_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_sermon_admin(update.message.reply_text, user_id):
        return
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please review sign-ups in a private chat with the bot.")
        return
    await send_pending_link_requests(update.message.reply_text)


async def send_pending_link_requests(reply_text):
    requests_to_review = sermon_portal.pending_link_requests()
    if not requests_to_review:
        await reply_text("There are no message-access sign-ups waiting for approval.")
        return
    await reply_text(
        f"Message-access sign-ups waiting for review: {len(requests_to_review)}"
    )
    for request in requests_to_review:
        if request["member_id"] == sermon_portal.UNMATCHED_MEMBER_ID:
            keyboard = [[
                InlineKeyboardButton("🔎 Match to roster", callback_data=f"msgacc:match:{request['telegram_id']}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"msgacc:d:{request['telegram_id']}"),
            ]]
            request_note = "Name needs manual roster matching"
        else:
            keyboard = [[
                InlineKeyboardButton("✅ Approve", callback_data=f"msgacc:a:{request['telegram_id']}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"msgacc:d:{request['telegram_id']}"),
            ]]
            request_note = "Matched roster entry"
        await reply_text(
            f"{request_note}: {request['member_name']}\n"
            f"Telegram account ID: {request['telegram_id']}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def retro(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await require_organizer(update.message.reply_text, user_id):
        return

    await update.message.reply_text(
        "🕒 Retro Submission — select the service:",
        reply_markup=build_service_keyboard("rsvc"),
    )


async def catchup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /catchup — same entry point as the "🎧 Log Catch Up" menu button,
    for people who prefer typing the command directly. Mirrors
    /retro's shape: pick a service, then type a date.
    """

    user_id = update.effective_user.id

    if not await require_organizer(update.message.reply_text, user_id):
        return

    if user_id in user_sessions:
        await update.message.reply_text(
            "Please finish or /done your current attendance session first, "
            "then try /catchup again."
        )
        return

    await update.message.reply_text(
        "🎧 Catch Up — select the service:",
        reply_markup=build_service_keyboard("csvc"),
    )


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /summary — same entry point as the "📊 Pull Summary" menu button,
    for people who prefer typing the command directly. Mirrors
    /retro's shape: pick a service, then type a date. Pulls straight
    from the Google Sheet, so it reflects any edits made there since
    the original submission.
    """

    user_id = update.effective_user.id

    if not await require_organizer(update.message.reply_text, user_id):
        return

    await update.message.reply_text(
        "📊 Pull Summary — select the service:",
        reply_markup=build_service_keyboard("sumsvc"),
    )


async def correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /correct — same entry point as the "✏️ Correct Attendance" menu
    button. Mirrors /summary's shape: pick a service, then type a
    date, then act on the entries pulled live from the sheet.
    """
    user_id = update.effective_user.id
    if not await require_organizer(update.message.reply_text, user_id):
        return
    await update.message.reply_text(
        "✏️ Correct Attendance — select the service:",
        reply_markup=build_service_keyboard("corsvc"),
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


async def receive_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    document = update.message.document
    if user_id not in sermon_upload_waiting:
        if is_organizer(user_id):
            await update.message.reply_text("Use /upload_message before uploading a sermon PDF.")
        return
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please upload the sermon PDF in a private chat with the bot.")
        return
    file_name = (document.file_name or "").lower()
    mime_type = (document.mime_type or "").lower()
    if not file_name.endswith(".pdf") and mime_type != "application/pdf":
        await update.message.reply_text("Please upload a PDF document.")
        return
    if document.file_size and document.file_size > sermon_portal.MAX_PDF_BYTES:
        await update.message.reply_text("This file is over the 10 MB limit.")
        return
    parts = [part.strip() for part in (update.message.caption or "").split("|", 1)]
    if len(parts) != 2:
        await update.message.reply_text(
            "Add this caption and resend the PDF:\nSunday | YYYY-MM-DD\n"
            "or Wednesday | YYYY-MM-DD"
        )
        return
    service, service_date = parts
    if service.title() not in ("Sunday", "Wednesday"):
        await update.message.reply_text("Service must be Sunday or Wednesday.")
        return
    try:
        datetime.strptime(service_date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("Use a service date in YYYY-MM-DD format.")
        return
    title = f"{service.title()} Message"

    sermon_portal.initialize_storage()
    temporary = sermon_portal.store_directory() / f"upload-{uuid.uuid4().hex}.pdf"
    try:
        telegram_file = await document.get_file()
        await telegram_file.download_to_drive(custom_path=str(temporary))
        with temporary.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("The uploaded file does not look like a valid PDF.")
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(temporary), strict=False)
            if reader.is_encrypted:
                raise ValueError(
                    "This PDF is password-protected. Open the original using its current password, "
                    "save an unlocked copy, then upload that copy so members will not see a password prompt."
                )
        except ImportError:
            raise RuntimeError("PDF validation is unavailable; install the pypdf dependency and redeploy.")
        sermon = sermon_portal.save_sermon(
            temporary, service, service_date, title, uploaded_by=user_id
        )
        sermon_upload_waiting.discard(user_id)
        await update.message.reply_text(
            f"✅ Saved {sermon['service']} message for {sermon['service_date']}.\n"
            "Members who attended that service can read it from the sermon library."
        )
    except ValueError as exc:
        temporary.unlink(missing_ok=True)
        await update.message.reply_text(f"Could not save this sermon: {exc}")
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        print("Sermon upload error:", type(exc).__name__)
        await update.message.reply_text("Could not save the sermon PDF. Please check the file and try again.")


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    text = update.message.text

    if not text:
        return

    # An administrator can search the roster after opening an unmatched signup.
    if user_id in roster_match_waiting:
        if not is_sermon_admin(user_id):
            roster_match_waiting.pop(user_id, None)
            await update.message.reply_text("Roster matching is limited to sermon administrators.")
            return
        requested_id = roster_match_waiting.pop(user_id)
        search = normalize_name(text)
        if not search:
            await update.message.reply_text("Type part of a roster name to search.")
            roster_match_waiting[user_id] = requested_id
            return
        candidates = []
        for member_id, member in MEMBERS.items():
            names = [member.get("display_name"), member.get("official_name")]
            names.extend(member.get("aliases", []))
            normalized_names = [normalize_name(name) for name in names if name]
            if any(search in name for name in normalized_names):
                display_name = member.get("display_name") or member.get("official_name") or member_id
                candidates.append((member_id, display_name, member))
        if not candidates:
            await update.message.reply_text(
                "No roster names matched that search. Tap Match to roster again and try another name."
            )
            return
        if len(candidates) > 20:
            await update.message.reply_text(
                f"That search matched {len(candidates)} roster entries. Type a more specific name."
            )
            roster_match_waiting[user_id] = requested_id
            return
        buttons = []
        for member_id, display_name, member in candidates:
            department = member.get("department", "")
            label = f"{display_name} · {member_id}"
            if department:
                label += f" · {department}"
            buttons.append([InlineKeyboardButton(
                label[:64], callback_data=f"msgacc:link:{requested_id}:{member_id}"
            )])
        await update.message.reply_text(
            f"Choose the roster entry for Telegram account {requested_id}:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # New member registration is handled before the attendance text flows.
    if user_id in signup_waiting:
        signup_waiting.discard(user_id)
        requested = normalize_name(text)
        matches = {}
        for member_id, member in MEMBERS.items():
            names = [member.get("display_name"), member.get("official_name")]
            names.extend(member.get("aliases", []))
            if any(normalize_name(name) == requested for name in names if name):
                matches[member_id] = member
        if not requested:
            await update.message.reply_text("Please type the name you use on the member roster.")
            signup_waiting.add(user_id)
            return
        if len(matches) == 1:
            member_id, member = next(iter(matches.items()))
            member_name = member.get("display_name") or member.get("official_name")
        else:
            member_id = sermon_portal.UNMATCHED_MEMBER_ID
            member_name = text.strip()
        result, stored_name = sermon_portal.submit_link_request(user_id, member_id, member_name)
        if result == "already_approved":
            await update.message.reply_text(f"Your Telegram account is already linked as {stored_name}.")
            return
        if result == "already_pending":
            await update.message.reply_text(f"Your request for {stored_name} is already waiting for approval.")
            return
        if member_id == sermon_portal.UNMATCHED_MEMBER_ID:
            confirmation = (
                f"Sign-up request submitted with the name '{member_name}'. An organizer will match it "
                "to the roster and approve it before you can read messages."
            )
            notice = f"New message-access signup needs roster matching: {member_name} (Telegram account {user_id}). Review with /message_access."
        else:
            confirmation = (
                f"Sign-up request submitted for {member_name}. An organizer must approve it before you can read messages."
            )
            notice = f"New message-access sign-up: {member_name} (Telegram account {user_id}). Review with /message_access."
        await update.message.reply_text(confirmation)
        for organizer_id in SERMON_ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=organizer_id,
                    text=notice,
                )
            except Exception as exc:
                print("Could not notify message-access organizer:", type(exc).__name__)
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

        # Catch Up flow: same idea -- still need a date before the
        # name-collection step.
        if user_id in catchup_pending and catchup_pending[user_id].get("awaiting") == "name":
            catchup_pending[user_id]["service"] = service_name
            catchup_pending[user_id]["awaiting"] = "date"

            await update.message.reply_text(
                f"🎧 Catch Up: {service_name}\n\n"
                "Please type the date this catch up is for (YYYY-MM-DD):"
            )
            return

        # Pull Summary flow: same idea -- still need a date before
        # fetching from the sheet.
        if user_id in summary_pending and summary_pending[user_id].get("awaiting") == "name":
            summary_pending[user_id]["service"] = service_name
            summary_pending[user_id]["awaiting"] = "date"

            await update.message.reply_text(
                f"📊 Summary: {service_name}\n\n"
                "Please type the date to pull (YYYY-MM-DD):"
            )
            return

        # Correction flow: still need a date before pulling entries.
        if user_id in correction_pending and correction_pending[user_id].get("awaiting") == "name":
            correction_pending[user_id]["service"] = service_name
            correction_pending[user_id]["awaiting"] = "date"
            await update.message.reply_text(
                f"✏️ Correct: {service_name}\n\n"
                "Please type the date to correct (YYYY-MM-DD):"
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

    # -----------------------------
    # CATCH UP: user is typing the date
    # -----------------------------
    if user_id in catchup_pending and catchup_pending[user_id].get("awaiting") == "date":

        date_text = text.strip()

        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid date in YYYY-MM-DD format (e.g. 2026-08-09)."
            )
            return

        catchup_pending[user_id]["date"] = parsed_date.strftime("%Y-%m-%d")
        catchup_pending[user_id]["awaiting"] = "names"
        catchup_pending[user_id]["names"] = []

        await update.message.reply_text(
            f"🎧 Catch Up: {catchup_pending[user_id]['service']} — "
            f"{catchup_pending[user_id]['date']}\n\n"
            "Type the name(s) of who caught up (one per line).\n\n"
            "When finished, type /done."
        )
        return

    # -----------------------------
    # CATCH UP: collecting typed names
    # -----------------------------
    if user_id in catchup_pending and catchup_pending[user_id].get("awaiting") == "names":

        typed = text.strip()

        if not typed:
            return

        lines = [line.strip() for line in typed.split("\n") if line.strip()]

        catchup_pending[user_id].setdefault("names", []).extend(lines)

        service = catchup_pending[user_id].get("service", "")
        date = catchup_pending[user_id].get("date", "")

        await update.message.reply_text(
            f"✅ Added {len(lines)} name(s) for catch up on {service} — {date}.\n"
            f"Total: {len(catchup_pending[user_id]['names'])}\n\n"
            "Send more names, or type /done."
        )
        return

    # -----------------------------
    # PULL SUMMARY: user is typing the date to fetch
    # -----------------------------
    if user_id in summary_pending and summary_pending[user_id].get("awaiting") == "date":

        date_text = text.strip()

        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid date in YYYY-MM-DD format (e.g. 2026-08-09)."
            )
            return

        service = summary_pending.pop(user_id)["service"]
        service_date = parsed_date.strftime("%Y-%m-%d")

        await update.message.reply_text("📤 Pulling summary...")

        try:
            entries = await fetch_summary(service, service_date)
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ Couldn't reach the webhook.\n\n{e}"
            )
            return

        if entries is None:
            await update.message.reply_text(
                "⚠️ Webhook returned an unexpected response."
            )
            return

        await update.message.reply_text(
            render_summary_text(service, service_date, entries),
            parse_mode="HTML",
        )
        return

    # -----------------------------
    # CORRECTION: user is typing the date to pull for correcting
    # -----------------------------
    if user_id in correction_pending and correction_pending[user_id].get("awaiting") == "date":

        date_text = text.strip()

        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid date in YYYY-MM-DD format (e.g. 2026-08-09)."
            )
            return

        service = correction_pending[user_id]["service"]
        service_date = parsed_date.strftime("%Y-%m-%d")

        await update.message.reply_text("📤 Loading current log...")

        try:
            entries = await fetch_summary(service, service_date)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Couldn't reach the webhook.\n\n{e}")
            correction_pending.pop(user_id, None)
            return

        if entries is None:
            await update.message.reply_text("⚠️ Webhook returned an unexpected response.")
            correction_pending.pop(user_id, None)
            return

        correction_pending[user_id].update({
            "date": service_date,
            "awaiting": "menu",
            "entries": entries,
            "page": 0,
        })

        await send_correction_menu(update.message.reply_text, correction_pending[user_id])
        return

    # -----------------------------
    # CORRECTION: typing a member's name to add
    # -----------------------------
    if user_id in correction_pending and correction_pending[user_id].get("awaiting") == "add_member_name":

        typed = text.strip()

        if not typed:
            return

        member = find_member(typed)

        if not member:
            await update.message.reply_text(
                f"⚠️ \"{typed}\" wasn't found in the roster. Check the spelling and try again, "
                "or use ➕ Add Newcomer / ➕ Add Visitor if they're not a member."
            )
            return

        correction_pending[user_id]["pending_add"] = {
            "name": member["display_name"],
            "department": member["department"],
            "type": get_member_type(member),
        }
        correction_pending[user_id]["awaiting"] = "add_member_source"

        await update.message.reply_text(
            f"Was {member['display_name']} Online or Onsite?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💻 Online", callback_data="coraddsrc:Online"),
                    InlineKeyboardButton("🏛 Onsite", callback_data="coraddsrc:Onsite"),
                ]
            ])
        )
        return

    # -----------------------------
    # CORRECTION: typing a newcomer's name manually
    # (only reached via the "✏️ Other" button in the picker)
    # -----------------------------
    if (
        user_id in correction_pending
        and correction_pending[user_id].get("awaiting") == "add_newcomer"
        and correction_pending[user_id].get("newcomer_pending_name") is None
    ):

        name = text.strip()

        if not name:
            return

        correction_pending[user_id]["newcomer_pending_name"] = name

        await update.message.reply_text(
            f"Department for \"{name}\"?",
            reply_markup=build_department_picker("ndept")
        )
        return

    # -----------------------------
    # CORRECTION: typing a visitor's name / "from"
    # -----------------------------
    if user_id in correction_pending and correction_pending[user_id].get("awaiting") == "add_visitor_name":

        typed = text.strip()

        if not typed:
            return

        correction_pending[user_id]["pending_visitor_name"] = typed
        correction_pending[user_id]["awaiting"] = "add_visitor_from"

        await update.message.reply_text(f"The visitor \"{typed}\" is from?")
        return

    if user_id in correction_pending and correction_pending[user_id].get("awaiting") == "add_visitor_from":

        typed = text.strip()

        if not typed:
            return

        correction_pending[user_id]["pending_visitor_from"] = typed
        correction_pending[user_id]["awaiting"] = "add_visitor_source"

        await update.message.reply_text(
            f"Was {correction_pending[user_id]['pending_visitor_name']} Online or Onsite?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💻 Online", callback_data="coraddvsrc:Online"),
                    InlineKeyboardButton("🏛 Onsite", callback_data="coraddvsrc:Onsite"),
                ]
            ])
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

    if user_id in catchup_pending:
        await finish_catchup(update, context, user_id)
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
# Catch Up logging
# =====================================================

async def finish_catchup(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):

    pending = catchup_pending.get(user_id)

    if not pending:
        await update.message.reply_text("No catch up in progress.")
        return

    if pending.get("awaiting") != "names":
        await update.message.reply_text(
            "Please finish selecting the service and date first."
        )
        return

    names = pending.get("names", [])

    if not names:
        await update.message.reply_text(
            "Please type at least one name before /done, or /start to cancel."
        )
        return

    service = pending["service"]
    service_date = pending["date"]

    # Match typed names against the member roster the same way
    # onsite typed names are matched -- recognized ones get the
    # member's proper display name + department/type looked up,
    # unmatched ones are kept as-is and flagged.
    result = recognize_text_names(names)

    entries = []

    for member in result["recognized"]:
        info = get_member_info(member["display_name"])
        entries.append({
            "name": member["display_name"],
            "matched": True,
            "department": info["department"] if info else "",
            "type": info["type"] if info else "Member",
        })

    for text in result["unknown"]:
        entries.append({
            "name": text,
            "matched": False,
            "department": "",
            "type": "Unrecognized",
        })

    await update.message.reply_text("📤 Logging catch up...")

    try:
        response = await submit_catchup(service, service_date, entries)

        body_status = None
        body_message = None

        try:
            body = response.json()
            body_status = body.get("status")
            body_message = body.get("message")
        except ValueError:
            pass

        if response.status_code == 200 and body_status == "success":
            await update.message.reply_text("✅ Catch up logged.")

        elif response.status_code == 200 and body_status == "error":
            await update.message.reply_text(
                "⚠️ Webhook reported an error: "
                f"{body_message or 'unknown error'}"
            )

        else:
            await update.message.reply_text(
                f"⚠️ Webhook returned HTTP {response.status_code}."
            )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Couldn't reach the webhook.\n\n{e}"
        )

    # Simple confirmation of what was logged -- there's no original
    # session data to re-render a full review against here (catch up
    # doesn't depend on a prior submission being remembered), so this
    # just lists what was just recorded.
    day_name = datetime.strptime(service_date, "%Y-%m-%d").strftime("%A")
    lines = [f"🎧 Catch Up — {service}", f"🗓 {day_name}, {service_date}", ""]

    for entry in entries:
        suffix = "" if entry["matched"] else " (unrecognized)"
        lines.append(f"• {entry['name']}{suffix}")

    await update.message.reply_text("\n".join(lines))

    catchup_pending.pop(user_id, None)


async def submit_catchup(service, service_date, entries):
    """
    Posts the catch-up log to WEBHOOK_URL. On the Apps Script side,
    entry_type == "catchup" routes to saveCatchUp(), which writes
    into the same "Attendance Log" sheet as normal submissions --
    same columns, just with Source = "Catch Up" instead of
    Online/Onsite.
    """

    payload = {
        "service": service,
        "service_date": service_date,
        "entry_type": "catchup",
        "catch_up_new": [
            {
                "name": e["name"],
                "matched": e["matched"],
                "department": e.get("department", ""),
                "type": e.get("type", ""),
            }
            for e in entries
        ],
    }

    response = await asyncio.to_thread(
        requests.post,
        WEBHOOK_URL,
        json=payload,
        timeout=30,
    )

    return response


# =====================================================
# Pull Summary (live from the Google Sheet)
# =====================================================

async def fetch_summary(service, service_date):
    """
    GETs the summary endpoint on the Apps Script webhook. Returns a
    list of entry dicts (each with name/department/status/source/
    type) on success, or None if the response wasn't a recognizable
    success -- distinct from raising, which happens on a network/
    connection failure instead.
    """

    response = await asyncio.to_thread(
        requests.get,
        WEBHOOK_URL,
        params={"action": "summary", "service": service, "date": service_date},
        timeout=30,
    )

    try:
        body = response.json()
    except ValueError:
        return None

    if response.status_code != 200 or body.get("status") != "success":
        return None

    return body.get("entries", [])


async def fetch_newcomer_names():
    """
    GETs the newcomer list from the webhook (action=newcomers), which
    reads column A (row 3+) of the LGC/LLC/LVC tabs on the lecture
    bot's spreadsheet and strips each entry down to a plain name (no
    department tag). Keeping this the source for the newcomer picker
    means names logged here match the tracker sheet verbatim, so
    syncAttendanceToTrackerLastActivity never needs fuzzy matching
    for names entered this way.

    Returns a dict GROUPED BY CHURCH, e.g.
    {"LGC": [...], "LLC": [...], "LVC": [...]} -- the combined list
    across all three churches was large enough to exceed Telegram's
    inline keyboard button limit, silently dropping names past a
    certain point alphabetically. Grouping lets the picker show one
    church's names at a time, well under that limit.

    Raises RuntimeError on any non-success response (unreachable
    webhook, bad JSON, or an explicit {"status": "error", ...} body)
    so callers can fall back to free-typed entry.
    """

    response = await asyncio.to_thread(
        requests.get,
        WEBHOOK_URL,
        params={"action": "newcomers"},
        timeout=30,
    )

    try:
        body = response.json()
    except ValueError:
        raise RuntimeError(f"Webhook returned an unexpected response (HTTP {response.status_code}).")

    if response.status_code != 200 or body.get("status") != "success":
        raise RuntimeError(body.get("message", f"HTTP {response.status_code}"))

    return body.get("names", {})


def render_summary_text(service, service_date, entries):
    """
    Same overall shape as render_review_text (department breakdown,
    online/onsite tagging, visitors/newcomers, totals) but built
    from rows pulled live from the sheet instead of an in-memory
    session -- so it reflects any edits made directly in the sheet
    after the original submission, and works for dates/services
    that were never held in this bot's memory at all (e.g. after a
    restart).
    """

    day_name = datetime.strptime(service_date, "%Y-%m-%d").strftime("%A")

    lines = [
        f"📊 {html.escape(service)} Attendance Summary",
        f"🗓 {day_name}, {service_date}",
        "",
    ]

    if not entries:
        lines.append("No attendance recorded for this service/date.")

    members_by_dept = {}
    visitors, newcomers, catchups, unrecognized = [], [], [], []

    for e in entries:
        source = e.get("source", "")
        etype = (e.get("type") or "").strip()

        if source == "Catch Up":
            catchups.append(e)
        elif etype == "Visitor":
            visitors.append(e)
        elif etype == "Newcomer":
            newcomers.append(e)
        elif etype == "Unrecognized":
            unrecognized.append(e)
        else:
            members_by_dept.setdefault(e.get("department", ""), []).append(e)

    total_present = 0
    total_online = 0
    total_onsite = 0

    def render_member_row(m):
        nonlocal total_present, total_online, total_onsite
        total_present += 1
        source = m.get("source", "")
        if source == "Online":
            total_online += 1
            tag = "Online"
        else:
            total_onsite += 1
            tag = "<b>Onsite</b>"
        lines.append(f"   • {html.escape(m['name'])} ({tag})")

    for i, department in enumerate(MEMBER_LISTS.keys()):

        dept_entries = members_by_dept.pop(department, [])
        color = DEPARTMENT_COLORS[i % len(DEPARTMENT_COLORS)]

        lines.append(f"{color} {html.escape(department)}: {len(dept_entries)}")

        for m in dept_entries:
            render_member_row(m)

    # Anything left over belongs to a department no longer in
    # MEMBER_LISTS (e.g. someone since moved departments) -- still
    # show it rather than silently dropping people from a
    # historical summary.
    for department, dept_entries in members_by_dept.items():

        lines.append(f"⚪ {html.escape(department)}: {len(dept_entries)}")

        for m in dept_entries:
            render_member_row(m)

    for v in visitors:
        total_present += 1
        if v.get("source") == "Online":
            total_online += 1
        else:
            total_onsite += 1

    for n in newcomers:
        total_present += 1
        if n.get("source") == "Online":
            total_online += 1
        else:
            total_onsite += 1

    lines.append("")
    lines.append(f"👥 Total Present: {total_present}")
    lines.append(f"💻 Total Online: {total_online}")
    lines.append(f"🏛 Total Onsite: {total_onsite}")

    if visitors:
        lines.append("")
        lines.append("👥 Visitors")

        for v in visitors:
            source_part = f", {html.escape(v.get('source', ''))}" if v.get("source") else ""
            lines.append(
                f"• {html.escape(v['name'])} (from {html.escape(v.get('department', ''))}{source_part})"
            )

    if newcomers:
        lines.append("")
        lines.append("🌱 Newcomers")

        for n in newcomers:
            source_part = f", {html.escape(n.get('source', ''))}" if n.get("source") else ""
            lines.append(
                f"• {html.escape(n['name'])} ({html.escape(n.get('department', ''))}{source_part})"
            )

    if unrecognized:
        lines.append("")
        lines.append("❓ Unrecognized")

        for u in unrecognized:
            lines.append(f"• {html.escape(u['name'])}")

    if catchups:
        lines.append("")
        lines.append("🎧 Catch Up")

        for c in catchups:
            lines.append(f"• {html.escape(c['name'])}")

    # Sunday and Wednesday summaries also show roster members who were
    # absent. Resolve names through the same alias index used by attendance
    # entry so a roster alias still counts as present. Iterate MEMBERS rather
    # than MEMBER_LISTS so inactive members are included too.
    if (service or "").strip().casefold() in {"sunday", "wednesday"}:
        present_member_ids = set()
        for entry in entries:
            member = find_member(entry.get("name", ""))
            if member and member.get("member_id"):
                present_member_ids.add(member["member_id"])

        summary_department = {
            "BLESSED FEMALES": "BLESSEDF",
            "BLESSED MALES": "BLESSEDM",
            "JS FEMALES": "JS",
            "JS MALES": "JS",
            "CAMPUS MALES": "Campus Male",
        }
        excluded_departments = {"OPM", "OVERSEAS PINOY MEMBERS", "MILKY WAY", "NEWCOMERS"}
        absentees_by_dept = {}

        for member_id, member in MEMBERS.items():
            department = (member.get("department") or "").strip()
            department_key = department.upper()
            status = (member.get("status") or "").strip().upper()
            if status == "NEWCOMER" or department_key in excluded_departments:
                continue
            if member_id in present_member_ids:
                continue

            display_department = summary_department.get(department, department)
            absentees_by_dept.setdefault(display_department, []).append(member)

        lines.append("")
        lines.append("🚫 Absentees")
        ordered_departments = list(MEMBER_LISTS.keys())
        ordered_departments.extend(
            dept for dept in absentees_by_dept if dept not in MEMBER_LISTS
        )
        if not absentees_by_dept:
            lines.append("No absentees in the included roster groups.")
        else:
            for department in ordered_departments:
                absent_members = absentees_by_dept.get(department, [])
                if not absent_members:
                    continue
                lines.append(f"• {html.escape(department)}: {len(absent_members)}")
                for absent_member in absent_members:
                    lines.append(f"   • {html.escape(absent_member['display_name'])}")

    return "\n".join(lines)


async def submit_correction(service, service_date, action, row=None, member=None):
    """
    Posts a correction to WEBHOOK_URL. entry_type == "correction"
    routes to applyCorrection() on the Apps Script side, which
    either deletes a specific row (action="remove") or appends one
    (action="add") directly in "Attendance Log".
    """
    payload = {
        "entry_type": "correction",
        "action": action,
        "service": service,
        "service_date": service_date,
    }
    if row is not None:
        payload["row"] = row
    if member is not None:
        payload["member"] = member
    response = await asyncio.to_thread(
        requests.post,
        WEBHOOK_URL,
        json=payload,
        timeout=30,
    )
    return response


def parse_webhook_body(response):
    try:
        body = response.json()
        return body.get("status"), body.get("message")
    except ValueError:
        return None, None


def get_newcomer_context(user_id):
    """
    The newcomer-picker callbacks (nchurch/nnc/ndept/nsrc) are
    shared by two different flows: adding a newcomer mid-attendance-
    session, and adding one via Correct Attendance. Returns
    (context_dict, "session"|"correction") for whichever flow is
    currently active for this user, or (None, None) if neither.
    """
    pending = correction_pending.get(user_id)
    if pending and pending.get("awaiting", "").startswith("add_newcomer"):
        return pending, "correction"
    if user_id in user_sessions:
        return user_sessions[user_id], "session"
    return None, None


def _correction_page_bounds(pending):
    """
    Clamps pending["page"] into range for the current entry count
    and returns (page, total_pages, start_idx, end_idx) -- start/end
    are the slice bounds (end exclusive) of entries shown on that
    page. Keeps pagination correct even after an add/remove changes
    how many entries there are.
    """
    entries = pending["entries"]
    total_pages = max(1, -(-len(entries) // CORRECTION_PAGE_SIZE))  # ceil div

    page = pending.get("page", 0)
    page = max(0, min(page, total_pages - 1))
    pending["page"] = page

    start = page * CORRECTION_PAGE_SIZE
    end = start + CORRECTION_PAGE_SIZE

    return page, total_pages, start, end


def build_correction_text(pending):
    service = pending["service"]
    date = pending["date"]
    entries = pending["entries"]
    day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    lines = [
        f"✏️ Correcting: {html.escape(service)}",
        f"🗓 {day_name}, {date}",
        "",
    ]
    if not entries:
        lines.append("No entries currently logged for this service/date.")
    else:
        page, total_pages, start, end = _correction_page_bounds(pending)
        lines.append(f"Currently logged ({len(entries)}):")
        if total_pages > 1:
            lines.append(f"Page {page + 1}/{total_pages}")
        lines.append("")
        for e in entries[start:end]:
            lines.append(f"• {e['name']} — {e.get('department', '')} ({e.get('source', '')})")
    lines.append("")
    lines.append("Tap a name below to remove it, or use ➕ Add for someone missed.")
    return "\n".join(lines)


def build_correction_keyboard(pending):
    keyboard = []

    _, total_pages, start, end = _correction_page_bounds(pending)
    page = pending["page"]

    for i, e in enumerate(pending["entries"][start:end], start=start):
        keyboard.append(
            [InlineKeyboardButton(f"❌ {e['name']}", callback_data=f"cordel:{i}")]
        )

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅ Prev", callback_data=f"corpage:{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="corpage:noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡", callback_data=f"corpage:{page + 1}"))
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton("➕ Add Member", callback_data="coraddmember"),
        InlineKeyboardButton("➕ Add Newcomer", callback_data="coraddnewcomer"),
    ])
    keyboard.append([
        InlineKeyboardButton("➕ Add Visitor", callback_data="coraddvisitor"),
    ])
    keyboard.append([
        InlineKeyboardButton("✅ Finish Correcting", callback_data="cordone"),
    ])
    return InlineKeyboardMarkup(keyboard)


async def send_correction_menu(send_func, pending):
    await send_func(
        text=build_correction_text(pending),
        reply_markup=build_correction_keyboard(pending),
    )


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
    return (
        f"❓ Unrecognized name: \"{name}\"\n\n"
        "Which department do they belong to, or mark them as a "
        "Visitor/Newcomer if they're not a member?"
    )


def build_resolve_departments_keyboard():
    """
    Shared by both resolve entry points — the auto-queue right
    after OCR (advance_resolve_queue) and the "🔍 Resolve Unknown"
    button on the review screen (show_resolve_departments) — so an
    unrecognized name can always be marked as a Visitor or Newcomer
    right alongside picking a department, not just from one of the
    two paths.
    """

    keyboard = [
        [InlineKeyboardButton("👋 Mark as Visitor", callback_data="rvisitor")],
        [InlineKeyboardButton("🌱 Mark as Newcomer", callback_data="rnewcomer")],
    ]

    for department in MEMBER_LISTS:
        keyboard.append(
            [InlineKeyboardButton(department, callback_data=f"adept:{department}")]
        )

    return keyboard


async def advance_resolve_queue(send_func, session):
    """
    Pops the next unresolved name and prompts for its department
    (or Visitor/Newcomer). Returns True if a prompt was sent (still
    resolving), False if the queue is now empty.
    """

    queue = session.get("resolve_queue")

    if queue:
        session["resolving_text"] = queue.pop(0)
        session["resolve_added_members"] = set()

        keyboard = build_resolve_departments_keyboard()

        await send_func(
            text=build_resolve_prompt_text(session),
            reply_markup=InlineKeyboardMarkup(keyboard)
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


def build_newcomer_church_keyboard(names_by_church):

    keyboard = [
        [InlineKeyboardButton(f"{church} ({len(names)})", callback_data=f"nchurch:{church}")]
        for church, names in names_by_church.items()
        if names
    ]
    keyboard.append(
        [InlineKeyboardButton("✏️ Other (type manually)", callback_data="nnc_other")]
    )

    return InlineKeyboardMarkup(keyboard)


async def show_newcomer_picker(send_func, session):
    """
    Step 1 of newcomer selection: pick a church first (LGC/LLC/LVC),
    then names for that church only -- keeps each keyboard well
    under Telegram's inline button limit, unlike showing all three
    churches' names merged into one list. Falls back to free-typed
    entry if the webhook call fails or nothing comes back -- typing
    is still allowed for anyone genuinely not on the tracker yet.
    """

    try:
        names_by_church = await fetch_newcomer_names()
    except Exception as e:
        session["newcomer_names_by_church"] = None
        session["newcomer_names"] = None
        await send_func(
            f"⚠️ Couldn't load the newcomer list from the sheet.\n\n{e}\n\n"
            "Type the newcomer's name instead:"
        )
        return

    if not names_by_church or not any(names_by_church.values()):
        session["newcomer_names_by_church"] = None
        session["newcomer_names"] = None
        await send_func(
            "⚠️ No names came back from the sheet. Type the newcomer's name instead:"
        )
        return

    session["newcomer_names_by_church"] = names_by_church
    session["newcomer_names"] = None

    await send_func(
        text="👤 Which church?",
        reply_markup=build_newcomer_church_keyboard(names_by_church),
    )


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

    keyboard = build_resolve_departments_keyboard()

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
    user_id = query.from_user.id

    action = query.data

    if action == "message_portal_unconfigured":
        await query.answer(
            "The sermon library address has not been configured yet.", show_alert=True
        )
        return
    await query.answer()

    if action == "message_signup":
        signup_waiting.add(user_id)
        await query.edit_message_text(
            "Sign up for message access through Telegram\n\n"
            "Type the name you use. If it does not match the roster exactly, an organizer will match it before approving access."
        )
        return

    if action == "sermon:upload":
        if not is_sermon_admin(user_id):
            await query.message.reply_text("🚫 Sermon uploads are limited to sermon administrators.")
            return
        if query.message.chat.type != "private":
            await query.message.reply_text("Please upload sermon PDFs in a private chat with the bot.")
            return
        await begin_sermon_upload(query.message.reply_text, user_id)
        return

    if action == "sermon:signups":
        if not is_sermon_admin(user_id):
            await query.message.reply_text("🚫 Signup approvals are limited to sermon administrators.")
            return
        if query.message.chat.type != "private":
            await query.message.reply_text("Please review sign-ups in a private chat with the bot.")
            return
        await send_pending_link_requests(query.message.reply_text)
        return

    if action.startswith("msgacc:"):
        if not is_sermon_admin(user_id):
            await query.message.reply_text("Only sermon administrators can review sign-ups.")
            return
        parts = action.split(":")
        decision = parts[1]
        if decision == "match":
            requested_id = int(parts[2])
            roster_match_waiting[user_id] = requested_id
            await query.message.reply_text(
                f"Type the full name or part of the roster name to match Telegram account {requested_id}."
            )
            return
        if decision == "link":
            requested_id = int(parts[2])
            member_id = parts[3]
            member = MEMBERS.get(member_id)
            if not member:
                await query.message.reply_text("That roster entry no longer exists. Please search again.")
                return
            member_name = member.get("display_name") or member.get("official_name") or member_id
            request = sermon_portal.assign_pending_link_member(
                requested_id, member_id, member_name
            )
            if not request:
                await query.edit_message_text("This signup is no longer waiting for a roster match.")
                return
            keyboard = [[
                InlineKeyboardButton("✅ Approve", callback_data=f"msgacc:a:{requested_id}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"msgacc:d:{requested_id}"),
            ]]
            await query.edit_message_text(
                f"Matched '{request['member_name']}' to {member_name} ({member_id}). Approve this link?",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            try:
                await context.bot.send_message(
                    chat_id=requested_id,
                    text=f"An organizer matched your signup to {member_name}. The link is waiting for final approval.",
                )
            except Exception as exc:
                print("Could not notify member about roster match:", type(exc).__name__)
            return
        requested_id = int(parts[2])
        if decision == "a":
            request, error = sermon_portal.approve_link_request(requested_id, user_id)
            if error:
                await query.edit_message_text(f"Could not approve: {error}")
                return
            await query.edit_message_text(f"✅ Linked {request['member_name']} to the approved Telegram account.")
            try:
                await context.bot.send_message(
                    chat_id=requested_id,
                    text=f"✅ Your message-access sign-up as {request['member_name']} was approved. Open /start to read eligible sermons.",
                )
            except Exception as exc:
                print("Could not send message-access approval:", type(exc).__name__)
        else:
            request = sermon_portal.deny_link_request(requested_id)
            await query.edit_message_text(
                f"Sign-up denied for {request['member_name']}." if request
                else "This request is no longer pending."
            )
            if request:
                try:
                    await context.bot.send_message(
                        chat_id=requested_id,
                        text="Your message-access sign-up was not approved. Please contact an organizer if you think this was a mistake.",
                    )
                except Exception as exc:
                    print("Could not send message-access denial:", type(exc).__name__)
        return

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

    # -----------------------------
    # Catch Up menu
    # -----------------------------
    if action == "catchup_menu":

        if user_id in user_sessions:
            await query.edit_message_text(
                "Please finish or /done your current attendance session first, "
                "then try Log Catch Up again."
            )
            return

        await query.edit_message_text(
            "🎧 Catch Up — select the service:",
            reply_markup=build_service_keyboard("csvc"),
        )
        return

    if action.startswith("csvc:"):

        choice = action.split(":", 1)[1]

        if choice == "special":

            awaiting_special_service.add(user_id)
            catchup_pending[user_id] = {"service": None, "awaiting": "name"}

            await query.edit_message_text(
                "Please type the name of the Service/Event:"
            )

        else:

            catchup_pending[user_id] = {"service": choice, "awaiting": "date"}

            await query.edit_message_text(
                f"🎧 Catch Up: {choice}\n\n"
                "Please type the date this catch up is for (YYYY-MM-DD):"
            )

        return

    # -----------------------------
    # Pull Summary menu
    # -----------------------------
    if action == "summary_menu":

        await query.edit_message_text(
            "📊 Pull Summary — select the service:",
            reply_markup=build_service_keyboard("sumsvc"),
        )
        return

    if action.startswith("sumsvc:"):

        choice = action.split(":", 1)[1]

        if choice == "special":

            awaiting_special_service.add(user_id)
            summary_pending[user_id] = {"service": None, "awaiting": "name"}

            await query.edit_message_text(
                "Please type the name of the Service/Event:"
            )

        else:

            summary_pending[user_id] = {"service": choice, "awaiting": "date"}

            await query.edit_message_text(
                f"📊 Summary: {choice}\n\n"
                "Please type the date to pull (YYYY-MM-DD):"
            )

        return

    # -----------------------------
    # Correct Attendance menu
    # -----------------------------
    if action == "correct_menu":
        await query.edit_message_text(
            "✏️ Correct Attendance — select the service:",
            reply_markup=build_service_keyboard("corsvc"),
        )
        return

    if action.startswith("corsvc:"):
        choice = action.split(":", 1)[1]
        if choice == "special":
            awaiting_special_service.add(user_id)
            correction_pending[user_id] = {"service": None, "awaiting": "name"}
            await query.edit_message_text(
                "Please type the name of the Service/Event:"
            )
        else:
            correction_pending[user_id] = {"service": choice, "awaiting": "date"}
            await query.edit_message_text(
                f"✏️ Correct: {choice}\n\n"
                "Please type the date to correct (YYYY-MM-DD):"
            )
        return

    # -----------------------------
    # Correct Attendance: page navigation
    # -----------------------------
    if action.startswith("corpage:"):

        pending = correction_pending.get(user_id)

        if not pending:
            return

        target = action.split(":", 1)[1]

        if target != "noop":
            pending["page"] = int(target)

        await query.edit_message_text(
            build_correction_text(pending),
            reply_markup=build_correction_keyboard(pending),
        )
        return

    # -----------------------------
    # Correct Attendance: remove an entry
    # -----------------------------
    if action.startswith("cordel:"):

        idx = int(action.split(":", 1)[1])
        pending = correction_pending.get(user_id)

        if not pending or idx >= len(pending["entries"]):
            return

        entry = pending["entries"][idx]

        await query.edit_message_text(f"🗑 Removing {entry['name']}...")

        try:
            response = await submit_correction(pending["service"], pending["date"], "remove", row=entry["row"])
            body_status, body_message = parse_webhook_body(response)

            if response.status_code == 200 and body_status == "success":
                pending["entries"].pop(idx)
                # Rows below the deleted one shift up by 1 in the sheet.
                for e in pending["entries"]:
                    if e["row"] > entry["row"]:
                        e["row"] -= 1
                await query.message.reply_text(f"✅ Removed {entry['name']}.")
            else:
                await query.message.reply_text(
                    f"⚠️ Couldn't remove: {body_message or f'HTTP {response.status_code}'}"
                )
        except Exception as e:
            await query.message.reply_text(f"⚠️ Couldn't reach the webhook.\n\n{e}")

        await send_correction_menu(query.message.reply_text, pending)
        return

    if action == "coraddmember":

        pending = correction_pending.get(user_id)

        if not pending:
            return

        pending["awaiting"] = "add_member_name"

        await query.message.reply_text("Type the member's name (as it appears in the roster):")
        return

    if action.startswith("coraddsrc:"):

        source = action.split(":", 1)[1]
        pending = correction_pending.get(user_id)

        if not pending or "pending_add" not in pending:
            return

        member = pending.pop("pending_add")
        member["source"] = source

        await query.edit_message_text(f"➕ Adding {member['name']}...")

        try:
            response = await submit_correction(pending["service"], pending["date"], "add", member=member)
            body_status, body_message = parse_webhook_body(response)

            if response.status_code == 200 and body_status == "success":
                entries = await fetch_summary(pending["service"], pending["date"])
                if entries is not None:
                    pending["entries"] = entries
                await query.message.reply_text(f"✅ Added {member['name']} ({source}).")
            else:
                await query.message.reply_text(
                    f"⚠️ Couldn't add: {body_message or f'HTTP {response.status_code}'}"
                )
        except Exception as e:
            await query.message.reply_text(f"⚠️ Couldn't reach the webhook.\n\n{e}")

        pending["awaiting"] = "menu"
        await send_correction_menu(query.message.reply_text, pending)
        return

    if action == "coraddnewcomer":

        pending = correction_pending.get(user_id)

        if not pending:
            return

        pending["awaiting"] = "add_newcomer"

        await show_newcomer_picker(query.message.reply_text, pending)
        return

    if action == "coraddvisitor":

        pending = correction_pending.get(user_id)

        if not pending:
            return

        pending["awaiting"] = "add_visitor_name"

        await query.message.reply_text("Enter the visitor's name:")
        return

    if action.startswith("coraddvsrc:"):

        source = action.split(":", 1)[1]
        pending = correction_pending.get(user_id)

        if not pending:
            return

        name = pending.pop("pending_visitor_name", None)
        from_ = pending.pop("pending_visitor_from", None)

        if not (name and from_):
            return

        member = {"name": name, "department": from_, "type": "Visitor", "source": source}

        await query.edit_message_text(f"➕ Adding visitor {name}...")

        try:
            response = await submit_correction(pending["service"], pending["date"], "add", member=member)
            body_status, body_message = parse_webhook_body(response)

            if response.status_code == 200 and body_status == "success":
                entries = await fetch_summary(pending["service"], pending["date"])
                if entries is not None:
                    pending["entries"] = entries
                await query.message.reply_text(f"✅ Added visitor {name} ({source}).")
            else:
                await query.message.reply_text(
                    f"⚠️ Couldn't add: {body_message or f'HTTP {response.status_code}'}"
                )
        except Exception as e:
            await query.message.reply_text(f"⚠️ Couldn't reach the webhook.\n\n{e}")

        pending["awaiting"] = "menu"
        await send_correction_menu(query.message.reply_text, pending)
        return

    if action == "cordone":

        correction_pending.pop(user_id, None)
        await query.edit_message_text("✅ Done correcting attendance.")
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

        await show_newcomer_picker(query.message.reply_text, session)

        return

    elif action.startswith("nchurch:"):

        church = action.split(":", 1)[1]
        ctx, ctx_type = get_newcomer_context(user_id)

        if ctx is None:
            return

        names_by_church = ctx.get("newcomer_names_by_church") or {}
        names = names_by_church.get(church, [])

        if not names:
            await query.edit_message_text(f"No names found for {church}.")
            return

        ctx["newcomer_names"] = names

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"nnc:{i}")]
            for i, name in enumerate(names)
        ]
        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="nnc_back")])
        keyboard.append([InlineKeyboardButton("✏️ Other (type manually)", callback_data="nnc_other")])

        await query.edit_message_text(
            f"👤 Select the newcomer ({church}):",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    elif action == "nnc_back":

        ctx, ctx_type = get_newcomer_context(user_id)

        if ctx is None:
            return

        names_by_church = ctx.get("newcomer_names_by_church")

        if not names_by_church:
            await show_newcomer_picker(query.message.reply_text, ctx)
            return

        await query.edit_message_text(
            "👤 Which church?",
            reply_markup=build_newcomer_church_keyboard(names_by_church),
        )

        return

    elif action.startswith("nnc:"):

        idx = int(action.split(":", 1)[1])
        ctx, ctx_type = get_newcomer_context(user_id)

        if ctx is None:
            return

        names = ctx.get("newcomer_names") or []

        if idx >= len(names):
            return

        name = names[idx]
        ctx["newcomer_pending_name"] = name

        await query.edit_message_text(
            f"Department for \"{name}\"?",
            reply_markup=build_department_picker("ndept")
        )

        return

    elif action == "nnc_other":

        await query.edit_message_text("✏️ Type the newcomer's name:")

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
        ctx, ctx_type = get_newcomer_context(user_id)

        if ctx is None:
            return

        name = ctx.get("newcomer_pending_name")

        if name:

            ctx["newcomer_pending_department"] = department

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
        ctx, ctx_type = get_newcomer_context(user_id)

        if ctx is None:
            return

        name = ctx.get("newcomer_pending_name")
        department = ctx.get("newcomer_pending_department")

        if not (name and department):
            return

        ctx["newcomer_pending_name"] = None
        ctx["newcomer_pending_department"] = None

        if ctx_type == "session":

            ctx["newcomers"].append({
                "name": name,
                "department": department,
                "source": source,
            })

            await query.edit_message_text(
                f"✅ Newcomer added: {name} ({department}, {source})"
            )

            await query.message.reply_text(
                "Type another newcomer's name, or /done to return to the review."
            )

        else:  # correction flow

            member = {"name": name, "department": department, "type": "Newcomer", "source": source}

            await query.edit_message_text(f"➕ Adding {name}...")

            try:
                response = await submit_correction(ctx["service"], ctx["date"], "add", member=member)
                body_status, body_message = parse_webhook_body(response)

                if response.status_code == 200 and body_status == "success":
                    entries = await fetch_summary(ctx["service"], ctx["date"])
                    if entries is not None:
                        ctx["entries"] = entries
                    await query.message.reply_text(f"✅ Added {name} ({department}, {source}).")
                else:
                    await query.message.reply_text(
                        f"⚠️ Couldn't add: {body_message or f'HTTP {response.status_code}'}"
                    )
            except Exception as e:
                await query.message.reply_text(f"⚠️ Couldn't reach the webhook.\n\n{e}")

            ctx["awaiting"] = "menu"
            await send_correction_menu(query.message.reply_text, ctx)

        return

    elif action == "submit":

        session = user_sessions[user_id]

        await query.message.reply_text(
            "Submitting attendance..."
        )
        try:

            response = await submit_attendance(session)

            # Apps Script web apps always return HTTP 200 for any
            # execution that doesn't crash outright — even when the
            # script's own code catches an error and reports
            # {"status": "error", ...} in the JSON body. So the
            # webhook's actual verdict has to come from the body,
            # not the HTTP status code alone.
            body_status = None
            body_message = None

            try:
                body = response.json()
                body_status = body.get("status")
                body_message = body.get("message")
            except ValueError:
                pass

            if response.status_code == 200 and body_status == "success":

                del user_sessions[user_id]

                # Drop the buttons so the review card can't be
                # re-submitted, but keep the review text itself
                # visible in the chat instead of overwriting it.
                await query.edit_message_reply_markup(reply_markup=None)

                await query.message.reply_text(
                    "✅ Attendance successfully submitted."
                )

            elif response.status_code == 200 and body_status == "error":

                await query.message.reply_text(
                    "Submission failed.\n\n"
                    f"Webhook error: {body_message or 'unknown error'}"
                )

            else:

                await query.message.reply_text(

                    f"Submission failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text[:500]}"

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
    /skip — nobody attended online (or onsite) at all; moves
    straight to the next stage / review.
    """

    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text("No active attendance session.")
        return

    session = user_sessions[user_id]

    if session["stage"] == STAGE_ONLINE:
        session["online_result"] = {"recognized": [], "unknown": []}

        await update.message.reply_text(
            "🟢 Online attendance skipped — no online attendees recorded."
        )

        await continue_after_online(update.message.reply_text, context, user_id, session)
        return

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
    # Keep request content, names, and Telegram IDs out of Railway logs.
    update_type = "callback" if update.callback_query else "message" if update.message else "other"
    print("Telegram update received:", update_type)


async def portal_attendance_check(telegram_id, sermon):
    """Check the live attendance sheet for this linked member and service."""
    link = sermon_portal.get_member_link(telegram_id)
    if not link:
        return False
    cache_key = (sermon["service"], sermon["service_date"])
    cached = portal_attendance_cache.get(cache_key)
    if cached and cached[0] > asyncio.get_running_loop().time():
        entries = cached[1]
    else:
        async with portal_attendance_lock:
            cached = portal_attendance_cache.get(cache_key)
            if cached and cached[0] > asyncio.get_running_loop().time():
                entries = cached[1]
            else:
                entries = await fetch_summary(*cache_key)
                if entries is None:
                    raise RuntimeError("Attendance summary could not be read from the webhook.")
                portal_attendance_cache[cache_key] = (
                    asyncio.get_running_loop().time() + 300, entries
                )
    linked_member = MEMBERS.get(link["member_id"])
    if not linked_member:
        return False
    linked_names = {
        normalize_name(name)
        for name in [
            linked_member.get("display_name"),
            linked_member.get("official_name"),
            *(linked_member.get("aliases") or []),
            link["member_name"],
        ]
        if name
    }
    linked_department = normalize_name(linked_member.get("department", ""))
    linked_departments = {linked_department}

    # Attendance summary groups can use short labels (for example,
    # BLESSEDF) while the master roster stores the full department
    # name (BLESSED FEMALES). Accept the summary bucket that contains
    # this roster member and belongs to the same canonical department.
    linked_display_name = normalize_name(linked_member.get("display_name", ""))
    for department_label, display_names in MEMBER_LISTS.items():
        bucket_names = {normalize_name(name) for name in display_names}
        if linked_display_name not in bucket_names:
            continue
        same_department = any(
            normalize_name(member.get("department", "")) == linked_department
            and normalize_name(member.get("display_name", "")) in bucket_names
            for member in MEMBERS.values()
        )
        if same_department:
            linked_departments.add(normalize_name(department_label))

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if (
            normalize_name(entry.get("name", "")) in linked_names
            and normalize_name(entry.get("department", "")) in linked_departments
        ):
            return True
    return False


async def start_sermon_portal(application):
    sermon_portal.initialize_storage()
    if not PUBLIC_BASE_URL:
        print("Sermon reader is disabled until PUBLIC_BASE_URL is configured.")
        return
    if not PUBLIC_BASE_URL.startswith("https://"):
        raise RuntimeError("PUBLIC_BASE_URL must use HTTPS for Telegram Mini App authentication.")
    from aiohttp import web
    sermon_portal.set_attendance_checker(portal_attendance_check)
    runner = web.AppRunner(sermon_portal.create_web_app(BOT_TOKEN, portal_attendance_check))
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    application.bot_data["sermon_portal_runner"] = runner
    print("Sermon reader web endpoint started on port", port)


async def stop_sermon_portal(application):
    runner = application.bot_data.pop("sermon_portal_runner", None)
    if runner:
        await runner.cleanup()


async def error_handler(update, context):
    print("EXCEPTION:", repr(context.error))
    import traceback
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)


print("=== BUILD 6 ===")
app = (ApplicationBuilder().token(BOT_TOKEN)
       .post_init(start_sermon_portal)
       .post_shutdown(stop_sermon_portal)
       .build())

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("service", service_menu))
app.add_handler(CommandHandler("signup", signup))
app.add_handler(CommandHandler("upload_message", upload_message))
app.add_handler(CommandHandler("message_access", message_access))
app.add_handler(CommandHandler("predawn", predawn))
app.add_handler(CommandHandler("sunday", sunday))
app.add_handler(CommandHandler("wednesday", wednesday))
app.add_handler(CommandHandler("friday", friday))
app.add_handler(CommandHandler("retro", retro))
app.add_handler(CommandHandler("catchup", catchup))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("correct", correct))
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
    MessageHandler(filters.Document.ALL, receive_document)
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
