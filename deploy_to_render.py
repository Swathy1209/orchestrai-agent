#!/usr/bin/env python3
"""
Deploy OrchestrAI to Render
"""

import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    print("🚀 Deploy OrchestrAI to Render")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("❌ Not in a git repository. Please run 'git init' first.")
        return False
    
    # Stage all files
    if not run_command("git add .", "Staging files"):
        return False
    
    # Commit changes
    commit_message = "Add OrchestrAI Dashboard with Gemini API integration"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        return False
    
    # Push to GitHub
    if not run_command("git push origin main", "Pushing to GitHub"):
        return False
    
    print("\n🎉 Deployment steps completed!")
    print("\n📋 Next steps:")
    print("1. Go to https://dashboard.render.com")
    print("2. Click 'New +' → 'Web Service'")
    print("3. Connect your GitHub repository")
    print("4. Use the render.yaml configuration")
    print("5. Set environment variables:")
    print("   - GEMINI_API_KEY=AIzaSyDEOz_aJpaJ1CTorIlrQ4GxfwDP1S0wF3A")
    print("   - GITHUB_TOKEN=your_github_token")
    print("   - EMAIL_USER=your_gmail@gmail.com")
    print("   - EMAIL_PASS=your_gmail_app_password")
    print("   - EMAIL_RECEIVER=receiver@gmail.com")
    print("\n🌐 Your app will be available at:")
    print("   - API: https://orchestrai-api.onrender.com")
    print("   - Dashboard: https://orchestrai-api.onrender.com/dashboard")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ Ready for Render deployment!")
    else:
        print("\n❌ Deployment failed. Please check the errors above.")
