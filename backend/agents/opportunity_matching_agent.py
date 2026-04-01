"""
opportunity_matching_agent.py — Opportunity Matching Agent
OrchestrAI Autonomous Multi-Agent System

Flow:
1. Load database/jobs.yaml, database/skill_gap_per_job.yaml, database/users.yaml
2. Calculate match score based on multiple weights
3. Assign selection probability and recommendation priority
4. Save to database/opportunity_scores.yaml
5. Log activity
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.github_yaml_db import (
    read_yaml_from_github,
    write_yaml_to_github,
    append_log_entry
)

logger = logging.getLogger("OrchestrAI.OpportunityMatchingAgent")

JOBS_FILE = "database/jobs.yaml"
SKILL_GAPS_FILE = "database/skill_gap_per_job.yaml"
USERS_FILE = "database/users.yaml"
SCORES_FILE = "database/opportunity_scores.yaml"

def read_jobs() -> list[dict]:
    try:
        data = read_yaml_from_github(JOBS_FILE)
        jobs = data.get("jobs", [])
        return jobs if isinstance(jobs, list) else []
    except Exception as exc:
        logger.error("OpportunityMatchingAgent: read_jobs failed - %s", exc)
        return []

def read_skill_gaps() -> list[dict]:
    try:
        data = read_yaml_from_github(SKILL_GAPS_FILE)
        gaps = data.get("job_skill_analysis", [])
        return gaps if isinstance(gaps, list) else []
    except Exception as exc:
        logger.error("OpportunityMatchingAgent: read_skill_gaps failed - %s", exc)
        return []

def read_user() -> dict:
    try:
        data = read_yaml_from_github(USERS_FILE)
        return data.get("user", {})
    except Exception as exc:
        logger.error("OpportunityMatchingAgent: read_user failed - %s", exc)
        return {}

def update_scores_yaml(data: list[dict]) -> bool:
    try:
        return write_yaml_to_github(SCORES_FILE, data)
    except Exception as exc:
        logger.error("OpportunityMatchingAgent: update_scores_yaml failed - %s", exc)
        return False

def log_agent_activity(action: str, status: str = "success") -> None:
    try:
        append_log_entry({
            "agent": "OpportunityMatchingAgent",
            "action": action,
            "status": status,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        })
    except:
        pass

def run_opportunity_matching_agent() -> list[dict]:
    logger.info("OpportunityMatchingAgent: Starting...")
    
    jobs = read_jobs()
    gaps = read_skill_gaps()
    user = read_user()
    
    if not jobs:
        logger.warning("OpportunityMatchingAgent: Missing jobs.")
        log_agent_activity("Skipped matching - missing data", "partial")
        return []
        
    gap_lookup = {
        (item.get("company", ""), item.get("role", "")): item.get("missing_skills", [])
        for item in gaps if isinstance(item, dict)
    }
    
    user_skills = [s.lower() for s in user.get("resume_skills", [])]
    user_pref_locations = [loc.lower() for loc in user.get("preferred_locations", ["remote"])]
    user_goals = [goal.lower() for goal in user.get("career_goals", ["data", "engineer", "AI", "scientist", "intern"])]
    user_experience = user.get("experience_years", 0)

    opportunity_scores = []
    
    for job in jobs:
        company = job.get("company", "Unknown")
        role = job.get("role", "Unknown")
        location = job.get("location", "Remote")
        required_skills = job.get("technical_skills", [])
        
        # 1. Skill Match Score (Weight: 50%)
        req_skills_lower = [s.lower() for s in required_skills if str(s).strip()]
        if len(req_skills_lower) > 0:
            intersection = [s for s in req_skills_lower if s in user_skills]
            skill_match_ratio = len(intersection) / len(req_skills_lower)
            skill_score = skill_match_ratio * 50
        else:
            skill_score = 50.0 # Default if no skills listed
            
        # 2. Skill Gap Penalty (Weight: 20%)
        missing_skills = gap_lookup.get((company, role), [])
        gap_penalty = len(missing_skills) * 3
        if gap_penalty > 20:
            gap_penalty = 20
            
        # 3. Location Match (Weight: 10%)
        loc_lower = location.lower()
        location_score = 5
        for pref in user_pref_locations:
            if pref in loc_lower or loc_lower in pref:
                location_score = 10
                break
                
        # 4. Career Goal Alignment (Weight: 10%)
        role_lower = role.lower()
        goal_score = 5
        for goal in user_goals:
            if goal in role_lower:
                goal_score = 10
                break
                
        # 5. Experience Alignment (Weight: 10%)
        # Internships generally assume 0-1 years. We map lightly.
        experience_score = 5
        if "intern" in role_lower or "junior" in role_lower:
            if user_experience <= 2:
                experience_score = 10
        elif "senior" in role_lower and user_experience >= 3:
            experience_score = 10
        elif user_experience > 0: # Middle ground if matching normal roles
            experience_score = 10
            
        # FINAL MATCH SCORE
        match_score = skill_score + location_score + goal_score + experience_score - gap_penalty
        match_score = max(0.0, min(100.0, match_score)) # Clamp between 0 and 100
        match_score = round(match_score)
        
        # PROBABILITY LOGIC
        if match_score >= 85:
            selection_probability = "High"
        elif match_score >= 65:
            selection_probability = "Medium"
        else:
            selection_probability = "Low"
            
        # PRIORITY LOGIC
        if match_score >= 80:
            priority = "Apply Now"
        elif match_score >= 60:
            priority = "Strong Consideration"
        else:
            priority = "Optional"
            
        result = {
            "company": company,
            "role": role,
            "match_score": match_score,
            "selection_probability": selection_probability,
            "priority": priority
        }
        
        opportunity_scores.append(result)
        
    if opportunity_scores:
        update_scores_yaml(opportunity_scores)
        log_agent_activity(f"Generated match scores for {len(opportunity_scores)} internships")
        
    logger.info("OpportunityMatchingAgent: Completed successfully.")
    return opportunity_scores

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    results = run_opportunity_matching_agent()
    print(f"Scored {len(results)} roles.")
