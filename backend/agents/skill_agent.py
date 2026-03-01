"""
skill_agent.py - Skill Gap Analysis Agent
OrchestrAI Autonomous Multi-Agent System

Flow:
  1. read_user_skills()          - reads database/users.yaml from GitHub
  2. read_jobs()                 - reads database/jobs.yaml from GitHub
  3. detect_skill_gaps()         - missing_skills = job_skills - user_skills
  4. generate_learning_roadmap() - OpenAI prompt -> structured roadmap list
  5. store_skill_gap_yaml()      - writes database/skill_gap.yaml to GitHub
  6. log_agent_activity()        - appends to database/agent_logs.yaml

Returns structured dict to ExecutionAgent.
Does NOT send email - ExecutionAgent handles that.
Does NOT modify jobs.yaml or users.yaml.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from backend.github_yaml_db import (
    read_yaml_from_github,
    write_yaml_to_github,
    append_log_entry,
)

logger = logging.getLogger("OrchestrAI.SkillAgent")

USERS_FILE     = "database/users.yaml"
JOBS_FILE      = "database/jobs.yaml"
SKILL_GAP_FILE = "database/skill_gap.yaml"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def read_user_skills() -> tuple:
    """Read users.yaml. Returns (name, email, skills_list). Does NOT modify file."""
    try:
        data   = read_yaml_from_github(USERS_FILE)
        user   = data.get("user", {})
        name   = user.get("name", "unknown")
        email  = user.get("email", "")
        skills = user.get("resume_skills", [])
        if not isinstance(skills, list):
            skills = []
        clean  = [str(s).strip() for s in skills if s]
        logger.info("SkillAgent: Read %d skills for '%s'.", len(clean), name)
        return name, email, clean
    except Exception as exc:
        logger.error("SkillAgent: read_user_skills failed - %s", exc)
        return "unknown", "", []


def read_jobs() -> list:
    """Read jobs.yaml. Returns list of job dicts. Does NOT modify file."""
    try:
        data = read_yaml_from_github(JOBS_FILE)
        jobs = data.get("jobs", [])
        if not isinstance(jobs, list):
            return []
        logger.info("SkillAgent: Read %d jobs.", len(jobs))
        return jobs
    except Exception as exc:
        logger.error("SkillAgent: read_jobs failed - %s", exc)
        return []


def detect_skill_gaps(user_skills: list, jobs: list) -> tuple:
    """
    Compute missing_skills = union(job technical_skills) - user_skills.
    Returns (all_job_skills, missing_skills) as sorted lists.
    """
    job_skills: set = set()
    for job in jobs:
        for s in job.get("technical_skills", []):
            if s and str(s).strip():
                job_skills.add(str(s).strip())
    user_lower = {s.lower() for s in user_skills}
    missing = sorted({s for s in job_skills if s.lower() not in user_lower})
    logger.info("SkillAgent: %d missing skills detected.", len(missing))
    return sorted(job_skills), missing


def _fallback_roadmap(missing_skills: list) -> list:
    priority = {
        "docker":      "Learn Docker for containerisation and deployment",
        "kubernetes":  "Learn Kubernetes for container orchestration",
        "aws":         "Learn AWS (S3, EC2, SageMaker) for cloud engineering",
        "gcp":         "Learn GCP for cloud-based ML pipelines",
        "azure":       "Learn Azure ML for enterprise cloud solutions",
        "fastapi":     "Learn FastAPI for building production ML APIs",
        "flask":       "Learn Flask for lightweight Python web services",
        "pytorch":     "Learn PyTorch for deep learning model development",
        "tensorflow":  "Learn TensorFlow for scalable ML model training",
        "airflow":     "Learn Apache Airflow for data pipeline orchestration",
        "spark":       "Learn Apache Spark for large-scale data processing",
        "mlflow":      "Learn MLflow for experiment tracking and model registry",
        "langchain":   "Learn LangChain for building LLM-powered applications",
        "huggingface": "Learn HuggingFace Transformers for NLP/LLM tasks",
        "pyspark":     "Learn PySpark for distributed data engineering",
        "streamlit":   "Learn Streamlit to build interactive ML dashboards",
        "kafka":       "Learn Apache Kafka for real-time data streaming",
        "dbt":         "Learn dbt for analytics engineering and data modelling",
    }
    roadmap = []
    for skill in missing_skills:
        key = skill.lower().replace(" ", "")
        roadmap.append(priority.get(key, f"Learn {skill} via official docs and hands-on projects"))
    return roadmap or [f"Learn {s} to meet job requirements" for s in missing_skills]


def generate_learning_roadmap(user_skills: list, missing_skills: list) -> list:
    """
    Generate learning roadmap via OpenAI GPT-3.5, with keyword fallback.
    Returns list of actionable roadmap step strings.
    """
    if not missing_skills:
        return ["No skill gaps detected. You are well-equipped for current listings!"]

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = (
                f"User's current skills: {', '.join(user_skills)}\n\n"
                f"Missing skills required by job listings: {', '.join(missing_skills)}\n\n"
                "Generate a concise, prioritised learning roadmap (5-8 bullet points) "
                "for becoming an industry-ready AI/Data Science engineer. "
                "Focus on actionable steps. Return ONLY bullet points, one per line, "
                "starting with a dash (-)."
            )
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a technical career coach for AI/Data Science."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.5,
            )
            raw = response.choices[0].message.content.strip()
            roadmap = [l.lstrip("- ").strip() for l in raw.splitlines() if l.strip()]
            logger.info("SkillAgent: OpenAI generated %d roadmap steps.", len(roadmap))
            return roadmap if roadmap else _fallback_roadmap(missing_skills)
        except Exception as exc:
            logger.warning("SkillAgent: OpenAI failed (%s) - using fallback.", exc)

    return _fallback_roadmap(missing_skills)


def store_skill_gap_yaml(
    user_name: str,
    user_skills: list,
    missing_skills: list,
    roadmap: list,
) -> bool:
    """
    Write database/skill_gap.yaml to GitHub orchestrai-db.
    Does NOT touch jobs.yaml or users.yaml.
    """
    analyzed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    data = {
        "skill_analysis": {
            "user":            user_name,
            "current_skills":  user_skills,
            "missing_skills":  missing_skills,
            "recommended_learning_roadmap": roadmap,
            "analyzed_at":     analyzed_at,
        }
    }
    try:
        ok = write_yaml_to_github(SKILL_GAP_FILE, data)
        if ok:
            logger.info("SkillAgent: skill_gap.yaml written (%d missing, %d steps).",
                        len(missing_skills), len(roadmap))
        return ok
    except Exception as exc:
        logger.error("SkillAgent: store_skill_gap_yaml failed - %s", exc)
        return False


def log_agent_activity(action: str, details: Optional[str] = None, status: str = "success") -> bool:
    """Append a SkillAgent log entry to database/agent_logs.yaml."""
    entry = {
        "agent":     "SkillAgent",
        "action":    action,
        "status":    status,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if details:
        entry["details"] = details
    try:
        return append_log_entry(entry)
    except Exception as exc:
        logger.error("SkillAgent: log_agent_activity failed - %s", exc)
        return False


def run_skill_agent() -> dict:
    """
    Main orchestrator. Runs all 6 steps and returns structured result dict.
    Does NOT send email. ExecutionAgent reads skill_gap.yaml for the email.

    Returns:
        {
            "user": str,
            "current_skills": list,
            "missing_skills": list,
            "roadmap": list,
            "analyzed_at": str,
            "status": "success" | "partial" | "error"
        }
    """
    logger.info("SkillAgent: Starting skill gap analysis...")
    log_agent_activity("Skill gap analysis started")

    result = {
        "user":           "unknown",
        "current_skills": [],
        "missing_skills": [],
        "roadmap":        [],
        "analyzed_at":    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "status":         "error",
    }

    try:
        # Step 1: Read user skills
        user_name, _, user_skills = read_user_skills()
        result["user"] = user_name

        if not user_skills:
            logger.warning("SkillAgent: No user skills in users.yaml.")
            log_agent_activity("Skipped", "users.yaml missing or empty", "partial")
            result["status"] = "partial"
            return result

        result["current_skills"] = user_skills

        # Step 2: Read jobs
        jobs = read_jobs()
        if not jobs:
            logger.warning("SkillAgent: No jobs yet - run CareerAgent first.")
            log_agent_activity("Partial", "jobs.yaml is empty", "partial")
            result["status"] = "partial"
            return result

        # Step 3: Detect skill gaps
        _, missing_skills = detect_skill_gaps(user_skills, jobs)
        result["missing_skills"] = missing_skills

        # Step 4: Generate roadmap
        roadmap = generate_learning_roadmap(user_skills, missing_skills)
        result["roadmap"] = roadmap

        # Step 5: Store skill_gap.yaml
        if not store_skill_gap_yaml(user_name, user_skills, missing_skills, roadmap):
            log_agent_activity("skill_gap.yaml write failed", status="error")
            result["status"] = "error"
            return result

        # Step 6: Log success
        log_agent_activity(
            "Skill gap analysis completed",
            f"{len(missing_skills)} missing skills; {len(roadmap)} roadmap steps for '{user_name}'",
        )

        result["status"] = "success"
        result["analyzed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        logger.info("SkillAgent: Done - %d missing skills, %d roadmap steps.", len(missing_skills), len(roadmap))
        return result

    except Exception as exc:
        logger.exception("SkillAgent crashed - %s", exc)
        log_agent_activity("FAILED", str(exc), "error")
        result["status"] = "error"
        return result


if __name__ == "__main__":
    import json, sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    result = run_skill_agent()
    print("\n-- SkillAgent Result " + "-" * 40)
    print(json.dumps(result, indent=2, ensure_ascii=False))
