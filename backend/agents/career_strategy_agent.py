"""
career_strategy_agent.py — Career Strategy Agent
OrchestrAI Autonomous Multi-Agent System

Generate an AI-driven weekly career strategy by analyzing skill gaps, internship match scores, portfolio quality, and interview readiness.
"""

from __future__ import annotations
import logging
import os
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from backend.github_yaml_db import read_yaml_from_github, write_yaml_to_github, append_log_entry

load_dotenv()
logger = logging.getLogger("OrchestrAI.CareerStrategyAgent")

OPENAI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=GEMINI_BASE_URL,
) if OPENAI_API_KEY else None

USERS_FILE = "database/users.yaml"
SKILL_GAPS_FILE = "database/skill_gap_per_job.yaml"
SCORES_FILE = "database/opportunity_scores.yaml"
PORTFOLIO_FILE = "database/portfolio.yaml"
PRACTICE_FILE = "database/practice_sessions.yaml"
STRATEGY_FILE = "database/career_strategy.yaml"

def analyze_career_state() -> dict:
    # 1. Target Goal
    try:
        users_data = read_yaml_from_github(USERS_FILE)
    except:
        users_data = {}
    
    user = users_data.get("user", {})
    career_goals = user.get("career_goals", ["Software Engineer"])
    primary_goal = career_goals[0] if career_goals else "Software Engineer"

    # 2. Skill Gaps
    try:
        skills_data = read_yaml_from_github(SKILL_GAPS_FILE)
        job_skills = skills_data.get("job_skill_analysis", []) if isinstance(skills_data, dict) else []
    except:
        job_skills = []
        
    skill_freq = {}
    for job in job_skills:
        for skill in job.get("missing_skills", []):
            skill_freq[skill] = skill_freq.get(skill, 0) + 1
    
    # Sort by frequency
    sorted_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)
    top_missing_skills = [s[0] for s in sorted_skills[:5]]

    # 3. Opportunity Scores
    try:
        scores_data = read_yaml_from_github(SCORES_FILE)
        scores_list = scores_data if isinstance(scores_data, list) else []
    except:
        scores_list = []
        
    top_jobs = []
    for score in scores_list:
        if score.get("match_score", 0) > 70:
            top_jobs.append(f"{score.get('role')} at {score.get('company')}")
    top_jobs = top_jobs[:5]

    # 4. Portfolio Strength
    try:
        portfolio_data = read_yaml_from_github(PORTFOLIO_FILE)
        portfolio = portfolio_data.get("portfolio", {})
    except:
        portfolio = {}
        
    projects = portfolio.get("projects", [])
    num_projects = len(projects)
    portfolio_strength = f"{num_projects} projects built."
    if num_projects < 4:
        portfolio_strength += " Recommend building more projects to strengthen portfolio."

    # 5. Practice Progress
    try:
        practice_data = read_yaml_from_github(PRACTICE_FILE)
        practice_list = practice_data if isinstance(practice_data, list) else []
    except:
        practice_list = []
        
    sessions_completed = len(practice_list)
    practice_progress = f"{sessions_completed} sessions generated."
    if sessions_completed < 5:
        practice_progress += " Recommend completing more interview practice."
        
    return {
        "goal": primary_goal,
        "missing_skills": top_missing_skills,
        "top_jobs": top_jobs,
        "portfolio_score": portfolio_strength,
        "practice_sessions": practice_progress
    }

def _generate_strategy(data: dict) -> list[str]:
    if not openai_client:
        return [
            f"Learn {', '.join(data['missing_skills'][:2])}",
            "Build more projects",
            "Apply to top matching jobs",
            "Complete more practice sessions"
        ]

    prompt = f"""You are an AI career coach.

User goal: {data['goal']}
Skill gaps (highest priority to learn): {data['missing_skills']}
Top opportunities to apply to: {data['top_jobs']}
Portfolio strength: {data['portfolio_score']}
Practice progress: {data['practice_sessions']}

Generate a weekly action plan with exactly 5-7 prioritized, actionable steps. Make the steps concise but specific.

Respond exactly in JSON format:
{{
  "actions": ["Action 1", "Action 2", "Action 3"]
}}
"""
    try:
        resp = openai_client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        content = resp.choices[0].message.content.strip()
        result = json.loads(content)
        return result.get("actions", [])
    except Exception as exc:
        logger.error(f"CareerStrategyAgent: Failed to generate LLM strategy - {exc}")
        return ["Focus on missing skills: " + ", ".join(data['missing_skills'])]

def run_career_strategy_agent():
    logger.info("CareerStrategyAgent: Starting analysis...")
    
    analysis_data = analyze_career_state()
    actions = _generate_strategy(analysis_data)
    
    strategy_obj = {
        "strategy": {
            "goal": analysis_data["goal"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "actions": actions
        }
    }
    
    try:
        write_yaml_to_github(STRATEGY_FILE, strategy_obj)
        append_log_entry({
            "agent": "CareerStrategyAgent",
            "action": "Generated Career Strategy",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        })
    except Exception as exc:
        logger.error(f"CareerStrategyAgent: Failed to save strategy: {exc}")

    logger.info("CareerStrategyAgent: Finished.")
    return strategy_obj

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
    run_career_strategy_agent()
