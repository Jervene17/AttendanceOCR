"""Attendance-gated sermon storage and the Telegram Mini App reader.

Persistent state is held in SERMON_DATA_DIR (mount a Railway Volume there).
The original sermon PDFs are kept outside the public web root and are streamed
only after Telegram Web App identity and attendance have both been checked.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web


DATA_DIR = Path(os.getenv("SERMON_DATA_DIR", "data")).resolve()
SERMON_DIR = DATA_DIR / "sermons"
DB_PATH = DATA_DIR / "sermon_portal.sqlite3"
MAX_PDF_BYTES = 10 * 1024 * 1024
UNMATCHED_MEMBER_ID = "__unmatched__"
TOKEN_TTL_SECONDS = 10 * 60
_reader_tokens: dict[str, tuple[int, str, float]] = {}
_attendance_checker = None


def initialize_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SERMON_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS member_links (
            telegram_id INTEGER PRIMARY KEY,
            member_id TEXT NOT NULL,
            member_name TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','approved','denied')),
            requested_at TEXT NOT NULL,
            approved_by INTEGER,
            approved_at TEXT
        )""")
        db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS one_approved_link_per_member
            ON member_links(member_id) WHERE status='approved'""")
        db.execute("""CREATE TABLE IF NOT EXISTS sermons (
            sermon_id TEXT PRIMARY KEY,
            service TEXT NOT NULL CHECK(service IN ('Sunday','Wednesday')),
            service_date TEXT NOT NULL,
            title TEXT NOT NULL,
            file_name TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(service, service_date)
        )""")


def set_attendance_checker(checker) -> None:
    global _attendance_checker
    _attendance_checker = checker


def _connect():
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    return db


def get_member_link(telegram_id: int):
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM member_links WHERE telegram_id=? AND status='approved'",
            (int(telegram_id),),
        ).fetchone()
        return dict(row) if row else None


def get_link_for_user(telegram_id: int):
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM member_links WHERE telegram_id=?", (int(telegram_id),)
        ).fetchone()
        return dict(row) if row else None


def submit_link_request(telegram_id: int, member_id: str, member_name: str):
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        existing = db.execute(
            "SELECT status, member_name FROM member_links WHERE telegram_id=?",
            (int(telegram_id),),
        ).fetchone()
        if existing and existing["status"] == "approved":
            return "already_approved", existing["member_name"]
        if existing and existing["status"] == "pending":
            return "already_pending", existing["member_name"]
        db.execute(
            """INSERT INTO member_links
               (telegram_id, member_id, member_name, status, requested_at,
                approved_by, approved_at)
               VALUES (?, ?, ?, 'pending', ?, NULL, NULL)
               ON CONFLICT(telegram_id) DO UPDATE SET
                 member_id=excluded.member_id,
                 member_name=excluded.member_name,
                 status='pending', requested_at=excluded.requested_at,
                 approved_by=NULL, approved_at=NULL""",
            (int(telegram_id), member_id, member_name, now),
        )
    return "submitted", member_name


def pending_link_requests(limit: int = 30):
    with _connect() as db:
        rows = db.execute(
            "SELECT * FROM member_links WHERE status='pending' "
            "ORDER BY requested_at LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def assign_pending_link_member(telegram_id: int, member_id: str, member_name: str):
    """Attach an unmatched signup to a roster entry, leaving approval explicit."""
    with _connect() as db:
        cursor = db.execute(
            """UPDATE member_links SET member_id=?, member_name=?
               WHERE telegram_id=? AND status='pending' AND member_id=?""",
            (str(member_id), str(member_name), int(telegram_id), UNMATCHED_MEMBER_ID),
        )
        if cursor.rowcount != 1:
            return None
        row = db.execute(
            "SELECT * FROM member_links WHERE telegram_id=?", (int(telegram_id),)
        ).fetchone()
        return dict(row) if row else None


def approve_link_request(telegram_id: int, organizer_id: int):
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM member_links WHERE telegram_id=? AND status='pending'",
            (int(telegram_id),),
        ).fetchone()
        if not row:
            return None, "This request is no longer pending."
        if row["member_id"] == UNMATCHED_MEMBER_ID:
            return None, "Match this signup to a roster member before approving it."
        linked = db.execute(
            "SELECT telegram_id FROM member_links "
            "WHERE member_id=? AND status='approved'",
            (row["member_id"],),
        ).fetchone()
        if linked and int(linked["telegram_id"]) != int(telegram_id):
            return None, "That roster member is already linked to another Telegram account."
        db.execute(
            "UPDATE member_links SET status='approved', approved_by=?, approved_at=? "
            "WHERE telegram_id=?",
            (int(organizer_id), now, int(telegram_id)),
        )
        return dict(row), None


def deny_link_request(telegram_id: int):
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM member_links WHERE telegram_id=? AND status='pending'",
            (int(telegram_id),),
        ).fetchone()
        if not row:
            return None
        db.execute(
            "UPDATE member_links SET status='denied' WHERE telegram_id=?",
            (int(telegram_id),),
        )
        return dict(row)


def save_sermon(source_path: str | Path, service: str, service_date: str,
                title: str, uploaded_by: int):
    service = service.strip().title()
    if service not in ("Sunday", "Wednesday"):
        raise ValueError("Service must be Sunday or Wednesday.")
    datetime.strptime(service_date, "%Y-%m-%d")
    title = title.strip()
    if not title or len(title) > 160:
        raise ValueError("Title must contain 1 to 160 characters.")
    source = Path(source_path)
    if source.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("PDF is larger than the 10 MB upload limit.")
    with source.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("The uploaded file does not look like a PDF.")

    sermon_id = secrets.token_hex(12)
    file_name = f"{sermon_id}.pdf"
    destination = SERMON_DIR / file_name
    old_file = None
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        old = db.execute(
            "SELECT file_name FROM sermons WHERE service=? AND service_date=?",
            (service, service_date),
        ).fetchone()
        if old:
            old_file = SERMON_DIR / old["file_name"]
        os.replace(source, destination)
        db.execute(
            """INSERT INTO sermons
               (sermon_id, service, service_date, title, file_name, uploaded_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(service, service_date) DO UPDATE SET
                 sermon_id=excluded.sermon_id, title=excluded.title,
                 file_name=excluded.file_name, uploaded_by=excluded.uploaded_by,
                 created_at=excluded.created_at""",
            (sermon_id, service, service_date, title, file_name, int(uploaded_by), now),
        )
    if old_file and old_file != destination:
        old_file.unlink(missing_ok=True)
    return get_sermon(sermon_id)


def get_sermon(sermon_id: str):
    with _connect() as db:
        row = db.execute("SELECT * FROM sermons WHERE sermon_id=?", (sermon_id,)).fetchone()
        return dict(row) if row else None


def list_sermons():
    with _connect() as db:
        rows = db.execute(
            "SELECT sermon_id, service, service_date, title FROM sermons "
            "ORDER BY service_date DESC, service DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def _validate_init_data(init_data: str, bot_token: str):
    if not isinstance(init_data, str) or not init_data or len(init_data) > 8192:
        return None
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = fields.pop("hash", None)
    if not received_hash:
        return None
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        return None
    try:
        auth_date = int(fields["auth_date"])
        user = json.loads(fields["user"])
        if time.time() - auth_date > 24 * 60 * 60 or auth_date > time.time() + 60:
            return None
        user_id = int(user["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return user_id


def _json_error(status: int, message: str):
    return web.json_response({"ok": False, "message": message}, status=status,
                             headers={"Cache-Control": "no-store"})


def _app_html() -> str:
    return r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>Sermon messages</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root{color-scheme:light dark;font-family:Arial,sans-serif}*{box-sizing:border-box}body{margin:0;background:var(--tg-theme-bg-color,#fff);color:var(--tg-theme-text-color,#222);font-size:16px}.wrap{max-width:760px;margin:auto;padding:18px 16px 42px}.top{display:flex;align-items:center;justify-content:space-between;gap:12px}.muted{color:var(--tg-theme-hint-color,#777);font-size:14px}.card{padding:15px 0;border-bottom:1px solid var(--tg-theme-hint-color,#ddd)}button{font:inherit;color:var(--tg-theme-button-text-color,#fff);background:var(--tg-theme-button-color,#2878d0);border:0;border-radius:9px;padding:11px 14px;min-height:42px}button.secondary{color:var(--tg-theme-text-color,#222);background:var(--tg-theme-secondary-bg-color,#eee)}button:disabled{opacity:.55}.row{display:flex;gap:8px;align-items:center}.reader{display:none}.controls{position:sticky;top:0;background:var(--tg-theme-bg-color,#fff);padding:8px 0;z-index:2;display:flex;justify-content:space-between;align-items:center}.pages{display:flex;flex-direction:column;gap:10px}canvas{display:block;width:100%;height:auto;background:#fff;box-shadow:0 1px 6px #8885}.status{padding:18px 0}.empty{padding:28px 8px;text-align:center}
</style></head><body><main class="wrap"><section id="library"><div class="top"><div><h2 style="margin:0">Sermon messages</h2><div id="member" class="muted"></div></div><button id="refresh" class="secondary">Refresh</button></div><div id="status" class="status">Loading your access…</div><div id="sermons"></div></section><section id="reader" class="reader"><div class="top"><div><button id="back" class="secondary">← Messages</button><div id="readTitle" class="muted"></div></div></div><div class="controls"><button id="prev" class="secondary">Previous</button><span id="pageLabel" class="muted"></span><button id="next" class="secondary">Next</button></div><div id="pages" class="pages"></div><div class="muted" style="padding-top:12px">Reader view. Access is limited to sermons for services recorded for your linked account.</div></section></main>
<script type="module">
const tg=window.Telegram?.WebApp;const statusEl=document.querySelector('#status');const listEl=document.querySelector('#sermons');let pdfDoc=null,pageNum=1,scale=1.25;
if(!tg||!tg.initData){statusEl.textContent='Please open this page from the Telegram bot.';}else{tg.ready();tg.expand();loadLibrary();}
async function api(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({initData:tg.initData,...data}),cache:'no-store'});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.message||'Could not complete that request.');return d}
async function loadLibrary(){document.querySelector('#reader').style.display='none';document.querySelector('#library').style.display='block';listEl.replaceChildren();statusEl.textContent='Loading your access…';try{const d=await api('/api/library',{});document.querySelector('#member').textContent='Linked account: '+d.memberName;statusEl.textContent=d.sermons.length?'Choose a message to check access and read it.':'No sermons have been uploaded yet.';for(const s of d.sermons){const card=document.createElement('div');card.className='card';const left=document.createElement('div');const title=document.createElement('strong');title.textContent=s.title;const meta=document.createElement('div');meta.className='muted';meta.textContent=s.service+' · '+s.service_date;left.append(title,meta);const b=document.createElement('button');b.textContent='Read';b.onclick=()=>openSermon(s,b);const row=document.createElement('div');row.className='top';row.append(left,b);card.append(row);listEl.append(card)}}catch(e){statusEl.textContent=e.message}}
async function openSermon(s,b){b.disabled=true;try{statusEl.textContent='';const d=await api('/api/read',{sermonId:s.sermon_id});document.querySelector('#library').style.display='none';document.querySelector('#reader').style.display='block';document.querySelector('#readTitle').textContent=s.title+' · '+s.service_date;const pdfjs=await import('https://unpkg.com/pdfjs-dist@4.10.38/build/pdf.min.mjs');pdfjs.GlobalWorkerOptions.workerSrc='https://unpkg.com/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs';pdfDoc=await pdfjs.getDocument({url:d.pdfUrl,withCredentials:false}).promise;pageNum=1;await preparePages(pdfjs)}catch(e){statusEl.textContent=e.message;alert(e.message)}finally{b.disabled=false}}
async function preparePages(pdfjs){const host=document.querySelector('#pages');host.replaceChildren();const observer=new IntersectionObserver(async entries=>{for(const entry of entries){const slot=entry.target;const n=Number(slot.dataset.page);if(entry.isIntersecting){if(slot.dataset.rendered==='1'||slot.dataset.busy==='1')continue;slot.dataset.busy='1';try{const page=await pdfDoc.getPage(n);const base=page.getViewport({scale:1});const dpr=Math.min(window.devicePixelRatio||1,2);const pxScale=1.33*(slot.clientWidth/base.width)*dpr;const viewport=page.getViewport({scale:pxScale});const canvas=document.createElement('canvas');canvas.dataset.page=String(n);canvas.style.width='100%';canvas.style.height='100%';canvas.width=viewport.width;canvas.height=viewport.height;slot.replaceChildren(canvas);const task=page.render({canvasContext:canvas.getContext('2d'),viewport});slot._task=task;await task.promise;slot.dataset.rendered='1'}catch(e){if(e?.name!=='RenderingCancelledException')console.error('Page render failed')}finally{slot.dataset.busy='0'}}else if(slot.dataset.rendered==='1'){if(slot._task){try{slot._task.cancel()}catch{}}slot.replaceChildren();slot.dataset.rendered='0'}}updateCurrentPage()},{rootMargin:'180% 0px'});for(let n=1;n<=pdfDoc.numPages;n++){const slot=document.createElement('div');slot.dataset.page=String(n);slot.dataset.rendered='0';slot.style.position='relative';slot.style.width='100%';slot.style.aspectRatio='612 / 792';slot.style.background='#eee';host.append(slot);observer.observe(slot)}host._observer=observer;updatePageLabel()}
function updateCurrentPage(){const slots=[...document.querySelector('#pages').children];if(!slots.length)return;let best=slots[0],distance=Infinity;for(const slot of slots){const d=Math.abs(slot.getBoundingClientRect().top-100);if(d<distance){distance=d;best=slot}}pageNum=Number(best.dataset.page);updatePageLabel()}
function updatePageLabel(){document.querySelector('#pageLabel').textContent=pdfDoc?'Page '+pageNum+' of '+pdfDoc.numPages:'';document.querySelector('#prev').disabled=pageNum<=1;document.querySelector('#next').disabled=!pdfDoc||pageNum>=pdfDoc.numPages}
document.querySelector('#refresh').onclick=loadLibrary;document.querySelector('#back').onclick=loadLibrary;document.querySelector('#prev').onclick=()=>{pageNum=Math.max(1,pageNum-1);document.querySelector(`#pages [data-page="${pageNum}"]`)?.scrollIntoView({behavior:'smooth',block:'start'});updatePageLabel()};document.querySelector('#next').onclick=()=>{pageNum=Math.min(pdfDoc.numPages,pageNum+1);document.querySelector(`#pages [data-page="${pageNum}"]`)?.scrollIntoView({behavior:'smooth',block:'start'});updatePageLabel()};document.querySelector('#pages').addEventListener('scroll',updateCurrentPage);window.addEventListener('scroll',updateCurrentPage,{passive:true});
document.addEventListener('contextmenu',e=>e.preventDefault());
</script></body></html>"""


def create_web_app(bot_token: str, attendance_checker):
    initialize_storage()
    set_attendance_checker(attendance_checker)
    app = web.Application(client_max_size=1024 * 1024)

    def current_user(request, body):
        if not isinstance(body, dict):
            return None
        user_id = _validate_init_data(body.get("initData", ""), bot_token)
        return user_id

    async def index(_request):
        return web.Response(text=_app_html(), content_type="text/html", headers={
            "Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        })

    async def health(_request):
        return web.json_response({"status": "ok"}, headers={"Cache-Control": "no-store"})

    async def library(request):
        try:
            body = await request.json()
        except (json.JSONDecodeError, web.HTTPException):
            return _json_error(400, "Invalid request.")
        user_id = current_user(request, body)
        if not user_id:
            return _json_error(401, "Telegram could not verify this session. Reopen the library from the bot.")
        link = get_member_link(user_id)
        if not link:
            return _json_error(403, "Your Telegram account is not linked yet. Use /signup in the bot and ask an organizer to approve it.")
        return web.json_response({"ok": True, "memberName": link["member_name"],
                                  "sermons": list_sermons()},
                                 headers={"Cache-Control": "no-store"})

    async def read_sermon(request):
        try:
            body = await request.json()
        except (json.JSONDecodeError, web.HTTPException):
            return _json_error(400, "Invalid request.")
        user_id = current_user(request, body)
        if not user_id:
            return _json_error(401, "Telegram session expired. Reopen the library from the bot.")
        if not get_member_link(user_id):
            return _json_error(403, "Your Telegram account is not linked. Use /signup first.")
        sermon_id = str(body.get("sermonId", ""))
        sermon = get_sermon(sermon_id)
        if not sermon:
            return _json_error(404, "That sermon is no longer available.")
        if _attendance_checker is None:
            return _json_error(503, "Attendance access checking is not configured.")
        try:
            allowed = await _attendance_checker(user_id, sermon)
        except Exception:
            return _json_error(503, "Could not check attendance right now. Please try again shortly.")
        if not allowed:
            return _json_error(403, "Attendance for this service is not recorded under your linked account.")
        token = secrets.token_urlsafe(32)
        _reader_tokens[token] = (user_id, sermon_id, time.time() + TOKEN_TTL_SECONDS)
        return web.json_response({"ok": True, "pdfUrl": f"/api/pdf/{sermon_id}?token={token}"},
                                 headers={"Cache-Control": "no-store"})

    async def pdf_file(request):
        sermon_id = request.match_info["sermon_id"]
        if not re.fullmatch(r"[a-f0-9]{24}", sermon_id):
            raise web.HTTPNotFound()
        token = request.query.get("token", "")
        token_record = _reader_tokens.get(token)
        if not token_record or token_record[1] != sermon_id or token_record[2] < time.time():
            _reader_tokens.pop(token, None)
            raise web.HTTPForbidden(text="Reader authorization expired. Reopen the sermon from Telegram.")
        _user_id, _sermon_id, expiry = token_record
        _reader_tokens[token] = (_user_id, _sermon_id, min(expiry, time.time() + TOKEN_TTL_SECONDS))
        sermon = get_sermon(sermon_id)
        if not sermon:
            raise web.HTTPNotFound()
        path = SERMON_DIR / sermon["file_name"]
        if not path.is_file():
            raise web.HTTPNotFound(text="Sermon file is missing.")
        return web.FileResponse(path, headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'inline; filename="{sermon_id}.pdf"',
            "Cache-Control": "private, no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        })

    app.router.add_get("/", lambda _request: web.HTTPFound("/app"))
    app.router.add_get("/healthz", health)
    app.router.add_get("/app", index)
    app.router.add_post("/api/library", library)
    app.router.add_post("/api/read", read_sermon)
    app.router.add_get("/api/pdf/{sermon_id}", pdf_file)
    return app


def store_directory() -> Path:
    initialize_storage()
    return SERMON_DIR
