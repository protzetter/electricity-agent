#!/usr/bin/env python3
"""
Run script for the European Electricity Market Analysis Streamlit app
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit application"""
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("Streamlit not found. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "streamlit_requirements.txt"])
    
    # Check if .env file exists
    if not os.path.exists('config/.env'):
        print("⚠️  Warning: config/.env file not found!")
        print("Please make sure you have your ENTSOE_API_TOKEN configured.")
        print("You can create config/.env with:")
        print("ENTSOE_API_TOKEN=your_token_here")
        print()
    
    # Run streamlit
    print("🚀 Starting European Electricity Market Analysis App...")
    print("📊 Open your browser to http://localhost:8501")
    print("Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped.")

if __name__ == "__main__":
    main()
