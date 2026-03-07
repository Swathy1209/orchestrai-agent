#!/usr/bin/env python3
"""
Setup script for OrchestrAI with Gemini API
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with Gemini API key"""
    env_content = """# ─────────────────────────────────────────────────────────────
# OrchestrAI Career Agent — Environment Variables
# ─────────────────────────────────────────────────────────────

# ── GitHub Cloud YAML Database ────────────────────────────────
GITHUB_TOKEN=your-github-personal-access-token-here
GITHUB_USERNAME=Swathy1209
GITHUB_REPO=Swathy1209/orchestrai-db
GITHUB_BRANCH=main

# ── Gemini AI ────────────────────────────────────────────────────
# Gemini API key (you provided this)
GEMINI_API_KEY=AIzaSyDEOz_aJpaJ1CTorIlrQ4GxfwDP1S0wF3A

# ── Email (SMTP) ──────────────────────────────────────────────
# Gmail address used to SEND the daily report
EMAIL_USER=your-gmail@gmail.com

# Gmail App Password (NOT your login password)
# Generate at: https://myaccount.google.com/apppasswords
EMAIL_PASS=your-gmail-app-password

# Email address(es) to RECEIVE the daily report
EMAIL_RECEIVER=your-receiver@gmail.com

# ── SMTP Server (defaults work for Gmail) ─────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
"""
    
    env_path = Path(".env")
    if env_path.exists():
        print("⚠️  .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return False
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("📝 Please edit the .env file and update:")
        print("   - GITHUB_TOKEN: Your GitHub personal access token")
        print("   - EMAIL_USER: Your Gmail address")
        print("   - EMAIL_PASS: Your Gmail app password")
        print("   - EMAIL_RECEIVER: Email address to receive reports")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def run_pipeline():
    """Run the OrchestrAI pipeline"""
    print("\n🚀 Starting OrchestrAI pipeline...")
    
    try:
        # Load environment and run pipeline
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if Gemini API key is set
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key or gemini_key == "your-github-personal-access-token-here":
            print("❌ GEMINI_API_KEY not properly set in .env")
            return False
        
        print("✅ Gemini API key configured")
        
        # Import and run the pipeline
        from backend.agents.execution_agent import run_orchestrai_pipeline
        run_orchestrai_pipeline()
        
        print("🎉 Pipeline completed successfully!")
        print("📧 Check your email for the daily report!")
        print("🌐 Dashboard available at: http://localhost:8000/frontend/dashboard/")
        return True
        
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🤖 OrchestrAI Setup & Run Script")
    print("=" * 50)
    
    # Step 1: Create .env file
    if not create_env_file():
        return False
    
    # Step 2: Ask user to configure and continue
    print("\n" + "=" * 50)
    input("📝 Please edit .env file with your credentials, then press Enter to continue...")
    
    # Step 3: Run pipeline
    return run_pipeline()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
