"""
interview_coach_agent.py — AI Interview Coach
OrchestrAI Autonomous Multi-Agent System

PURPOSE:
  For each internship listing, generate a tailored mock interview simulation
  page containing technical, behavioral, coding, and case-study questions.

FLOW:
  1. Read jobs from database/jobs.yaml
  2. Read user profile from database/users.yaml
  3. Use LLM to generate 8+ role-specific questions per job
  4. Build a rich HTML interview practice page
  5. Save HTML to DATA_DIR/frontend/interview/{slug}.html
  6. Serve via Render static mount at /interview/{slug}.html
  7. Save index to database/interview_sessions.yaml
"""

from __future__ import annotations

import logging
import os
import re
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
logger = logging.getLogger("OrchestrAI.InterviewCoachAgent")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
openai_client = OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL, max_retries=0) if GEMINI_API_KEY else None

JOBS_FILE             = "database/jobs.yaml"
USERS_FILE            = "database/users.yaml"
INTERVIEW_INDEX_FILE  = "database/interview_sessions.yaml"

DEFAULT_USER_NAME   = "Swathy G"
DEFAULT_SKILLS      = ["Python", "Machine Learning", "SQL", "Data Analysis"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40]


def _is_data_role(role: str) -> bool:
    keywords = ["data", "analyst", "analytics", "business analyst", "bi ", "sql"]
    return any(k in role.lower() for k in keywords)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Question Generator
# ─────────────────────────────────────────────────────────────────────────────

def _generate_questions(company: str, role: str, skills: list[str], user_skills: list[str]) -> dict:
    """
    Call Gemini to generate 4 categories of interview questions.
    Returns dict with keys: technical, behavioral, coding, case
    """
    skills_str = ", ".join(skills[:8]) if skills else "Python, ML, SQL"
    user_skills_str = ", ".join(user_skills[:6]) if user_skills else "Python"
    include_case = _is_data_role(role)

    prompt = f"""You are a senior interviewer at {company}.
Generate realistic interview questions for the role: {role}
Required skills: {skills_str}
Candidate has: {user_skills_str}

Return EXACTLY this format (no extra text):
TECHNICAL:
1. [question]
2. [question]
3. [question]

BEHAVIORAL:
1. [question]
2. [question]
3. [question]

CODING:
1. [coding problem title] — [brief description]
2. [coding problem title] — [brief description]

{"CASE:" if include_case else ""}
{"1. [data/business case scenario]" if include_case else ""}
{"2. [data/business case scenario]" if include_case else ""}
"""

    fallback = {
        "technical": [
            f"Explain your experience with {skills[0] if skills else 'Python'} and how you've used it in projects.",
            f"How would you approach building a {role.replace(' Intern', '')} pipeline from scratch?",
            f"Describe a challenging technical problem you solved using {skills[1] if len(skills) > 1 else 'Machine Learning'}.",
        ],
        "behavioral": [
            "Tell me about a time you had to learn a new technology quickly.",
            "Describe a situation where you had to work under tight deadlines.",
            "Give an example of a project where you collaborated with a team.",
        ],
        "coding": [
            f"Implement a function to {skills[0].lower() if skills else 'clean'} a dataset and handle missing values",
            "Write an efficient algorithm for binary search and analyze its time complexity",
        ],
        "case": [
            f"Given a dataset of {company}'s user behavior, how would you identify churn patterns?",
            "A/B test results show 10% lift in metric X but 5% drop in metric Y — what's your recommendation?",
        ] if include_case else [],
    }

    if not openai_client:
        return fallback

    try:
        resp = openai_client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7,
        )
        raw = resp.choices[0].message.content.strip()

        def _extract_section(label: str, text: str) -> list[str]:
            pattern = rf"{label}:?\s*\n(.*?)(?=\n[A-Z]+:|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if not match:
                return []
            lines = match.group(1).strip().split("\n")
            result = []
            for line in lines:
                line = re.sub(r"^\d+\.\s*", "", line).strip()
                if line and len(line) > 5:
                    result.append(line)
            return result[:3]

        return {
            "technical": _extract_section("TECHNICAL", raw) or fallback["technical"],
            "behavioral": _extract_section("BEHAVIORAL", raw) or fallback["behavioral"],
            "coding":    _extract_section("CODING", raw) or fallback["coding"],
            "case":      _extract_section("CASE", raw) if include_case else [],
        }

    except Exception as exc:
        logger.warning("InterviewCoachAgent: LLM failed for %s — %s. Using fallback.", role, exc)
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# HTML Page Builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_interview_html(
    company: str,
    role: str,
    skills: list[str],
    questions: dict,
    user_name: str,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    # Flatten questions into a list of {q, cat, color} for the JS state machine
    flat_questions = []
    
    cat_meta = {
        "technical": {"label": "⚙️ Technical", "color": "#818cf8"},
        "behavioral": {"label": "🧠 Behavioral", "color": "#34d399"},
        "coding": {"label": "💻 Coding", "color": "#38bdf8"},
        "case": {"label": "📊 Case Study", "color": "#fbbf24"},
    }
    
    for cat in ["technical", "behavioral", "coding", "case"]:
        qs = questions.get(cat, [])
        for q in qs:
            flat_questions.append({
                "question": q,
                "category": cat_meta[cat]["label"],
                "color": cat_meta[cat]["color"],
                "type": cat
            })

    skill_tags = "".join(f'<span class="badge">{s}</span>' for s in skills[:8])
    
    # Convert flat questions to JSON for JavaScript
    import json
    questions_json = json.dumps(flat_questions)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mock Interview — {role} at {company}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        /* ── Glassmorphism ─────────────────────────── */
        .glass {{
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
        }}
        
        .hero {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            padding: 40px 20px;
            text-align: center;
            position: relative;
            box-shadow: 0 4px 50px rgba(139, 92, 246, 0.3);
        }}
        
        .hero h1 {{ font-size: 1.8rem; font-weight: 800; color: #fff; margin-bottom: 8px; }}
        .hero p {{ font-size: 1rem; color: rgba(255, 255, 255, 0.85); }}
        
        .main-layout {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 24px;
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }}

        /* ── Sidebar ───────────────────────────────── */
        .sidebar {{ padding: 24px; height: fit-content; sticky: top; top: 20px; }}
        .sidebar-title {{ font-size: 0.9rem; font-weight: 700; color: #a78bfa; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }}
        
        .step-item {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            padding: 10px;
            border-radius: 10px;
            color: rgba(255,255,255,0.4);
            font-size: 0.85rem;
            transition: all 0.2s;
        }}
        .step-item.active {{ background: rgba(139, 92, 246, 0.15); color: #fff; font-weight: 600; border-left: 3px solid #8b5cf6; }}
        .step-item.completed {{ color: #10b981; }}
        .step-dot {{ width: 8px; height: 8px; border-radius: 50%; background: currentColor; margin-right: 12px; }}

        /* ── Interview Stage ───────────────────────── */
        .stage {{ position: relative; }}
        
        .question-card {{
            padding: 40px;
            min-height: 400px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .category-badge {{
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 24px;
            background: rgba(139, 92, 246, 0.2);
            color: #c4b5fd;
        }}
        
        .question-text {{ font-size: 1.6rem; font-weight: 600; line-height: 1.4; color: #fff; margin-bottom: 40px; max-width: 650px; }}
        
        /* ── Input Area ────────────────────────────── */
        .input-area {{ width: 100%; margin-top: auto; }}
        textarea {{
            width: 100%;
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px;
            color: #fff;
            font-family: inherit;
            resize: none;
            margin-bottom: 20px;
            transition: border-color 0.2s;
        }}
        textarea:focus {{ border-color: #8b5cf6; outline: none; }}
        
        .btn-group {{ display: flex; gap: 16px; justify-content: center; }}
        .btn {{
            padding: 12px 32px;
            border-radius: 30px;
            font-weight: 700;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .btn-primary {{ background: #8b5cf6; color: white; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4); }}
        .btn-primary:not(:disabled):hover {{ background: #7c3aed; transform: translateY(-2px); }}
        .btn-secondary {{ background: rgba(255,255,255,0.1); color: #fff; }}
        .btn-secondary:hover {{ background: rgba(255,255,255,0.15); }}
        .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}

        .hint-btn {{ color: #fbbf24; font-size: 0.85rem; border: none; background: none; cursor: pointer; text-decoration: underline; margin-top: 10px; }}

        /* ── Timer ─────────────────────────────────── */
        .timer-box {{ position: absolute; top: -15px; right: 20px; padding: 10px 20px; border-radius: 12px; font-weight: 700; font-size: 1.1rem; color: #f87171; background: #1a1a3e; border: 1px solid #f87171; }}

        /* ── Feedback Form (Final Step) ────────────────*/
        #feedback-screen {{ display: none; }}
        .rating-group {{ margin-bottom: 20px; }}
        input[type="range"] {{ width: 100%; accent-color: #8b5cf6; margin-top: 8px; }}
        
        .badge {{ background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; margin: 3px; display: inline-block; }}
        
        .footer {{ text-align: center; padding: 40px; color: rgba(255,255,255,0.2); font-size: 0.8rem; }}
        
        @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(30px); }} to {{ opacity: 1; transform: translateX(0); }} }}
        .animate-slide {{ animation: slideIn 0.4s cubic-bezier(0,0,0.2,1); }}

        @media (max-width: 768px) {{
            .main-layout {{ grid-template-columns: 1fr; }}
            .sidebar {{ display: none; }}
            .question-text {{ font-size: 1.3rem; }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <p>ORCHESTRAI INTERVIEW COACH</p>
        <h1>🤖 AI Mock Interview Session</h1>
        <p style="margin-top:8px;">{role} — <strong>{company}</strong></p>
    </div>

    <div class="main-layout">
        <!-- Sidebar Navigation -->
        <div class="sidebar glass">
            <div class="sidebar-title">Session Progress</div>
            <div id="step-list">
                <!-- JS populated -->
            </div>
            
            <div style="margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
                <div class="sidebar-title">Skills Overview</div>
                {skill_tags or '<span style="color:#666">General skills</span>'}
            </div>
        </div>

        <!-- Main Stage -->
        <div class="stage">
            <div id="timer" class="timer-box">30:00</div>
            
            <!-- Question Screen -->
            <div id="question-screen" class="question-card glass animate-slide">
                <div id="category-label" class="category-badge">TECHNICAL ROUND</div>
                <div id="q-text" class="question-text">Loading question...</div>
                
                <div class="input-area">
                    <textarea id="user-answer" rows="4" placeholder="Type your answer here... (Tip: Explain your thought process out loud)"></textarea>
                    
                    <div class="btn-group">
                        <button id="skip-btn" class="btn btn-secondary" onclick="nextQuestion(true)">Skip</button>
                        <button id="next-btn" class="btn btn-primary" onclick="nextQuestion()">Next Question →</button>
                    </div>
                    <div>
                        <button class="hint-btn" onclick="showHint()">Need a hint? (Tamil → English Helper)</button>
                    </div>
                </div>
            </div>

            <!-- Final Feedback Screen -->
            <div id="feedback-screen" class="question-card glass animate-slide">
                <h2 style="margin-bottom: 20px;">🎉 Session Complete</h2>
                <p style="margin-bottom: 30px; color: #a78bfa;">Great job, {user_name}! Let's log your performance to improve your roadmap.</p>
                
                <div style="width: 100%; text-align: left;">
                    <div class="rating-group">
                        <label style="font-weight: 600; font-size: 0.9rem;">How confident did you feel?</label>
                        <input type="range" id="fb_confidence" min="1" max="10" value="7">
                        <div style="display:flex; justify-content:space-between; font-size: 0.75rem; color:#666;">
                            <span>Nervous</span><span>Confident</span>
                        </div>
                    </div>
                    
                    <div class="rating-group">
                        <label style="font-weight: 600; font-size: 0.9rem;">Interview Difficulty</label>
                        <input type="range" id="fb_difficulty" min="1" max="10" value="5">
                        <div style="display:flex; justify-content:space-between; font-size: 0.75rem; color:#666;">
                            <span>Easy</span><span>Hard</span>
                        </div>
                    </div>

                    <label style="font-weight: 600; font-size: 0.9rem;">Review of faced questions:</label>
                    <textarea id="fb_questions" rows="4" style="margin-top:8px;"></textarea>
                </div>

                <button class="btn btn-primary" onclick="submitFeedback()">📤 Finalize & Log Session</button>
                <div id="fb_status" style="margin-top: 15px; font-size: 13px;"></div>
            </div>
        </div>
    </div>

    <div class="footer">
        Generated by OrchestrAI • Interview Coach • {ts}
    </div>

    <script>
        const QUESTIONS = {questions_json};
        let currentIdx = 0;
        let timerSeconds = 1800;
        let userResponses = [];

        // ── Initialization ─────────────────────────────────
        function init() {{
            renderSidebar();
            updateScreen();
            startTimer();
        }}

        function renderSidebar() {{
            const list = document.getElementById('step-list');
            list.innerHTML = QUESTIONS.map((q, i) => `
                <div class="step-item ${{i === currentIdx ? 'active' : ''}} ${{i < currentIdx ? 'completed' : ''}}">
                    <div class="step-dot"></div>
                    Q${{i + 1}}. ${{q.category}}
                </div>
            `).join('');
        }}

        function updateScreen() {{
            if (currentIdx >= QUESTIONS.length) {{
                showFeedback();
                return;
            }}

            const q = QUESTIONS[currentIdx];
            const screen = document.getElementById('question-screen');
            screen.classList.remove('animate-slide');
            void screen.offsetWidth; // Trigger reflow
            screen.classList.add('animate-slide');

            document.getElementById('category-label').textContent = q.category;
            document.getElementById('category-label').style.color = q.color;
            document.getElementById('category-label').style.background = q.color + '22';
            document.getElementById('q-text').textContent = q.question;
            document.getElementById('user-answer').value = '';
            
            renderSidebar();
        }}

        function nextQuestion(skipped = false) {{
            const ans = document.getElementById('user-answer').value.trim();
            userResponses.push({{
                q: QUESTIONS[currentIdx].question,
                a: skipped ? '[Skipped]' : ans
            }});

            currentIdx++;
            updateScreen();
        }}

        function showHint() {{
            const q = QUESTIONS[currentIdx].question;
            alert("Advice: Think in Tamil if it helps, but translate key concepts. \\n\\nFocus on: " + q.split(' ').slice(0, 5).join(' ') + "...");
        }}

        function showFeedback() {{
            document.getElementById('question-screen').style.display = 'none';
            document.getElementById('feedback-screen').style.display = 'flex';
            
            // Auto-populate some questions for feedback
            const summary = userResponses.map(r => r.q).join('\\n');
            document.getElementById('fb_questions').value = summary;
        }}

        function startTimer() {{
            setInterval(() => {{
                if (timerSeconds <= 0) return;
                timerSeconds--;
                const m = Math.floor(timerSeconds / 60);
                const s = timerSeconds % 60;
                document.getElementById('timer').textContent = `${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
            }}, 1000);
        }}

        async function submitFeedback() {{
            const status = document.getElementById('fb_status');
            status.textContent = '⏳ Saving to cloud database...';
            
            const payload = {{
                company: "{company}",
                role: "{role}",
                questions_faced: document.getElementById('fb_questions').value.split('\\n').filter(q => q.trim().length > 2),
                confidence_level: parseInt(document.getElementById('fb_confidence').value),
                difficulty_level: parseInt(document.getElementById('fb_difficulty').value)
            }};

            try {{
                const resp = await fetch(window.location.origin + '/log-feedback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});
                const data = await resp.json();
                if (resp.ok) {{
                    status.innerHTML = '✅ <span style="color:#4ade80">Session Logged! Your skill gap roadmap will update tomorrow.</span>';
                    setTimeout(() => {{ window.location.href = '/'; }}, 3000);
                }} else {{
                    status.textContent = '❌ Error: ' + data.message;
                }}
            }} catch (e) {{
                status.textContent = '❌ Connection failed. Check Render logs.';
            }}
        }}

        window.onload = init;
    </script>
</body>
</html>"""




# ─────────────────────────────────────────────────────────────────────────────
# Main agent
# ─────────────────────────────────────────────────────────────────────────────

def run_interview_coach_agent() -> list[dict]:
    logger.info("InterviewCoachAgent: Starting...")

    jobs_data  = read_yaml_from_github(JOBS_FILE)
    jobs       = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []

    users_data = read_yaml_from_github(USERS_FILE)
    user       = users_data.get("user", {}) if isinstance(users_data, dict) else {}
    user_name  = user.get("name", DEFAULT_USER_NAME)
    user_skills = user.get("resume_skills", DEFAULT_SKILLS)

    from backend.github_yaml_db import DATA_DIR
    interview_dir = os.path.join(DATA_DIR, "frontend", "interview")
    os.makedirs(interview_dir, exist_ok=True)

    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://orchestrai-agent.onrender.com")
    index    = []
    generated = 0

    for job in jobs:  # Process all internships as requested
        if not isinstance(job, dict):
            continue

        company    = job.get("company", "Unknown")
        role       = job.get("role", "Intern")
        job_skills = [str(s) for s in job.get("technical_skills", []) if s]

        try:
            questions = _generate_questions(company, role, job_skills, user_skills)

            html = _build_interview_html(
                company=company,
                role=role,
                skills=job_skills,
                questions=questions,
                user_name=user_name,
            )

            slug = f"{_slugify(company)}_{_slugify(role)}"
            file_name = f"{slug}.html"
            file_path = f"frontend/interview/{file_name}"
            
            _, sha = _get_raw_file(file_path)
            ts = datetime.now(timezone.utc).isoformat()
            _put_raw_file(file_path, html, sha, f"feat(interview): generated for {company} — {ts}")

            interview_url = f"{base_url}/interview/{slug}.html"
            index.append({
                "company":        company,
                "role":           role,
                "interview_link": interview_url,
                "generated_at":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            })
            generated += 1
            logger.info("InterviewCoachAgent: ✓ %s — %s → %s", company, role, interview_url)

        except Exception as exc:
            logger.error("InterviewCoachAgent: Failed for %s %s — %s", company, role, exc)

    # Save index to GitHub
    try:
        write_yaml_to_github(INTERVIEW_INDEX_FILE, {"interview_sessions": index})
    except Exception as exc:
        logger.error("InterviewCoachAgent: Failed to save index — %s", exc)

    try:
        append_log_entry({
            "agent":     "InterviewCoachAgent",
            "action":    f"Generated {generated} interview simulation pages",
            "status":    "success" if generated > 0 else "partial",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        })
    except Exception:
        pass

    logger.info("InterviewCoachAgent: Done. %d pages generated.", generated)
    return index


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    results = run_interview_coach_agent()
    print(f"\n✅ Generated {len(results)} interview pages:")
    for r in results:
        print(f"  {r['company']:25s} | {r['role']:35s} | {r['interview_link']}")
