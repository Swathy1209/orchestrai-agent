"""
practice_routes.py — Real-Time Interactive Interview Coach API
OrchestrAI Autonomous Multi-Agent System

Endpoints:
    POST /practice/{company}/{role}/ask
        → Accepts Tamil or English question
        → Returns AI-generated professional answer, practice version, confidence tips

    GET  /practice/health
        → Health check
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.practice_agent import (
    generate_interview_response,
    validate_company_role,
    log_interview_interaction,
)

logger = logging.getLogger("OrchestrAI.PracticeRoutes")

router = APIRouter(prefix="/practice", tags=["Practice"])


# ── Request / Response models ──────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    professional_answer: str
    practice_version: str
    confidence_tips: list[str]
    detected_language: str
    company: str
    role: str
    timestamp: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "OrchestrAI Practice API", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/{company}/{role}/ask", response_model=AskResponse)
async def ask_interview_question(company: str, role: str, request: AskRequest):
    """
    Real-time AI interview coaching endpoint.

    Accepts a question in Tamil or English and returns:
    - Professional interview answer
    - Simplified practice version
    - Confidence tips

    Args:
        company: Company slug (e.g., 'nvidia', 'google')
        role:    Role slug (e.g., 'ai_intern', 'data_engineer')
        request: JSON body with 'question' field
    """
    # ── Input validation ──
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    question = request.question.strip()
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="Question too long. Max 2000 characters.")

    # ── Security: validate company + role exist ──
    company_decoded = company.replace("_", " ").title()
    role_decoded    = role.replace("_", " ").title()

    is_valid = validate_company_role(company_decoded, role_decoded)
    if not is_valid:
        logger.warning("PracticeRoutes: Unknown company/role — %s / %s", company_decoded, role_decoded)
        # Don't block — still answer but log the warning
        # raise HTTPException(status_code=404, detail=f"No practice data found for {company_decoded} / {role_decoded}")

    # ── Generate AI response ──
    try:
        result = generate_interview_response(
            company=company_decoded,
            role=role_decoded,
            user_input=question,
        )
    except RuntimeError as exc:
        logger.error("PracticeRoutes: AI generation failed — %s", exc)
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(exc)}")
    except Exception as exc:
        logger.error("PracticeRoutes: Unexpected error — %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again.")

    # ── Log interaction ──
    try:
        log_interview_interaction(
            company=company_decoded,
            role=role_decoded,
            user_input=question,
        )
    except Exception:
        pass  # Never let logging crash the response

    timestamp = datetime.now(timezone.utc).isoformat()

    return AskResponse(
        professional_answer=result.get("professional_answer", ""),
        practice_version=result.get("practice_version", ""),
        confidence_tips=result.get("confidence_tips", []),
        detected_language=result.get("detected_language", "English"),
        company=company_decoded,
        role=role_decoded,
        timestamp=timestamp,
    )
