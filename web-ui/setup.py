#!/usr/bin/env python3
"""
Setup script for High Frequency Crypto Trading Bot Web UI
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_colored(text, color="green"):
    """Print colored text to console"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['green'])}{text}{colors['reset']}")

def create_directory_structure():
    """Create the necessary directory structure"""
    print_colored("Creating directory structure...", "blue")
    
    # Create templates directory
    os.makedirs("templates", exist_ok=True)
    
    # Create static directory with subdirectories
    for dir_path in ["static/css", "static/js", "static/img"]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create data directory if not exists
    os.makedirs("simulation_data", exist_ok=True)
    
    print_colored("Directory structure created successfully!", "green")

def install_requirements():
    """Install required packages"""
    print_colored("Installing required Python packages...", "blue")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print_colored("All requirements installed successfully!", "green")
    except subprocess.CalledProcessError:
        print_colored("Failed to install some requirements. Please check error messages above.", "red")
        return False
    
    return True

def setup_environment():
    """Set up the environment variables"""
    print_colored("Setting up environment...", "blue")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print_colored("Creating sample .env file...", "yellow")
        with open(".env", "w") as f:
            f.write("""# API Configuration
API_KEY=your_api_key_here

# Trading Configuration
SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT,BNB/USDT
TIMEFRAME=30s
TRADE_AMOUNT=0.0001

# Mode Configuration
SIMULATION_MODE=true
SIMULATION_INITIAL_BALANCE=100.0

# Strategy Parameters
SHORT_WINDOW=2
LONG_WINDOW=5

# Bot Settings
CHECK_INTERVAL=2
GENERATE_DASHBOARD_INTERVAL=5

# Directory Settings
DATA_DIR=simulation_data
""")
        print_colored("Sample .env file created. Please edit it with your API key and preferences.", "yellow")
    else:
        print_colored(".env file already exists. Skipping creation.", "yellow")
    
    print_colored("Environment setup completed!", "green")

def main():
    """Main setup function"""
    print_colored("=" * 80, "blue")
    print_colored("High Frequency Crypto Trading Bot - Web UI Setup", "blue")
    print_colored("=" * 80, "blue")
    
    create_directory_structure()
    
    if not install_requirements():
        print_colored("Setup failed due to package installation issues.", "red")
        return
    
    setup_environment()
    
    print_colored("=" * 80, "blue")
    print_colored("Setup completed successfully!", "green")
    print_colored("To start the web interface, run: python app.py", "green")
    print_colored("Then open your browser at: http://localhost:5222", "green")
    print_colored("=" * 80, "blue")

if __name__ == "__main__":
    main()