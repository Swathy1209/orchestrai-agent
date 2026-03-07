#!/usr/bin/env python3
"""
Create .env file with Gemini API key
"""

def create_env():
    env_content = """# OrchestrAI Environment Variables
GITHUB_TOKEN=your-github-token-here
GITHUB_USERNAME=Swathy1209
GITHUB_REPO=Swathy1209/orchestrai-db
GITHUB_BRANCH=main

# Gemini AI API Key
GEMINI_API_KEY=AIzaSyDEOz_aJpaJ1CTorIlrQ4GxfwDP1S0wF3A

# Email Configuration
EMAIL_USER=your-gmail@gmail.com
EMAIL_PASS=your-gmail-app-password
EMAIL_RECEIVER=your-receiver@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env file created with Gemini API key!")
    print("📝 Please edit .env and update:")
    print("   - GITHUB_TOKEN: Your GitHub token")
    print("   - EMAIL_USER: Your Gmail address")
    print("   - EMAIL_PASS: Your Gmail app password")
    print("   - EMAIL_RECEIVER: Receiver email")

if __name__ == "__main__":
    create_env()
