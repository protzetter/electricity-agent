#!/usr/bin/env python3
"""
Run script for the Electricity Agent Chat Application
"""

import subprocess
import sys
import os

def main():
    """Run the chat application"""
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Check if .env file exists
    if not os.path.exists('config/.env'):
        print("⚠️  Warning: config/.env file not found!")
        print("Please make sure you have your ENTSOE_API_TOKEN configured.")
        print("You can create config/.env with:")
        print("ENTSOE_API_TOKEN=your_token_here")
        print("ANTHROPIC_API_KEY=your_anthropic_key_here")
        print()
    
    # Check if electricity agent exists
    if not os.path.exists('src/agents/electricity_agent.py'):
        print("⚠️  Warning: src/agents/electricity_agent.py not found!")
        print("Please make sure the electricity agent file exists.")
        print()
    
    # Run streamlit
    print("💬 Starting Electricity Agent Chat...")
    print("🌐 Open your browser to http://localhost:8501")
    print("Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "chat_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Chat application stopped.")

if __name__ == "__main__":
    main()
