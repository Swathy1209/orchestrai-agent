"""
interview_agent.py — Real-Time AI Interviewer
OrchestrAI Autonomous Multi-Agent System

PURPOSE:
  Provide a conversational AI interviewer that dynamically generates
  interview questions and follow-up questions based on the user's answers.
  Includes portfolio-personalized questions and a 5-metric evaluation system.
"""

import logging
import os
import re
import json
from datetime import datetime, timezone
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI

from backend.github_yaml_db import (
    read_yaml_from_github,
    write_yaml_to_github,
    append_log_entry,
    _put_raw_file,
    _get_raw_file
)

load_dotenv()
logger = logging.getLogger("OrchestrAI.InterviewAgent")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
openai_client = OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL, max_retries=0) if GEMINI_API_KEY else None

JOBS_FILE = "database/jobs.yaml"
USERS_FILE = "database/users.yaml"

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40]

def _build_realtime_html(company: str, role: str, user_name: str) -> str:
    """Builds a conversational chat interface for the real-time interview."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time AI Interview — {role} at {company}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Outfit', sans-serif; background: #0a0b10; color: #fff; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }}
        .header {{ padding: 25px 40px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 40px; display: flex; flex-direction: column; gap: 20px; }}
        .chat-bubble {{ max-width: 70%; padding: 16px 24px; border-radius: 20px; line-height: 1.5; font-size: 1rem; animation: slideUp 0.3s ease-out; position: relative; }}
        .ai-bubble {{ background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); align-self: flex-start; border-bottom-left-radius: 4px; color: #c4b5fd; }}
        .user-bubble {{ background: #8b5cf6; color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); }}
        .input-bar {{ padding: 30px 40px; background: rgba(255,255,255,0.02); display: flex; gap: 15px; border-top: 1px solid rgba(255,255,255,0.05); }}
        #user-input {{ flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 15px 25px; color: #fff; font-family: inherit; font-size: 1rem; }}
        #user-input:focus {{ outline: none; border-color: #8b5cf6; background: rgba(255,255,255,0.08); }}
        .send-btn {{ background: #8b5cf6; border: none; width: 50px; height: 50px; border-radius: 50%; color: white; cursor: pointer; transition: all 0.2s; font-size: 1.2rem; }}
        .send-btn:hover {{ background: #7c3aed; transform: scale(1.05); }}
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .metric-badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; margin-right: 8px; font-weight: 700; background: rgba(139, 92, 246, 0.2); color: #a78bfa; }}
        #typing-indicator {{ display: none; color: #666; font-size: 0.8rem; margin-left: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h2 style="font-size: 1.1rem; color: #8b5cf6;">ORCHESTRAI | REAL-TIME 🎧</h2>
            <p style="font-size: 0.8rem; opacity: 0.6;">{role} at {company}</p>
        </div>
        <div style="text-align: right;">
            <p style="font-size: 0.9rem; font-weight: 700;">{user_name}</p>
            <p style="font-size: 0.7rem; color: #34d399;">● LIVE SESSION</p>
        </div>
    </div>

    <div class="chat-container" id="chat">
        <div class="chat-bubble ai-bubble">
            Hello {user_name}! I'm the AI Interviewer for {company}. I've reviewed your skills and experience. Are you ready to begin the interview for the {role} position?
        </div>
    </div>

    <div id="typing-indicator">AI is analyzing your response...</div>

    <form class="input-bar" onsubmit="sendMessage(event)">
        <input type="text" id="user-input" placeholder="Type your answer..." autocomplete="off">
        <button type="submit" class="send-btn">➔</button>
    </form>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('user-input');
        const typing = document.getElementById('typing-indicator');
        let context = [];

        async function sendMessage(e) {{
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;

            addBubble(text, 'user');
            input.value = '';
            typing.style.display = 'block';

            try {{
                const resp = await fetch(window.location.origin + '/api/chat-interview', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ 
                        role: "{role}", 
                        company: "{company}", 
                        message: text,
                        history: context
                    }})
                }});
                const data = await resp.json();
                typing.style.display = 'none';
                addBubble(data.reply, 'ai');
                context.push({{ role: 'user', content: text }});
                context.push({{ role: 'assistant', content: data.reply }});
            }} catch(e) {{
                typing.style.display = 'none';
                addBubble("⚠️ Backend connection failed. Please ensure the Render background worker is active.", 'ai');
            }}
            chat.scrollTop = chat.scrollHeight;
        }}

        function addBubble(text, type) {{
            const div = document.createElement('div');
            div.className = `chat-bubble ${{type}}-bubble`;
            div.textContent = text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}
    </script>
</body>
</html>"""

def run_interview_agent() -> List[Dict]:
    logger.info("InterviewAgent: Starting...")
    jobs_data = read_yaml_from_github(JOBS_FILE)
    jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []

    users_data = read_yaml_from_github(USERS_FILE)
    user = users_data.get("user", {}) if isinstance(users_data, dict) else {}
    user_name = user.get("name", "Swathy G")

    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://orchestrai-agent.onrender.com")
    index = []

    from backend.github_yaml_db import DATA_DIR
    interview_dir = os.path.join(DATA_DIR, "frontend", "interview")
    os.makedirs(interview_dir, exist_ok=True)

    for job in jobs[:1]: # Create a live session template for the best match
        company = job.get("company", "Unknown")
        role = job.get("role", "Developer")
        
        try:
            html = _build_realtime_html(company, role, user_name)
            slug = f"live_{_slugify(company)}_{_slugify(role)}"
            file_path = f"frontend/interview/{slug}.html"

            _, sha = _get_raw_file(file_path)
            _put_raw_file(file_path, html, sha, f"feat(interview): generated live session template for {company}")

            index.append({
                "company": company,
                "role": role,
                "live_url": f"{base_url}/interview/{slug}.html",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logger.info("InterviewAgent: ✓ %s — %s (Live)", company, role)
        except Exception as e:
            logger.error("InterviewAgent: Error for %s - %s", company, e)

    return index

if __name__ == "__main__":
    run_interview_agent()
