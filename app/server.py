"""
XACT Web Builder — upload WAV files, get compiled .xwb/.xsb/.xgs back.

Auth: single-password login via ADMIN_PASSWORD env var.
"""
import hmac
import io
import os
import re
import shutil
import subprocess
import tempfile
import time
import wave
import zipfile
from datetime import timedelta
from functools import wraps

from flask import (Flask, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.utils import secure_filename

from xap_generator import generate_xap

# =====================================================================
# Config
# =====================================================================

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not ADMIN_PASSWORD:
    raise RuntimeError(
        "ADMIN_PASSWORD environment variable must be set. "
        "Add it to your docker-compose file."
    )

# Persist SECRET_KEY across container restarts so sessions survive.
# Lives in the wine prefix volume which is already persistent.
SECRET_KEY_FILE = "/wine/.flask-secret"
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "rb") as fh:
        SECRET_KEY = fh.read()
else:
    SECRET_KEY = os.urandom(32)
    os.makedirs("/wine", exist_ok=True)
    with open(SECRET_KEY_FILE, "wb") as fh:
        fh.write(SECRET_KEY)
    os.chmod(SECRET_KEY_FILE, 0o600)

# Cookie policy: assume HTTPS via reverse proxy. Override by setting
# INSECURE_COOKIES=1 if you're testing over plain HTTP locally.
INSECURE_COOKIES = os.environ.get("INSECURE_COOKIES") == "1"

# XactBld path in the wine prefix; override via env if your SDK ships
# XactBld.exe (no "3") instead of XactBld3.exe.
XACTBLD_EXE = os.environ.get(
    "XACTBLD_EXE", "/wine/drive_c/xact/XactBld3.exe"
)
XACTBLD_FALLBACK = "/wine/drive_c/xact/XactBld.exe"

WINE_ENV = {
    **os.environ,
    "WINEPREFIX": "/wine",
    "WINEARCH": "win32",
    "WINEDEBUG": "-all",
    "DISPLAY": ":99",
}

# =====================================================================
# App
# =====================================================================

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    MAX_CONTENT_LENGTH=25 * 1024 * 1024,  # 25 MB upload cap
    SESSION_COOKIE_SECURE=not INSECURE_COOKIES,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)

# Simple in-memory rate limit for login attempts.
_login_attempts = {}          # ip -> [timestamps]
_MAX_LOGIN_TRIES = 5
_LOGIN_WINDOW_SECS = 300      # 5 minutes


def _client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _prune_attempts(ip):
    now = time.time()
    _login_attempts[ip] = [
        t for t in _login_attempts.get(ip, []) if now - t < _LOGIN_WINDOW_SECS
    ]


def _record_attempt(ip):
    _login_attempts.setdefault(ip, []).append(time.time())


def _can_attempt(ip):
    _prune_attempts(ip)
    return len(_login_attempts.get(ip, [])) < _MAX_LOGIN_TRIES


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authed"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def sanitize_name(raw, default):
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", raw or "")
    return cleaned if cleaned else default


def read_wav_info(path):
    """Return (channels, sample_rate, data_length_bytes) or defaults."""
    try:
        with wave.open(path, "rb") as w:
            channels = w.getnchannels()
            rate = w.getframerate()
            nframes = w.getnframes()
            sampwidth = w.getsampwidth()
            return channels, rate, nframes * channels * sampwidth
    except Exception:
        return 2, 48000, 0


# =====================================================================
# Routes
# =====================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authed"):
        return redirect(url_for("index"))

    ip = _client_ip()
    if request.method == "POST":
        if not _can_attempt(ip):
            return (
                render_template(
                    "login.html",
                    error="Too many attempts. Try again in a few minutes.",
                ),
                429,
            )
        _record_attempt(ip)
        pw = request.form.get("password", "")
        if hmac.compare_digest(pw, ADMIN_PASSWORD):
            session.clear()
            session["authed"] = True
            session.permanent = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Wrong password."), 401

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    xactbld_ok = os.path.exists(XACTBLD_EXE) or os.path.exists(XACTBLD_FALLBACK)
    return jsonify(
        {
            "ok": xactbld_ok,
            "xactbld_path": XACTBLD_EXE if os.path.exists(XACTBLD_EXE) else (
                XACTBLD_FALLBACK if os.path.exists(XACTBLD_FALLBACK) else None
            ),
        }
    )


@app.route("/")
@require_login
def index():
    return render_template("index.html")


@app.route("/build", methods=["POST"])
@require_login
def build():
    files = request.files.getlist("waves")
    if not files or not files[0].filename:
        return jsonify(error="No WAV files uploaded"), 400
    if len(files) > 32:
        return jsonify(error="Too many files (max 32)"), 400

    bank_name = sanitize_name(request.form.get("bank_name", ""), "SoundBank")

    workdir = tempfile.mkdtemp(prefix="xact-")
    try:
        wave_entries = []
        seen_cues = set()
        for f in files:
            filename = secure_filename(f.filename or "")
            if not filename.lower().endswith(".wav"):
                return jsonify(error=f"Not a WAV file: {filename}"), 400
            f.save(os.path.join(workdir, filename))

            base = os.path.splitext(filename)[0]
            cue = sanitize_name(base, "cue")
            unique = cue
            n = 2
            while unique in seen_cues:
                unique = f"{cue}_{n}"
                n += 1
            seen_cues.add(unique)

            channels, rate, data_length = read_wav_info(
                os.path.join(workdir, filename)
            )
            wave_entries.append({
                "filename": filename,
                "cue": unique,
                "channels": channels,
                "rate": rate,
                "data_length": data_length,
            })

        xap_text = generate_xap(bank_name, wave_entries)
        xap_path = os.path.join(workdir, f"{bank_name}.xap")
        with open(xap_path, "w", encoding="utf-8") as fh:
            fh.write(xap_text)

        xactbld = XACTBLD_EXE if os.path.exists(XACTBLD_EXE) else XACTBLD_FALLBACK
        if not os.path.exists(xactbld):
            return (
                jsonify(
                    error="XactBld binary not found in wine prefix. "
                    "See README.md.",
                    tried=[XACTBLD_EXE, XACTBLD_FALLBACK],
                ),
                500,
            )

        # Pass only the basename (with cwd set to workdir). Wine handles
        # relative paths cleanly; absolute Unix paths can confuse it.
        xap_basename = f"{bank_name}.xap"
        # XactBld writes to Win\ and Xbox\ subfolders but does NOT create them.
        os.makedirs(os.path.join(workdir, "Win"), exist_ok=True)
        os.makedirs(os.path.join(workdir, "Xbox"), exist_ok=True)
        cmd = ["wine", xactbld, xap_basename, "/WINDOWS", "/R:VERBOSE"]

        try:
            proc = subprocess.run(
                cmd,
                cwd=workdir, env=WINE_ENV,
                capture_output=True, timeout=90,
            )
        except subprocess.TimeoutExpired:
            return jsonify(error="XactBld timed out after 90 seconds"), 500

        outputs = {}
        for ext in ("xwb", "xsb", "xgs"):
            for candidate_dir in ("Win", "."):
                names_to_try = (
                    [f"{bank_name}.{ext}", "GlobalSettings.xgs"]
                    if ext == "xgs"
                    else [f"{bank_name}.{ext}"]
                )
                for name in names_to_try:
                    candidate = os.path.join(workdir, candidate_dir, name)
                    if os.path.exists(candidate):
                        outputs[ext] = candidate
                        break
                if ext in outputs:
                    break

        if len(outputs) < 3:
            return (
                jsonify(
                    error="XactBld did not produce all 3 output files "
                    "(.xwb, .xsb, .xgs). See diagnostic output below.",
                    version="v6-mkdir-Win",
                    command=" ".join(cmd),
                    workdir_contents=os.listdir(workdir),
                    win_dir_contents=os.listdir(os.path.join(workdir, "Win"))
                        if os.path.isdir(os.path.join(workdir, "Win")) else "no Win dir",
                    found=list(outputs.keys()),
                    returncode=proc.returncode,
                    stdout=proc.stdout.decode("utf-8", errors="replace")[:8000],
                    stderr=proc.stderr.decode("utf-8", errors="replace")[:8000],
                    xap_content=xap_text[:8000],
                ),
                500,
            )

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for ext, path in outputs.items():
                out_name = f"{bank_name}.{ext}"
                z.write(path, out_name)
        buf.seek(0)

        return send_file(
            buf,
            as_attachment=True,
            download_name=f"{bank_name}.zip",
            mimetype="application/zip",
        )

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
