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
    """Builds a premium conversational AI voice-enabled chat interface."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Voice Interview — {role} at {company}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #8b5cf6;
            --secondary: #34d399;
            --accent: #f43f5e;
            --bg: #030408;
            --glass: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.08);
            --text-glow: 0 0 15px rgba(139, 92, 246, 0.5);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Outfit', sans-serif; 
            background: linear-gradient(135deg, #030408 0%, #0a0b18 100%); 
            color: #fff; 
            height: 100vh; 
            overflow: hidden; 
            display: flex; 
            flex-direction: row;
        }}

        /* Sidebar / Avatar Area */
        .sidebar {{
            width: 350px;
            background: rgba(0, 0, 0, 0.5);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
            position: relative;
        }}

        .avatar-container {{
            width: 200px;
            height: 200px;
            border-radius: 50%;
            border: 4px solid var(--primary);
            box-shadow: var(--text-glow);
            overflow: hidden;
            margin-bottom: 30px;
            position: relative;
            background: #111;
        }}

        .avatar-container img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .ai-pulse {{
            position: absolute;
            bottom: -5px;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            height: 10px;
            background: var(--primary);
            box-shadow: 0 0 30px var(--primary);
            visibility: hidden;
            animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }}

        @keyframes pulse-ring {{
            0% {{ transform: translate(-50%, 0) scale(0.7); opacity: 0.5; }}
            100% {{ transform: translate(-50%, 0) scale(1.5); opacity: 0; }}
        }}

        .info-box {{
            text-align: center;
            background: var(--glass);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid var(--border);
            width: 100%;
        }}

        /* Main Chat Area */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: transparent;
            position: relative;
        }}

        .header {{ 
            padding: 25px 40px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: rgba(255,255,255,0.02); 
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border); 
        }}

        .chat-container {{ 
            flex: 1; 
            overflow-y: auto; 
            padding: 40px; 
            display: flex; 
            flex-direction: column; 
            gap: 25px;
            scrollbar-width: thin;
            scrollbar-color: var(--primary) transparent;
        }}

        .chat-bubble {{ 
            max-width: 80%; 
            padding: 18px 26px; 
            border-radius: 24px; 
            line-height: 1.6; 
            font-size: 1.05rem; 
            position: relative; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .ai-bubble {{ 
            background: var(--glass); 
            border: 1px solid var(--border); 
            align-self: flex-start; 
            border-bottom-left-radius: 4px; 
            color: #e0e0e0;
            backdrop-filter: blur(5px);
        }}

        .user-bubble {{ 
            background: var(--primary); 
            color: #fff; 
            align-self: flex-end; 
            border-bottom-right-radius: 4px; 
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4); 
        }}

        /* Controls Bar */
        .controls-bar {{ 
            padding: 30px 40px; 
            background: rgba(0,0,0,0.4); 
            backdrop-filter: blur(20px);
            display: flex; 
            gap: 15px; 
            border-top: 1px solid var(--border); 
            align-items: center;
        }}

        #user-input {{ 
            flex: 1; 
            background: rgba(255,255,255,0.04); 
            border: 1px solid var(--border); 
            border-radius: 30px; 
            padding: 16px 28px; 
            color: #fff; 
            font-family: inherit; 
            font-size: 1.05rem; 
            transition: all 0.2s;
        }}

        #user-input:focus {{ outline: none; border-color: var(--primary); background: rgba(255,255,255,0.07); }}

        .action-btn {{
            width: 54px;
            height: 54px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 1.4rem;
        }}

        .voice-btn {{ background: rgba(255,255,255,0.1); border: 1px solid var(--border); }}
        .voice-btn:hover {{ background: rgba(255,255,255,0.2); transform: scale(1.05); }}
        .voice-btn.recording {{ background: var(--accent); animation: breathe 1.5s infinite; }}

        @keyframes breathe {{ 0% {{ box-shadow: 0 0 0 0px rgba(244, 63, 94, 0.5); }} 100% {{ box-shadow: 0 0 0 15px rgba(244, 63, 94, 0); }} }}

        .send-btn {{ background: var(--primary); box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4); }}
        .send-btn:hover {{ background: #7c3aed; transform: scale(1.05); }}

        #status-indicator {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 10px;
            margin-left: 5px;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="avatar-container">
            <img src="/interview/avatar.png" alt="AI Interviewer" onerror="this.src='https://ui-avatars.com/api/?name=AI&background=8b5cf6&color=fff'">
            <div class="ai-pulse" id="pulse"></div>
        </div>
        <div class="info-box">
            <h2 style="color: var(--primary); font-size: 1.2rem; margin-bottom: 5px;">Dr. OrchestrAI</h2>
            <p style="opacity: 0.6; font-size: 0.85rem; letter-spacing: 1px;">SENIOR TECHNICAL INTERVIEWER</p>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border);">
                <p style="font-size: 0.8rem; color: var(--secondary);">● SESSION ACTIVE</p>
                <div style="display: flex; gap: 8px; justify-content: center; margin-top: 10px;">
                    <div style="background: rgba(139, 92, 246, 0.2); border-radius: 4px; padding: 4px 8px; font-size: 10px; color: #a78bfa;">VOICE: ON</div>
                    <div style="background: rgba(52, 211, 153, 0.2); border-radius: 4px; padding: 4px 8px; font-size: 10px; color: #6ee7b7;">SSL: SECURE</div>
                </div>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="header">
            <div>
                <h2 style="font-size: 1.1rem; color: #8b5cf6;">REAL-TIME INTERVIEW 🎧</h2>
                <p style="font-size: 0.8rem; opacity: 0.6;">Targeting {role} at {company}</p>
            </div>
            <div style="text-align: right;">
                <p style="font-size: 0.95rem; font-weight: 700;">{user_name}</p>
                <p style="font-size: 0.75rem; color: grey;">Status: Practice Mode</p>
            </div>
        </div>

        <div class="chat-container" id="chat">
            <div class="chat-bubble ai-bubble">
                Greetings, {user_name}. I am Dr. OrchestrAI. I've reviewed your credentials for the {role} position here at {company}. I'm excited to explore your expertise. Shall we begin?
            </div>
        </div>

        <div class="controls-bar">
            <div style="display: flex; flex-direction: column; flex: 1;">
                <div id="status-indicator">Listening...</div>
                <input type="text" id="user-input" placeholder="Type or speak your answer..." autocomplete="off">
            </div>
            <button class="action-btn voice-btn" onclick="toggleVoice()" id="mic-btn" title="Click to Speak">🎙️</button>
            <button class="action-btn send-btn" onclick="sendMessage()">➔</button>
        </div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('user-input');
        const status = document.getElementById('status-indicator');
        const pulse = document.getElementById('pulse');
        const micBtn = document.getElementById('mic-btn');
        let context = [];

        // ── Voice Synthesis (TTS) ──
        function speak(text) {{
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            const voices = window.speechSynthesis.getVoices();
            utterance.voice = voices.find(v => v.lang.includes('en-US') && v.name.includes('Google')) || voices[0];
            utterance.rate = 1.05;
            utterance.pitch = 0.95;
            
            utterance.onstart = () => pulse.style.visibility = 'visible';
            utterance.onend = () => pulse.style.visibility = 'hidden';
            
            window.speechSynthesis.speak(utterance);
        }}

        // ── Voice Recognition (STT) ──
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition;
        if (SpeechRecognition) {{
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.onresult = (event) => {{
                input.value = event.results[0][0].transcript;
                toggleVoice(); // Stop recording
                sendMessage(); // Auto-send
            }};
            recognition.onend = () => {{
                micBtn.classList.remove('recording');
                status.style.display = 'none';
            }};
        }}

        function toggleVoice() {{
            if (!recognition) {{
                alert("Speech recognition is not supported in this browser.");
                return;
            }}
            if (micBtn.classList.contains('recording')) {{
                recognition.stop();
            }} else {{
                recognition.start();
                micBtn.classList.add('recording');
                status.style.display = 'block';
            }}
        }}

        // ── Chat Logic ──
        async function sendMessage() {{
            const text = input.value.trim();
            if (!text) return;

            addBubble(text, 'user');
            input.value = '';
            
            status.style.display = 'block';
            status.textContent = "AI is thinking...";

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
                status.style.display = 'none';
                addBubble(data.reply, 'ai');
                speak(data.reply); // SPEAK THE REPLY!
                context.push({{ role: 'user', content: text }});
                context.push({{ role: 'assistant', content: data.reply }});
            }} catch(e) {{
                status.style.display = 'none';
                addBubble("⚠️ Session error: Could not reached the AI server.", 'ai');
            }}
        }}

        function addBubble(text, type) {{
            const div = document.createElement('div');
            div.className = `chat-bubble ${{type}}-bubble`;
            div.textContent = text;
            chat.appendChild(div);
            scrollToBottom();
        }}

        function scrollToBottom() {{
            chat.scrollTop = chat.scrollHeight;
        }}

        // Initial greeting voice
        window.onload = () => {{
            setTimeout(() => speak(chat.querySelector('.ai-bubble').textContent), 1000);
        }};
        
        // Handle enter key
        input.addEventListener('keypress', (e) => {{ if(e.key === 'Enter') sendMessage(); }});
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
