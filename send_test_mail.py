"""
send_test_mail.py — Quick test: generate email report and send it.
Mocks all expensive agents so only the email generation + sending runs.
"""
import os, sys, traceback
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("Loading environment...", flush=True)
from dotenv import load_dotenv
load_dotenv()

# ---- patch GitHub I/O to use local files ----
import backend.github_yaml_db as gh
import yaml

def _local_raw(file_path):
    p = os.path.join(".", file_path)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read(), "local_sha"
    return "", ""

def _local_yaml(file_path):
    content, _ = _local_raw(file_path)
    if content:
        try:
            return yaml.safe_load(content) or {}
        except Exception:
            pass
    return {}

gh._get_raw_file = _local_raw
gh.read_yaml_from_github = _local_yaml
gh.write_yaml_to_github = lambda p, d: True
gh.append_log_entry = lambda e: None
gh._put_raw_file = lambda p, c, s, m: None

# ---- no-op all heavy agents ----
import backend.agents.execution_agent as ea

def _noop(*a, **k): return None

ea.run_career_agent              = _noop
ea.run_interview_feedback_agent  = _noop
ea.run_skill_agent               = _noop
ea.run_repo_security_scanner_agent = _noop
ea.run_auto_fix_pr_agent         = _noop
ea.run_portfolio_builder_agent   = _noop
ea.run_porsche_portfolio_agent   = _noop
ea.run_resume_optimization_agent = _noop
ea.run_auto_apply_agent          = _noop
ea.run_opportunity_matching_agent = _noop
ea.run_career_strategy_agent     = _noop
ea.run_career_readiness_agent    = _noop
ea.run_career_analytics_agent    = lambda: os.getenv("RENDER_EXTERNAL_URL", "https://orchestrai-agent.onrender.com") + "/analytics"
ea.run_interview_coach_agent     = _noop

# Also no-op scraper if referenced
try:
    import backend.agents.internship_scraper_agent as isa
    isa.scrape_jobs = _noop
    isa.remove_expired_jobs = _noop
    ea.scrape_jobs = _noop
    ea.remove_expired_jobs = _noop
except Exception:
    pass

print("Generating email HTML from local YAML files...", flush=True)
try:
    ea.run_orchestrai_pipeline()
    print("✅ Email sent successfully!", flush=True)
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    traceback.print_exc()
