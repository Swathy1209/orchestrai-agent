import json
import logging
import os
import re
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

from backend.github_yaml_db import (
    read_yaml_from_github,
    write_yaml_to_github,
    append_log_entry,
    _put_raw_file,
    DATA_DIR
)
from backend.utils.resume_parser import download_and_extract

load_dotenv()
logger = logging.getLogger("OrchestrAI.PorschePortfolioAgent")

JOBS_FILE = "database/jobs.yaml"
USERS_FILE = "database/users.yaml"
PER_INTERNSHIP_INDEX_FILE = "database/per_internship_portfolios.yaml"
SKILL_GAP_FILE = "database/skill_gap_per_job.yaml"
CL_INDEX_FILE = "database/cover_letter_index.yaml"

def _slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')[:50]

def extract_resume_details(resume_text: str) -> dict:
    if not resume_text:
        return {"projects": [], "experience": [], "achievements": []}
    
    api_key = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment.")
        return {"projects": [], "experience": [], "achievements": []}
        
    client = OpenAI(
        api_key=api_key, 
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    prompt = f"""Extract all technical projects, professional experience, and key achievements from this resume.
Return strictly in JSON format: 
{{
  "projects": [{{"title": "...", "description": "...", "technologies": "...", "impact": "...", "source": "resume"}}],
  "experience": [{{"role": "...", "company": "...", "duration": "...", "description": "..."}}],
  "achievements": ["..."]
}}
Exclude missing values or use empty strings. Sort from most recent to oldest.
Resume text:
{resume_text[:5000]}
"""
    try:
        resp = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to extract details from resume: {e}")
        return {"projects": [], "experience": [], "achievements": []}

def fetch_github_repos(username: str) -> list[dict]:
    if not username: return []
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token: headers["Authorization"] = f"token {token}"
    
    try:
        resp = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=30", headers=headers)
        if resp.status_code == 200:
            return [{
                "title": r.get("name", ""),
                "description": r.get("description", "") or "",
                "technologies": r.get("language", "") or "",
                "url": r.get("html_url", "#"),
                "stars": r.get("stargazers_count", 0),
                "impact": "",
                "source": "github"
            } for r in resp.json()]
        else:
            logger.error(f"GitHub API returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
    return []

def rank_projects(projects: list[dict], req_skills: list[str]) -> list[dict]:
    req_set = {s.lower() for s in req_skills if s}
    total_req = len(req_set) if req_set else 1
    
    ranked = []
    for p in projects:
        title = str(p.get("title", "")).lower()
        desc = str(p.get("description", "")).lower()
        tech = str(p.get("technologies", "")).lower()
        
        matches = [s for s in req_set if s in title or s in desc or s in tech]
        score = len(matches) / total_req
        
        ranked.append({
            **p,
            "_score": score,
            "_matched": matches
        })
        
    ranked.sort(key=lambda x: (-x["_score"], -x.get("stars", 0)))
    return ranked

def generate_porsche_html(user_name, company, role, req_skills, user_skills, gaps, roadmap, top_projects, github_showcase, cl_link, experience, achievements) -> str:
    ts = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    # 2. WHY I AM A GREAT FIT (Skill Chips)
    req_lower = [s.lower() for s in req_skills]
    skill_chips = ""
    for s in user_skills[:12]:
        if s.lower() in req_lower:
            skill_chips += f'<span style="background:rgba(225,6,0,0.15);color:#E10600;border:1px solid rgba(225,6,0,0.5);padding:8px 16px;border-radius:24px;font-size:13px;font-weight:600;margin:4px;display:inline-block;box-shadow:0 0 10px rgba(225,6,0,0.1)">{s}</span>'
        else:
            skill_chips += f'<span style="background:rgba(255,255,255,0.03);color:#9A9A9A;border:1px solid rgba(255,255,255,0.1);padding:8px 16px;border-radius:24px;font-size:13px;font-weight:500;margin:4px;display:inline-block;">{s}</span>'

    # 3. SKILL GAP ANALYSIS
    if not gaps:
        gap_html = '<div style="color:#10B981;font-size:15px;font-weight:600;display:flex;align-items:center;gap:10px"><span style="font-size:20px">✓</span> All required skills covered</div>'
    else:
        gap_html = '<div style="color:#E10600;font-size:13px;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:12px">Skills I am actively building</div>'
        gap_html += "".join(f'<div style="color:#F5F5F5;font-size:15px;margin-bottom:8px;display:flex;align-items:center;gap:10px"><span style="color:#E10600;font-size:18px">⚠</span> {g}</div>' for g in gaps)

    # 4. LEARNING ROADMAP
    if not roadmap:
        road_html = '<div style="color:#9A9A9A;font-size:15px;">No skill gaps detected. You are well-equipped for this role.</div>'
    else:
        road_html = "".join(f"<div style='color:#F5F5F5;font-size:15px;line-height:1.6;margin-bottom:12px;padding-left:16px;border-left:2px solid #E10600;'>{r}</div>" for r in roadmap[:3])

    # 5. MOST RELEVANT PROJECTS
    proj_html = ""
    for p in top_projects:
        title = p.get("title", "Project")
        desc = p.get("description", "")
        tech = p.get("technologies", "")
        impact = p.get("impact", "")
        url = p.get("url", "#")
        
        proj_html += f"""
        <div class="glass-card" style="margin-bottom:24px;padding:32px">
            <h3 style="color:#F5F5F5;font-size:22px;font-weight:700;margin-bottom:12px;border:none;padding:0;letter-spacing:-0.5px">{title}</h3>
            <p style="color:#9A9A9A;font-size:15px;line-height:1.6;margin-bottom:16px">{desc}</p>
            {f'<p style="color:#F5F5F5;font-size:14px;font-style:italic;margin-bottom:16px;border-left:2px solid #333;padding-left:12px">{impact}</p>' if impact else ''}
            <div style="color:#E10600;font-size:12px;text-transform:uppercase;font-weight:700;letter-spacing:1px;margin-bottom:24px">TECH STACK: <span style="color:#F5F5F5;font-weight:500">{tech}</span></div>
            <a href="{url}" target="_blank" class="btn-outline">GitHub Repository &rarr;</a>
        </div>
        """

    # 6. GITHUB PROJECT SHOWCASE
    gh_html = ""
    for p in github_showcase:
        title = p.get("title", "")
        desc = p.get("description", "")
        stars = p.get("stars", 0)
        url = p.get("url", "#")
        gh_html += f"""
        <a href="{url}" target="_blank" class="gh-card" style="text-decoration:none;display:block;padding:24px;border:1px solid rgba(255,255,255,0.05);border-radius:12px;background:#1A1A1A;margin-bottom:16px;transition:all 0.2s">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <h4 style="color:#F5F5F5;font-size:16px;font-weight:600;margin:0">{title}</h4>
                <span style="color:#E10600;font-size:12px;font-weight:700">⭐ {stars}</span>
            </div>
            <p style="color:#9A9A9A;font-size:13px;line-height:1.5;margin:0">{desc}</p>
        </a>
        """

    # 7. PROFESSIONAL EXPERIENCE
    exp_html = ""
    for exp in experience[:3]:
        r_role = exp.get("role", "Role")
        r_comp = exp.get("company", "Company")
        r_dur = exp.get("duration", "")
        r_desc = exp.get("description", "")
        
        exp_html += f"""
        <div style="margin-bottom:24px;padding-left:16px;border-left:2px solid #E10600;">
            <h4 style="color:#F5F5F5;font-size:18px;font-weight:600;margin-bottom:4px">{r_role} at {r_comp}</h4>
            {f'<div style="color:#E10600;font-size:12px;font-weight:600;margin-bottom:8px">{r_dur}</div>' if r_dur else ''}
            <p style="color:#9A9A9A;font-size:14px;line-height:1.6;margin-bottom:0">{r_desc}</p>
        </div>
        """

    # 8. KEY ACHIEVEMENTS
    ach_html = ""
    if achievements:
        ach_html += "<ul style='list-style-type:none;padding:0;margin:0;'>"
        for ach in achievements[:4]:
            ach_html += f"<li style='color:#F5F5F5;font-size:15px;margin-bottom:12px;display:flex;align-items:flex-start;'><span style='color:#E10600;margin-right:12px;font-weight:bold'>→</span><span>{ach}</span></li>"
        ach_html += "</ul>"

    cl_button = f'<a href="{cl_link}" target="_blank" class="btn-primary" style="margin-top:30px;display:inline-block">View Cover Letter</a>' if cl_link and cl_link != "#" else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{user_name} - Portfolio for {company}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
  :root {{ --bg:#0B0B0B; --surface:#1A1A1A; --primary:#E10600; --text:#F5F5F5; --dim:#9A9A9A; --border:rgba(255,255,255,0.05); }}
  * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Inter', sans-serif; }}
  body {{ background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; }}
  
  .hero {{ padding:100px 20px; text-align:center; background:linear-gradient(180deg, #1A1A1A 0%, #0B0B0B 100%); border-bottom:1px solid rgba(225,6,0,0.2); }}
  .hero h1 {{ font-size:48px; font-weight:800; letter-spacing:-1.5px; margin-bottom:16px; color:#fff; }}
  .hero h2 {{ font-size:18px; font-weight:400; color:var(--dim); max-width:600px; margin:0 auto 24px auto; line-height:1.5; }}
  
  .container {{ max-width:900px; margin:0 auto; padding:60px 20px; }}
  
  .glass-card {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.5); transition:all 0.3s; }}
  .glass-card:hover {{ border-color:rgba(225,6,0,0.4); box-shadow:0 15px 40px rgba(225,6,0,0.15); }}
  
  h3.section-title {{ font-size:13px; text-transform:uppercase; letter-spacing:2px; font-weight:700; color:var(--primary); margin-bottom:24px; border-bottom:1px solid var(--border); padding-bottom:16px; }}
  
  .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:32px; margin-bottom:48px; }}
  @media(max-width:768px) {{ .grid-2 {{ grid-template-columns:1fr; gap:24px; }} .hero h1 {{ font-size:36px; }} }}
  
  .btn-primary {{ background:linear-gradient(90deg, #E10600, #FF3B3B); color:#fff; text-decoration:none; padding:14px 32px; border-radius:30px; font-size:14px; font-weight:600; transition:all 0.2s; box-shadow:0 4px 15px rgba(225,6,0,0.3); }}
  .btn-primary:hover {{ transform:scale(1.02); box-shadow:0 8px 25px rgba(225,6,0,0.5); }}
  
  .btn-outline {{ background:transparent; border:1px solid rgba(225,6,0,0.5); color:#fff; text-decoration:none; padding:10px 24px; border-radius:24px; font-size:13px; font-weight:600; transition:all 0.2s; }}
  .btn-outline:hover {{ border-color:#E10600; background:rgba(225,6,0,0.05); }}
  
  .gh-card:hover {{ border-color:rgba(225,6,0,0.3) !important; transform:translateY(-2px); }}
  
  .footer {{ text-align:center; padding:60px 20px; color:var(--dim); font-size:12px; border-top:1px solid var(--border); text-transform:uppercase; letter-spacing:1px; }}
</style>
</head>
<body>

<div class="hero">
    <div style="font-size:14px;text-transform:uppercase;letter-spacing:2px;color:var(--primary);font-weight:700;margin-bottom:16px">{user_name}</div>
    <h1>Customized Portfolio</h1>
    <h2>Designed exclusively for the <strong style="color:#fff">{role}</strong> role at <strong style="color:#fff">{company}</strong></h2>
    {cl_button}
</div>

<div class="container">

    <div style="margin-bottom:60px">
        <h3 class="section-title">Why I Am A Great Fit</h3>
        <div style="margin-top:16px">{skill_chips}</div>
    </div>

    <div class="grid-2">
        <div class="glass-card" style="padding:32px">
            <h3 class="section-title" style="border:none;padding:0;margin-bottom:20px">Skill Gap Analysis</h3>
            {gap_html}
        </div>
        <div class="glass-card" style="padding:32px">
            <h3 class="section-title" style="border:none;padding:0;margin-bottom:20px">Learning Roadmap</h3>
            {road_html}
        </div>
    </div>

    <div class="grid-2">
        <div class="glass-card" style="padding:32px">
            <h3 class="section-title" style="border:none;padding:0;margin-bottom:20px">Professional Experience</h3>
            {exp_html or '<p style="color:#9A9A9A;font-size:14px">Focusing on academic and project-based experience.</p>'}
        </div>
        <div class="glass-card" style="padding:32px">
            <h3 class="section-title" style="border:none;padding:0;margin-bottom:20px">Key Achievements</h3>
            {ach_html or '<p style="color:#9A9A9A;font-size:14px">Building technical milestones.</p>'}
        </div>
    </div>

    <div style="margin-bottom:60px">
        <h3 class="section-title" style="margin-bottom:32px">Most Relevant Projects</h3>
        {proj_html or '<p style="color:#9A9A9A">No matching projects found.</p>'}
    </div>

    <div style="margin-bottom:40px">
        <h3 class="section-title" style="margin-bottom:32px">GitHub Project Showcase</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">
            {gh_html or '<p style="color:#9A9A9A">No additional repositories available.</p>'}
        </div>
    </div>

</div>

<div class="footer">
    Generated autonomously by OrchestrAI<br/>
    Advanced Career Intelligence System
</div>

</body>
</html>"""

def run_porsche_portfolio_agent() -> None:
    logger.info("PorschePortfolioAgent: Starting...")

    # 1. Fetch Inputs
    users_data = read_yaml_from_github(USERS_FILE)
    user = users_data.get("user", {}) if isinstance(users_data, dict) else {}
    user_name = user.get("name", "Applicant")
    user_skills = user.get("resume_skills", [])
    github_username = os.getenv("GITHUB_USERNAME", user.get("github_username", ""))

    # Extract resume details
    resume_text = download_and_extract()
    resume_details = extract_resume_details(resume_text) if resume_text else {"projects": [], "experience": [], "achievements": []}
    resume_projs = resume_details.get("projects", [])
    resume_exp = resume_details.get("experience", [])
    resume_achieves = resume_details.get("achievements", [])
    logger.info(f"Extracted from resume: {len(resume_projs)} projects, {len(resume_exp)} roles, {len(resume_achieves)} achievements")
    
    # Extract GitHub repos
    github_repos = fetch_github_repos(github_username) if github_username else []
    logger.info(f"Fetched from GitHub: {len(github_repos)} repos for '{github_username}'")

    jobs_data = read_yaml_from_github(JOBS_FILE)
    jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []

    skill_gap_data = read_yaml_from_github(SKILL_GAP_FILE)
    skill_analysis = skill_gap_data.get("job_skill_analysis", []) if isinstance(skill_gap_data, dict) else []
    skill_lookup = {(i.get("company"), i.get("role")): i for i in skill_analysis if isinstance(i, dict)}

    cl_data = read_yaml_from_github(CL_INDEX_FILE)
    cl_list = cl_data.get("cover_letters", []) if isinstance(cl_data, dict) else []
    cl_lookup = {(i.get("company"), i.get("role")): i.get("link", "") for i in cl_list if isinstance(i, dict)}

    # We will write to the same index file ExecutionAgent uses
    index = []
    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://orchestrai-agent.onrender.com")

    for job in jobs:
        company = job.get("company", "Unknown")
        role = job.get("role", "Intern")
        req_skills = [str(s) for s in job.get("technical_skills", [])]

        key = (company, role)
        gaps = skill_lookup.get(key, {}).get("missing_skills", [])
        roadmap = skill_lookup.get(key, {}).get("roadmap", [])
        cl_link = cl_lookup.get(key, "")

        # Rank all projects
        all_projects = resume_projs + github_repos
        ranked_all = rank_projects(all_projects, req_skills)
        
        # Most Relevant (Top 3)
        top_projects = ranked_all[:3]
        
        # GitHub Showcase (remaining github projects sorted by match/stars)
        # Exclude ones already in top 3
        top_titles_urls = {(p.get('title'), p.get('url')) for p in top_projects}
        showcase_candidates = [p for p in ranked_all if p.get("source") == "github" and (p.get('title'), p.get('url')) not in top_titles_urls]
        github_showcase = showcase_candidates[:4] # Top 4 remaining

        html = generate_porsche_html(
            user_name, company, role, req_skills, user_skills, gaps, roadmap, 
            top_projects, github_showcase, cl_link
        )
        
        slug = f"{_slugify(company)}_{_slugify(role)}"
        file_path = f"frontend/portfolio/internships/{slug}.html"
        
        try:
            # We don't need to put directly since execution_agent might sync it or Render will serve it 
            # Actually we must put it in github since frontend mounts depend on cloud sync
            from backend.github_yaml_db import _get_raw_file
            _, sha = _get_raw_file(file_path)
            _put_raw_file(file_path, html, sha, f"feat: [Porsche] generated portfolio for {slug}")
            
            url = f"{base_url}/portfolio/internships/{slug}.html"
            index.append({"company": company, "role": role, "link": url})
            logger.info(f"PorschePortfolioAgent: Generated {url}")
        except Exception as e:
            logger.error(f"PorschePortfolioAgent: Failed to save {slug} - {e}")

    # Save index for ExecutionAgent
    write_yaml_to_github(PER_INTERNSHIP_INDEX_FILE, {"per_internship_portfolios": index})
    append_log_entry({
        "agent": "PorschePortfolioAgent",
        "action": f"Generated premium portfolios for {len(index)} internships",
        "status": "success"
    })
    logger.info("PorschePortfolioAgent: Finished.")
