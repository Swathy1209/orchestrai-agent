"""
per_internship_portfolio_agent.py — Per-Internship Portfolio Generator
OrchestrAI Autonomous Multi-Agent System

Generates a customized single-page portfolio for EACH internship,
highlighting the most relevant GitHub projects based on the job's
technical requirements.
"""

from __future__ import annotations
import logging
import os
import re
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from backend.github_yaml_db import (
    read_yaml_from_github,
    write_yaml_to_github,
    append_log_entry,
    _get_raw_file,
    _put_raw_file,
)

load_dotenv()
logger = logging.getLogger("OrchestrAI.PerInternshipPortfolioAgent")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
openai_client = OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL, max_retries=0) if GEMINI_API_KEY else None

JOBS_FILE = "database/jobs.yaml"
PORTFOLIO_FILE = "database/portfolio.yaml"
USERS_FILE = "database/users.yaml"
PER_INTERNSHIP_INDEX_FILE = "database/per_internship_portfolios.yaml"

DEFAULT_USER_NAME = "Swathy G"
DEFAULT_SKILLS = ["Python", "Machine Learning", "Data Analysis", "SQL", "TensorFlow", "scikit-learn", "FastAPI", "NLP"]

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:40]

def _rank_projects_for_job(projects: list[dict], job_skills: list[str]) -> list[dict]:
    """Score and rank projects by relevance to job's required skills."""
    job_skill_set = {s.lower() for s in job_skills}
    scored = []
    for project in projects:
        # Match against title, summary, and technologies string
        title = project.get("title", project.get("original_name", "")).lower()
        summary = str(project.get("summary", "")).lower()
        tech_str = str(project.get("technologies", "")).lower()
        
        score = 0
        matched = []
        for skill in job_skill_set:
            if skill in title or skill in summary:
                score += 3
                matched.append(skill)
            elif skill in tech_str:
                score += 2
                matched.append(skill)
        
        scored.append({**project, "_relevance_score": score, "_matched_skills": list(set(matched))})
    
    scored.sort(key=lambda x: x["_relevance_score"], reverse=True)
    return scored

def _generate_portfolio_html(
    company: str, role: str, job_skills: list[str],
    projects: list[dict], user_name: str, user_skills: list[str],
    skill_gaps: list[str], roadmap_steps: list[str],
    cover_letter_link: str
) -> str:
    """Generate a full-page customized portfolio HTML for one internship (Premium 9-Section Design)."""
    
    # 1. Top 4 most relevant projects
    ranked = _rank_projects_for_job(projects, job_skills)[:4]

    projects_html = ""
    for p in ranked:
        name = p.get("title", p.get("original_name", "Project"))
        desc = p.get("summary") or "A complex technical project demonstrating deep engineering."
        techs = str(p.get("technologies") or "Python, Machine Learning")
        stars = p.get("stars") or 0
        url = p.get("github_link") or "#"
        demo = p.get("demo_link")
        matched = p.get("_matched_skills", [])
        
        tags_html = "".join(
            f'<span class="skill-tag">✓ {skill.title()}</span> ' 
            for skill in matched[:4]
        )

        demo_btn = f'<a href="{demo}" target="_blank" class="btn btn-secondary">Live Demo</a>' if demo and demo != "#" else ""
        projects_html += f"""
        <div class="project-card">
            <div class="project-header">
                <h3>{name}</h3>
                <span class="star-badge">⭐ {stars}</span>
            </div>
            <p class="project-desc">{desc}</p>
            <p class="project-tech"><b>Tech Stack:</b> {techs}</p>
            <div class="project-tags">{tags_html}</div>
            <div class="project-actions">
                <a href="{url}" target="_blank" class="btn btn-outline">GitHub Repository &rarr;</a>
                {demo_btn}
            </div>
        </div>
        """

    gap_items = "".join(f"<li class='list-item error'><span class='icon'>x</span><span>{g}</span></li>" for g in (skill_gaps or ["All required skills covered!"]))
    road_items = "".join(f"<li class='list-item primary'><span class='icon'>&rarr;</span><span>{r}</span></li>" for r in (roadmap_steps[:5] or ["Keep building impactful projects!"]))
    skill_badges = "".join(f'<span class="badge">{s}</span>' for s in user_skills[:12])
    required_skills_html = "".join(f'<span class="badge badge-accent fade-in">{s.title()}</span>' for s in job_skills[:8])
    ts = datetime.now(timezone.utc).strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{user_name} — Candidate Dossier for {company}</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet"/>
<style>
  :root {{
    --bg-main: #0a0a0a;
    --surface: rgba(255, 255, 255, 0.04);
    --surface-hover: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.1);
    --primary: #E10600; /* Porsche Red emphasis */
    --accent: #3b82f6; 
    --text-main: #f8fafc;
    --text-dim: #94a3b8;
    --succ: #10b981;
    --warn: #eab308;
    --font-heading: 'Plus Jakarta Sans', sans-serif;
    --font-body: 'Plus Jakarta Sans', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }}
  
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  
  body {{ 
      font-family: var(--font-body); 
      background-color: var(--bg-main); 
      color: var(--text-main); 
      line-height: 1.6;
      background-image: 
        radial-gradient(circle at top left, rgba(225, 6, 0, 0.05), transparent 40%),
        radial-gradient(circle at bottom right, rgba(59, 130, 246, 0.05), transparent 40%);
      background-attachment: fixed;
  }}

  /* Animations */
  @keyframes fadeInUp {{
      from {{ opacity: 0; transform: translateY(20px); }}
      to {{ opacity: 1; transform: translateY(0); }}
  }}
  .animate-section {{ animation: fadeInUp 0.6s ease-out forwards; opacity: 0; }}
  
  /* Layout */
  .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}
  
  /* Section 1: Hero Dossier */
  .hero-dossier {{
      padding: 100px 20px;
      text-align: center;
      border-bottom: 1px solid var(--border);
      position: relative;
      background: radial-gradient(circle at top, rgba(255,255,255,0.03) 0%, transparent 70%);
  }}
  .hero-tag {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 2px;
      padding: 4px 12px;
      border: 1px solid rgba(225, 6, 0, 0.3);
      border-radius: 4px;
      margin-bottom: 24px;
      background: rgba(225, 6, 0, 0.05);
  }}
  .hero-dossier h1 {{
      font-size: 4rem;
      font-weight: 800;
      letter-spacing: -2px;
      margin-bottom: 16px;
      background: linear-gradient(180deg, #ffffff 0%, #a1a1aa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
  }}
  .hero-dossier h2 {{
      font-size: 1.5rem;
      font-weight: 400;
      color: var(--text-dim);
      max-width: 700px;
      margin: 0 auto 32px auto;
  }}
  .hero-dossier strong {{ color: #fff; font-weight: 600; }}

  /* Shared Card Styles */
  .section-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 40px;
      margin-bottom: 32px;
      backdrop-filter: blur(12px);
      box-shadow: 0 4px 24px rgba(0,0,0,0.2);
  }}
  .section-title {{
      font-size: 1.75rem;
      font-weight: 700;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 12px;
      color: #fff;
  }}
  
  /* Badges & Tags */
  .badge-container {{ display: flex; flex-wrap: wrap; gap: 10px; }}
  .badge {{
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 500;
      color: var(--text-main);
  }}
  .badge-accent {{
      background: rgba(59, 130, 246, 0.1);
      border-color: rgba(59, 130, 246, 0.3);
      color: #60a5fa;
  }}

  /* Project Grid */
  .project-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
  }}
  .project-card {{
      background: rgba(0,0,0,0.3);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      transition: all 0.3s ease;
  }}
  .project-card:hover {{
      transform: translateY(-4px);
      border-color: rgba(255,255,255,0.2);
      background: rgba(255,255,255,0.02);
  }}
  .project-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
  .project-header h3 {{ font-size: 1.25rem; font-weight: 700; color: #fff; }}
  .star-badge {{ background: rgba(255,255,255,0.08); padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-family: var(--font-mono); }}
  .project-desc {{ color: var(--text-dim); font-size: 0.95rem; margin-bottom: 16px; min-height: 44px; }}
  .project-tech {{ font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); margin-bottom: 16px; }}
  .project-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; }}
  .skill-tag {{
      background: rgba(16, 185, 129, 0.1);
      color: var(--succ);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
  }}
  .project-actions {{ display: flex; gap: 12px; border-top: 1px solid var(--border); padding-top: 16px; }}
  
  /* Buttons */
  .btn {{
      display: inline-block;
      padding: 10px 20px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.9rem;
      text-decoration: none;
      transition: all 0.2s;
      cursor: pointer;
  }}
  .btn-primary {{
      background: var(--primary);
      color: #fff;
      box-shadow: 0 4px 14px rgba(225, 6, 0, 0.4);
  }}
  .btn-primary:hover {{ background: #ff1a1a; transform: translateY(-2px); }}
  .btn-secondary {{ background: #fff; color: #000; }}
  .btn-secondary:hover {{ background: #e2e8f0; }}
  .btn-outline {{ border: 1px solid var(--border); color: #fff; }}
  .btn-outline:hover {{ background: rgba(255,255,255,0.1); }}

  /* Lists */
  .list-wrapper {{ list-style: none; display: flex; flex-direction: column; gap: 12px; }}
  .list-item {{ display: flex; gap: 12px; font-size: 0.95rem; align-items: flex-start; }}
  .list-item .icon {{ font-weight: 700; }}
  .list-item.error .icon {{ color: var(--primary); }}
  .list-item.primary .icon {{ color: var(--accent); }}

  /* Footer */
  .footer {{ text-align: center; padding: 40px; border-top: 1px solid var(--border); color: var(--text-dim); font-size: 0.85rem; font-family: var(--font-mono); }}

  @media(max-width: 768px) {{
      .project-grid {{ grid-template-columns: 1fr; }}
      .hero-dossier h1 {{ font-size: 2.5rem; }}
      .section-card {{ padding: 24px; }}
  }}
</style>
</head>
<body>

<!-- Section 1: Hero Dossier -->
<div class="hero-dossier animate-section" style="animation-delay: 0.1s">
    <div class="hero-tag">CONFIDENTIAL DOSSIER • EXPORTED {ts}</div>
    <h1>{user_name}</h1>
    <h2>Candidate Portfolio specifically tailored for <strong>{role}</strong> at <strong>{company}</strong></h2>
    <div style="display:flex; justify-content:center; gap:16px; margin-top: 16px;">
        {f'<a href="{cover_letter_link}" target="_blank" class="btn btn-primary">📄 Read Cover Letter</a>' if cover_letter_link and cover_letter_link != "#" else ''}
        <a href="#projects" class="btn btn-outline">↓ View Engineering Work</a>
    </div>
</div>

<div class="container">

    <!-- Section 2: Executive Fit -->
    <div class="section-card animate-section" style="animation-delay: 0.2s">
        <h3 class="section-title">🎯 Role Alignment</h3>
        <p style="color:var(--text-dim); margin-bottom:16px; font-size: 1.1rem;">
            This role at {company} strictly requires the following core competencies:
        </p>
        <div class="badge-container" style="margin-bottom: 24px;">
            {required_skills_html}
        </div>
        <p style="color:var(--text-dim); margin-bottom:16px; font-size: 1.1rem; border-top: 1px solid var(--border); padding-top: 24px;">
            Here is my corresponding technical arsenal:
        </p>
        <div class="badge-container">
            {skill_badges}
        </div>
    </div>

    <!-- Section 3 & 4: Roadmap & Gaps -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-bottom: 32px;">
        <div class="section-card animate-section" style="margin-bottom:0; animation-delay: 0.3s">
            <h3 class="section-title" style="font-size: 1.3rem;">⚠️ Gap Analysis</h3>
            <p style="color:var(--text-dim); margin-bottom: 16px; font-size: 0.9rem;">Missing qualifications mapped to role</p>
            <ul class="list-wrapper">
                {gap_items}
            </ul>
        </div>
        
        <div class="section-card animate-section" style="margin-bottom:0; animation-delay: 0.4s">
            <h3 class="section-title" style="font-size: 1.3rem;">🚀 Learning Objective</h3>
            <p style="color:var(--text-dim); margin-bottom: 16px; font-size: 0.9rem;">My strategic upskilling plan</p>
            <ul class="list-wrapper">
                {road_items}
            </ul>
        </div>
    </div>

    <!-- Section 5: Projects -->
    <div id="projects" class="section-card animate-section" style="animation-delay: 0.5s">
        <h3 class="section-title">💻 High-Impact Engineering Proof</h3>
        <p style="color:var(--text-dim); margin-bottom: 32px; font-size: 1.1rem;">
            The following repositories demonstrate my hands-on capability directly related to the <strong>{role}</strong> position.
        </p>
        <div class="project-grid">
            {projects_html or f'<p style="color:var(--text-dim); font-style:italic;">No mapped projects found. Debug info: Found {len(projects)} total projects in portfolio_data. Ranked len: {len(ranked)}. portfolio_data keys: {list(portfolio_data.keys()) if isinstance(portfolio_data, dict) else type(portfolio_data)}. raw content length: {len(str(portfolio_data))}</p>'}
        </div>
    </div>

</div>

<!-- Footer -->
<div class="footer animate-section" style="animation-delay: 0.6s">
    SYSTEM_LOG: Generated via OrchestrAI Autonomous Agent System <br/>
    TIMESTAMP: {ts}
</div>

</body>
</html>"""

def run_per_internship_portfolio_agent() -> list[dict]:
    logger.info("PerInternshipPortfolioAgent: Starting...")

    jobs_data = read_yaml_from_github(JOBS_FILE)
    jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []

    portfolio_data = read_yaml_from_github(PORTFOLIO_FILE)
    projects = []
    if isinstance(portfolio_data, dict):
        projects = portfolio_data.get("portfolio", {}).get("projects", [])

    users_data = read_yaml_from_github(USERS_FILE)
    user = users_data.get("user", {}) if isinstance(users_data, dict) else {}
    user_name = user.get("name", DEFAULT_USER_NAME)
    user_skills = user.get("resume_skills", DEFAULT_SKILLS)

    skill_gap_data = read_yaml_from_github("database/skill_gap_per_job.yaml")
    skill_analysis = skill_gap_data.get("job_skill_analysis", []) if isinstance(skill_gap_data, dict) else []
    skill_lookup = {(item.get("company"), item.get("role")): item for item in skill_analysis if isinstance(item, dict)}

    cl_data = read_yaml_from_github("database/cover_letter_index.yaml")
    cl_list = cl_data.get("cover_letters", []) if isinstance(cl_data, dict) else []
    cl_lookup = {(item.get("company"), item.get("role")): item.get("link", "") for item in cl_list if isinstance(item, dict)}

    from backend.github_yaml_db import DATA_DIR
    internships_dir = os.path.join(DATA_DIR, "frontend", "portfolio", "internships")
    os.makedirs(internships_dir, exist_ok=True)

    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://orchestrai-agent.onrender.com")
    index = []
    generated = 0

    for job in jobs:  # Process all fetched internships
        company = job.get("company", "Unknown")
        role = job.get("role", "Intern")
        job_skills = [str(s) for s in job.get("technical_skills", []) if s]

        key = (company, role)
        skill_info = skill_lookup.get(key, {})
        skill_gaps = skill_info.get("missing_skills", [])
        roadmap = skill_info.get("roadmap", [])
        cl_link = cl_lookup.get(key, "")

        try:
            html = _generate_portfolio_html(
                company=company, role=role, job_skills=job_skills,
                projects=projects, user_name=user_name, user_skills=user_skills,
                skill_gaps=skill_gaps, roadmap_steps=roadmap,
                cover_letter_link=cl_link
            )
            slug = f"{_slugify(company)}_{_slugify(role)}"

            slug = f"{_slugify(company)}_{_slugify(role)}"
            # Write HTML file via GitHub Persistence layer
            file_name = f"{slug}.html"
            file_path = f"frontend/portfolio/internships/{file_name}"
            
            _, sha = _get_raw_file(file_path)
            ts = datetime.now(timezone.utc).isoformat()
            _put_raw_file(file_path, html, sha, f"feat(portfolio): generated for {company} — {ts}")

            # URL via Render's static file server
            pub_url = f"{base_url}/portfolio/internships/{slug}.html"
            index.append({"company": company, "role": role, "portfolio_url": pub_url})
            generated += 1
            logger.info("PerInternshipPortfolioAgent: ✓ %s — %s → %s", company, role, pub_url)
        except Exception as exc:
            logger.error("PerInternshipPortfolioAgent: Failed for %s %s - %s", company, role, exc)

    # Save index to GitHub so ExecutionAgent can read pre-built URLs
    try:
        write_yaml_to_github(PER_INTERNSHIP_INDEX_FILE, {"per_internship_portfolios": index})
    except Exception as exc:
        logger.error("PerInternshipPortfolioAgent: Failed to save index YAML - %s", exc)

    try:
        append_log_entry({
            "agent": "PerInternshipPortfolioAgent",
            "action": f"Generated {generated} per-internship portfolio pages",
            "status": "success" if generated > 0 else "partial",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        })
    except Exception:
        pass

    logger.info("PerInternshipPortfolioAgent: Done. %d pages generated.", generated)
    return index



if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
    results = run_per_internship_portfolio_agent()
    print(f"\nGenerated {len(results)} per-internship portfolio pages.")
