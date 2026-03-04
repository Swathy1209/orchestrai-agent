"""
main.py — OrchestrAI Career Agent Entry Point
Runs on Render as a FastAPI Web Service.

Flow:
  Render Env Vars  →  FastAPI + Scheduler  →  Gmail email
"""

import logging
import os
import sys
import threading
import traceback

from dotenv import load_dotenv

load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("OrchestrAI")

# ── Entry point ───────────────────────────────────────────────────────────────
def run_full_pipeline():
    from backend.agents.execution_agent import run_orchestrai_pipeline
    try:
        run_orchestrai_pipeline()
    except Exception as exc:
        logger.error("Pipeline CRASHED: %s", traceback.format_exc())

# ── FastAPI Web Server Setup ───────────────────────────────────────────────
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI(title="OrchestrAI Dashboard", description="OrchestrAI Autonomous Career Intelligence System.")

# ── Determine writable DATA_DIR ───────────────────────────────────────────────
DATA_DIR = os.getenv("DATA_DIR", ".")
STATIC_DIRS = [
    "database",
    "application_packages",
    "frontend/practice",
    "frontend/portfolio",
    "optimized_resumes",
    "cover_letters",
]

for _d in STATIC_DIRS:
    _path = os.path.join(DATA_DIR, _d)
    try:
        os.makedirs(_path, exist_ok=True)
    except PermissionError:
        logger.warning("Permission denied: '%s'. Falling back to './data'", _path)
        DATA_DIR = "./data"
        os.makedirs(os.path.join(DATA_DIR, _d), exist_ok=True)

# Seed each directory with a placeholder so StaticFiles doesn't crash
for _d in STATIC_DIRS:
    _placeholder = os.path.join(DATA_DIR, _d, ".keep")
    if not os.path.exists(_placeholder):
        try:
            with open(_placeholder, "w") as f:
                f.write("")
        except Exception:
            pass

# ── Mount static directories (safe — all dirs guaranteed to exist) ──────────
def _safe_mount(route, directory, name, html=False):
    try:
        kwargs = {"html": html} if html else {}
        app.mount(route, StaticFiles(directory=directory, **kwargs), name=name)
        logger.info("Mounted static dir: %s -> %s", route, directory)
    except Exception as exc:
        logger.warning("Could not mount %s: %s", route, exc)

_safe_mount("/database",            os.path.join(DATA_DIR, "database"),             "database")
_safe_mount("/application_packages", os.path.join(DATA_DIR, "application_packages"), "application_packages")
_safe_mount("/frontend/practice",   os.path.join(DATA_DIR, "frontend/practice"),    "practice")
_safe_mount("/portfolio",           os.path.join(DATA_DIR, "frontend/portfolio"),   "portfolio", html=True)
_safe_mount("/optimized_resumes",   os.path.join(DATA_DIR, "optimized_resumes"),    "optimized_resumes")
_safe_mount("/cover_letters",       os.path.join(DATA_DIR, "cover_letters"),        "cover_letters")

@app.on_event("startup")
def start_scheduler():
    try:
        from backend.scheduler import schedule_daily_internship_email, run_once_now

        if os.getenv("RUN_ON_STARTUP", "false").lower() == "true":
            logger.info("Startup trigger: running full pipeline immediately in background...")
            t = threading.Thread(target=run_full_pipeline, daemon=True)
            t.start()

        logger.info("Starting scheduler: full pipeline will run daily at 9:30 AM IST.")
        schedule_daily_internship_email(run_full_pipeline, hour=9, minute=30)
    except Exception as exc:
        logger.error("Scheduler startup failed: %s", exc)

@app.get("/", response_class=HTMLResponse)
def index():
    eu = os.getenv("EMAIL_USER", "NOT SET")
    er = os.getenv("EMAIL_RECEIVER", "NOT SET")
    ep = "✅ SET" if os.getenv("EMAIL_PASS") else "❌ NOT SET"
    return f"""
    <html><head><title>OrchestrAI Dashboard</title></head>
    <body style='font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px'>
      <h1>🤖 OrchestrAI Career Intelligence System</h1>
      <p>Your autonomous AI career agent is running on Render.</p>
      <hr/>
      <h3>⚙️ Email Configuration</h3>
      <ul>
        <li><b>EMAIL_USER:</b> {eu}</li>
        <li><b>EMAIL_RECEIVER:</b> {er}</li>
        <li><b>EMAIL_PASS:</b> {ep}</li>
      </ul>
      <hr/>
      <h3>🔧 Actions</h3>
      <p><a href='/test-email' style='background:#4CAF50;color:white;padding:10px 20px;border-radius:5px;text-decoration:none'>✉️ Test Email Now</a></p>
      <p><a href='/trigger' style='background:#2196F3;color:white;padding:10px 20px;border-radius:5px;text-decoration:none'>🚀 Run Pipeline (background)</a></p>
      <p><a href='/trigger-sync' style='background:#FF9800;color:white;padding:10px 20px;border-radius:5px;text-decoration:none'>🔍 Run Pipeline (with error display)</a></p>
    </body></html>
    """

@app.get("/trigger", response_class=HTMLResponse)
def trigger_pipeline(background_tasks: BackgroundTasks):
    logger.info("Manual HTTP trigger: running full pipeline in background...")
    background_tasks.add_task(run_full_pipeline)
    return "<h1>Pipeline Triggered! 🚀</h1><p>The AI agents are running in the background. The email will arrive in your inbox in ~10 minutes.</p><p><a href='/'>← Back to Dashboard</a></p>"

@app.get("/trigger-sync", response_class=HTMLResponse)
def trigger_pipeline_sync():
    """Runs the full pipeline synchronously and shows any errors in browser."""
    logger.info("Sync HTTP trigger: running full pipeline synchronously...")
    try:
        run_full_pipeline()
        return "<h1>Pipeline Completed ✅</h1><p>All agents ran successfully. Check your inbox!</p><p><a href='/'>← Back to Dashboard</a></p>"
    except Exception as e:
        err = traceback.format_exc()
        logger.error("Sync trigger FAILED: %s", err)
        return f"<h1>Pipeline FAILED ❌</h1><pre style='color:red;background:#ffeaea;padding:20px'>{err}</pre>"

@app.get("/test-email", response_class=HTMLResponse)
def test_email_endpoint():
    """Send a quick test email to verify SMTP credentials are working."""
    import smtplib
    from email.message import EmailMessage
    eu = os.getenv("EMAIL_USER", "")
    ep = os.getenv("EMAIL_PASS", "")
    er = os.getenv("EMAIL_RECEIVER", eu)
    sh = os.getenv("SMTP_HOST", "smtp.gmail.com")
    sp = int(os.getenv("SMTP_PORT", 587))

    if not eu or eu in ("your-gmail@gmail.com", ""):
        return f"<h1>❌ Email Not Configured</h1><p><b>EMAIL_USER</b> is not set or is still the placeholder value.</p><p>Go to your <b>Render Dashboard → Environment</b> and set EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER.</p>"

    if not ep or ep in ("xxxx-xxxx-xxxx-xxxx", ""):
        return f"<h1>❌ App Password Not Set</h1><p><b>EMAIL_PASS</b> is not set or is still the placeholder value.</p><p>Generate a Gmail App Password at: <a href='https://myaccount.google.com/apppasswords'>myaccount.google.com/apppasswords</a></p>"

    try:
        msg = EmailMessage()
        msg["Subject"] = "OrchestrAI Test Email 🚀"
        msg["From"] = eu
        msg["To"] = er
        msg.set_content("This is a test email from OrchestrAI. SMTP is working correctly!")
        with smtplib.SMTP(sh, sp) as server:
            server.starttls()
            server.login(eu, ep)
            server.send_message(msg)
        return f"<h1>✅ Test Email Sent!</h1><p>Successfully sent a test email to <b>{er}</b>. Check your inbox now!</p><p><a href='/trigger'>Now run the full pipeline →</a></p>"
    except Exception as e:
        return f"<h1>❌ Email Failed</h1><p style='color:red'><b>Error:</b> {e}</p><p>Common fixes:</p><ul><li>Make sure 2-Step Verification is enabled on your Google account</li><li>Generate an App Password at <a href='https://myaccount.google.com/apppasswords'>myaccount.google.com/apppasswords</a></li><li>Use the 16-character App Password (not your regular Gmail password)</li></ul>"

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        logger.info("Manual trigger: running full pipeline immediately...")
        from backend.scheduler import run_once_now
        run_once_now(run_full_pipeline)
    else:
        import uvicorn
        port = int(os.environ.get("PORT", "10000"))
        logger.info(f"Starting Uvicorn on 0.0.0.0:{port}")
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
