# Sermon message portal deployment

The sermon library runs inside the existing Telegram bot deployment. Members open it as a Telegram Mini App; the bot does not send PDF attachments to readers. PDF access is checked against the existing attendance-summary webhook each time a reader opens a sermon. Attendance loggers see both the existing attendance menu and the sermon access buttons from `/start`; other members see the sign-up and reading options.

## Railway setup

1. Attach a Railway Volume to the bot service and mount it at `/data`. This stores approved Telegram-to-member links, sermon metadata, and uploaded PDFs across deploys/restarts. Keep the service at one replica because this first version uses SQLite on that volume.
2. Generate a public HTTPS domain for the service, targeting the app's `PORT` (defaults to `8080`). The service now runs as a web process and binds to `0.0.0.0`.
3. Add these Railway variables:

   - `PUBLIC_BASE_URL=https://<your-railway-domain>`
   - `SERMON_DATA_DIR=/data`
   - `ATTENDANCE_LOGGER_IDS=<comma-separated Telegram numeric IDs>`
   - `SERMON_ADMIN_IDS=<comma-separated Telegram numeric IDs>`

   `ATTENDANCE_LOGGER_IDS` controls attendance entry, review, correction, catch-up, and summary commands. `SERMON_ADMIN_IDS` controls sermon uploads and account-link approvals. If either variable is omitted, that role falls back to the existing `ORGANIZER_IDS` in `config.py`.

4. Use the HTTPS Railway domain in `PUBLIC_BASE_URL`; the app URL is `https://<your-railway-domain>/app`. The bot's inline button opens this Mini App. Configuring it as the bot's main/menu Mini App in BotFather is optional.

## Weekly use

- Members use `/start` or `/signup` and submit the name they use. Exact roster matches wait for administrator approval. If a name does not match uniquely, it is sent to the sermon administrators, who can search the roster, select the right entry, and then approve or deny the link.
- Sermon administrators can tap **Upload sermon PDF** or send `/upload_message`, then upload the PDF with a caption such as `Sunday | 2026-10-04`. The library labels it by service and date. If the original is in Google Drive, download a copy and upload it to the bot; direct Drive fetching is not configured in this version.
- Upload an **unlocked PDF**. The current protected source must first be opened with its existing password and saved as a copy without a password, so readers are not prompted for a shared code.
- Uploading another sermon for the same service and date replaces the earlier PDF.

The in-app reader hides download controls and does not post the PDF in the Telegram chat. A reader with access could still capture screen content or retrieve the PDF from browser tools; the viewer is an access gate, not DRM.

## Storage and access notes

Attendance is queried live through the bot's existing Apps Script `action=summary` endpoint. If the webhook is unreachable, the reader fails closed and asks the member to retry. Uploaded PDFs and member links are stored under `SERMON_DATA_DIR`; deleting the Railway volume would remove them. Back up that volume if the sermon archive must be retained independently of Railway.

Member sign-up resolves against the bot's `MEMBERS` roster in `config.py`. The supplied workbook's Roster tab is not an exact match for that code roster, so reconcile the current roster before rollout; otherwise some people may not be able to link their account.
