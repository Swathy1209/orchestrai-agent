import sys
import os

# Ensure the correct path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import backend.agents.execution_agent

def no_op():
    pass

# Mock out all agent functions to skip the long generative pipeline
backend.agents.execution_agent.run_career_agent = no_op
backend.agents.execution_agent.run_interview_feedback_agent = no_op
backend.agents.execution_agent.run_skill_agent = no_op
backend.agents.execution_agent.run_repo_security_scanner_agent = no_op
backend.agents.execution_agent.run_auto_fix_pr_agent = no_op
backend.agents.execution_agent.run_portfolio_builder_agent = no_op
backend.agents.execution_agent.run_cover_letter_agent = no_op
backend.agents.execution_agent.run_practice_agent = no_op
backend.agents.execution_agent.run_resume_optimization_agent = no_op
backend.agents.execution_agent.run_auto_apply_agent = no_op
backend.agents.execution_agent.run_opportunity_matching_agent = no_op
backend.agents.execution_agent.run_career_strategy_agent = no_op
backend.agents.execution_agent.run_career_readiness_agent = no_op
backend.agents.execution_agent.run_career_analytics_agent = lambda: "http://example.com/analytics"
backend.agents.execution_agent.run_interview_coach_agent = no_op
backend.agents.execution_agent.run_per_internship_portfolio_agent = no_op

# Also mock send_email to just capture the HTML
def mock_send_email(subject, html_content):
    with open('mail.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Email HTML saved to mail.html")
    return True

backend.agents.execution_agent.send_email = mock_send_email

# Run pipeline (it will skip agents and go straight to Step 3 - GitHub read + Email formatting)
print("Running execution agent with mocked processors...")
backend.agents.execution_agent.run_orchestrai_pipeline()
print("Done.")
