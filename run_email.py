#!/usr/bin/env python3
"""
Quick script to run the OrchestrAI email pipeline
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print("🚀 OrchestrAI Email Pipeline Runner")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['EMAIL_USER', 'EMAIL_PASS', 'EMAIL_RECEIVER']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please set these in your .env file:")
        print("   1. Copy .env.example to .env")
        print("   2. Edit .env with your actual credentials")
        print("\n🔧 Example .env file:")
        print("   EMAIL_USER=your-gmail@gmail.com")
        print("   EMAIL_PASS=your-gmail-app-password")
        print("   EMAIL_RECEIVER=receiver@gmail.com")
        return False
    
    print("✅ Environment variables configured")
    print("📧 Starting email pipeline...")
    
    try:
        # Import and run the pipeline
        from backend.agents.execution_agent import run_orchestrai_pipeline
        run_orchestrai_pipeline()
        print("🎉 Email pipeline completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
