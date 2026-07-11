import os

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
    attendance_summary,
)

from members import (
    MEMBER_LISTS,
    MEMBERS,
)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

print(BOT_TOKEN)
print(WEBHOOK_URL)


user_sessions = {}

# =====================================================
# Session Stages
# =====================================================

STAGE_ONLINE = "online"
STAGE_ONSITE = "onsite"
STAGE_REVIEW = "review"

STAGE_VISITOR = "visitor"
STAGE_NEWCOMER = "newcomer"



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Attendance Bot V2 is ready."
    )


async def start_service(update, context, service):

    user_id = update.effective_user.id

    user_sessions[user_id] = {

        "service": service,

        "service_date": datetime.now(
            ZoneInfo("Asia/Manila")
        ).strftime("%Y-%m-%d"),

        "stage": STAGE_ONLINE,

        # Uploaded screenshots
        "online_images": [],
        "onsite_images": [],

        # OCR Results
        "online_result": None,
        "onsite_result": None,

        # Master Attendance
        "recognized": set(),
        "online_members": set(),
        "onsite_members": set(),
        "unknown": set(),

        # Manual additions
        "newcomers": [],
        "visitors": [],

        # Department verification
        "current_department": None,

    }
    await update.message.reply_text(

        f"{service} Attendance\n\n"

        "Please upload ONLINE participant screenshots.\n\n"

        "When finished, type:\n"

        "/done"
    )
async def predawn(update, context):
    await start_service(update, context, "Predawn")


async def sunday(update, context):
    await start_service(update, context, "Sunday")


async def wednesday(update, context):
    await start_service(update, context, "Wednesday")


async def friday(update, context):
    await start_service(update, context, "Friday")

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("===== RECEIVE PHOTO CALLED =====")
    print(update)

    await update.message.reply_text("I received something!")

    if update.message.photo:
        await update.message.reply_text("PHOTO detected!")

    elif update.message.document:
        await update.message.reply_text("DOCUMENT detected!")

    else:
        await update.message.reply_text("Something else detected.")

    user_id = update.effective_user.id
    session = user_sessions[user_id]

    print(session["stage"])

    photo = update.message.photo[-1]

    file = await photo.get_file()

    filename = f"temp/{uuid.uuid4()}.jpg"

    await file.download_to_drive(filename)

    print("Downloaded:", filename)

    if session["stage"] == "online":
        session["online_images"].append(filename)
        print(session["online_images"])

        await update.message.reply_text(
            f"✅ Online screenshot saved.\n"
            f"Total: {len(session['online_images'])}\n\n"
            "Upload another image or type /done."
        )

    elif session["stage"] == "onsite":

        session["onsite_images"].append(filename)

        await update.message.reply_text(
            f"✅ Onsite screenshot saved.\n"
            f"Total: {len(session['onsite_images'])}\n\n"
            "Upload another image or type /done."
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

        result = recognize_multiple_images(
            session["online_images"]
        )

        session["online_result"] = result

        update_master_attendance(
            session,
            result,
            "online"
        )

        await update.message.reply_text(
            attendance_summary(result)
        )

        session["stage"] = STAGE_ONSITE

        await update.message.reply_text(

            "✅ Online attendance completed.\n\n"

            "Now upload ONSITE screenshots.\n\n"

            "When finished, type /done."

        )

        return

    # -----------------------------
    # ONSITE COMPLETE
    # -----------------------------
    if session["stage"] == STAGE_ONSITE:

        if not session["onsite_images"]:

            await update.message.reply_text(

                "No onsite screenshots uploaded.\n\n"

                "If nobody attended onsite,\n"

                "type /skip"

            )

            return

        await update.message.reply_text(
            "Processing onsite screenshots..."
        )

        result = recognize_multiple_images(
            session["onsite_images"]
        )

        session["onsite_result"] = result

        update_master_attendance(
            session,
            result,
            "onsite"
        )

        session["stage"] = STAGE_REVIEW

        await show_review(update, context)

        return

def update_master_attendance(session, result, source):
    """
    Update the master attendance sets from an OCR result.

    source:
        "online"
        "onsite"
    """

    for member in result["recognized"]:

        name = member["name"]

        session["recognized"].add(name)

        if source == "online":
            session["online_members"].add(name)

        elif source == "onsite":
            session["onsite_members"].add(name)

    session["unknown"].update(result["unknown"])

def get_member_info(name):
    """
    Returns the member record from MEMBERS by display name.
    """

    for member in MEMBERS.values():
        if member["name"] == name:
            return member

    return None

async def show_review(update, context):

    user_id = update.effective_user.id
    session = user_sessions[user_id]

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
        missing = []

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

    if session["unknown"]:
        lines.append("")
        lines.append("❓ Unknown Names")

        for name in sorted(session["unknown"]):
            lines.append(f"• {name}")
    
    if session["visitors"]:
        lines.append("")
        lines.append("👥 Visitors")

        for visitor in session["visitors"]:
            lines.append(f"• {visitor}")

    if session["newcomers"]:
        lines.append("")
        lines.append("🌱 Newcomers")

        for newcomer in session["newcomers"]:
            lines.append(f"• {newcomer}")

    keyboard = [

    [
        InlineKeyboardButton(
            "✔ Verify Department",
            callback_data="verify"
        )
    ],

    [
        InlineKeyboardButton(
            "➕ Visitor",
            callback_data="visitor"
        ),

        InlineKeyboardButton(
            "➕ Newcomer",
            callback_data="newcomer"
        ),
    ],

    [
        InlineKeyboardButton(
            "✅ Submit",
            callback_data="submit"
        )
    ],

    [
        InlineKeyboardButton(
            "❌ Cancel",
            callback_data="cancel"
        )
    ],

]

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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

def get_member_info(name):

    for department, members in MEMBER_LISTS.items():

        if name in members:

            return {
                "name": name,
                "department": department,
                "type": "Member"
            }

    return None

async def show_review_callback(query, session):

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
            member
            for member in members
            if member not in recognized
        ]

        if missing:

            for member in missing:
                lines.append(f"   • {member}")

    lines.append("")
    lines.append(
        f"👥 Total Present: {total_present}/{total_expected}"
    )

    if session["unknown"]:

        lines.append("")
        lines.append("❓ Unknown Names")

        for name in sorted(session["unknown"]):
            lines.append(f"• {name}")

    if session["visitors"]:

        lines.append("")
        lines.append("👥 Visitors")

        for visitor in session["visitors"]:
            lines.append(f"• {visitor}")

    if session["newcomers"]:

        lines.append("")
        lines.append("🌱 Newcomers")

        for newcomer in session["newcomers"]:
            lines.append(f"• {newcomer}")

    keyboard = [

        [
            InlineKeyboardButton(
                "✔ Verify Department",
                callback_data="verify"
            )
        ],

        [
            InlineKeyboardButton(
                "➕ Visitor",
                callback_data="visitor"
            ),
            InlineKeyboardButton(
                "➕ Newcomer",
                callback_data="newcomer"
            ),
        ],

        [
            InlineKeyboardButton(
                "✅ Submit",
                callback_data="submit"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel"
            )
        ],

    ]

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard)
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

    response = requests.post(

        WEBHOOK_URL,

        json=payload,

        timeout=30,

    )

    return response

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_sessions:

        await query.edit_message_text(
            "This attendance session has already ended."
        )
        return

    action = query.data

    if action == "verify":

        await show_departments(query, user_sessions[user_id])

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

        await query.message.reply_text(

            "Enter visitor names.\n\n"

            "One name per line.\n\n"

            "Example:\n"

            "Juan Dela Cruz\n"

            "Maria Santos\n\n"

            "When finished, type:\n"

            "/done"

        )

    elif action == "newcomer":

        await query.message.reply_text(
            "Newcomer entry will be implemented next."
        )

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

        await show_review_callback(
            query,
            user_sessions[user_id]
        )

        return

async def debug_any(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("UPDATE RECEIVED")
    print(update)

app.add_handler(
    MessageHandler(
        filters.ALL,
        debug_any
    ),
    group=-1
)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("predawn", predawn))
app.add_handler(CommandHandler("sunday", sunday))
app.add_handler(CommandHandler("wednesday", wednesday))
app.add_handler(CommandHandler("friday", friday))
app.add_handler(CommandHandler("done", done))

app.add_handler(
    MessageHandler(
        filters.ALL,
        debug_any,
    ),
    group=-1,
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        receive_photo,
    )
)

app.add_handler(
    CallbackQueryHandler(button_handler)
)

print("Attendance Bot V2 is running...")
app.run_polling()