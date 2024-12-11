# bootstrap.py
import sys
import subprocess
import os
from pathlib import Path
from typing import List

def check_python_version() -> None:
    """Check if Python version meets minimum requirements."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current Python version is {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)

def setup_virtual_environment() -> str:
    """Create and activate a virtual environment."""
    print("Setting up virtual environment...")
    try:
        # Install python3-venv if not present
        subprocess.run(
            ['sudo', 'apt-get', 'update'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        subprocess.run(
            ['sudo', 'apt-get', 'install', '-y', 'python3-venv', 'python3-full'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Create venv directory in the installer directory
        venv_path = Path(__file__).parent / 'venv'
        subprocess.run(
            [sys.executable, '-m', 'venv', str(venv_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Return path to venv's Python
        return str(venv_path / 'bin' / 'python3')
        
    except subprocess.CalledProcessError as e:
        print("Error: Failed to setup virtual environment")
        print(f"Details: {e.stderr.decode()}")
        sys.exit(1)

def install_packages(venv_python: str, packages: List[str]) -> None:
    """Install required packages in virtual environment."""
    print("Installing required Python packages...")
    try:
        # Upgrade pip in virtual environment
        subprocess.run(
            [venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Install required packages
        subprocess.run(
            [venv_python, '-m', 'pip', 'install'] + packages,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        print("✔ All Python packages installed successfully")
        
    except subprocess.CalledProcessError as e:
        print("Error: Failed to install required Python packages.")
        print(f"Details: {e.stderr.decode()}")
        sys.exit(1)

def main():
    print("Checking Python environment...")
    
    # Check Python version
    check_python_version()
    print("✔ Python version check passed")
    
    # Setup virtual environment
    venv_python = setup_virtual_environment()
    print("✔ Virtual environment created")
    
    # Define required packages
    packages = [
        'psutil',
        'requests',
        'typing_extensions',
        'packaging'
    ]
    
    # Install required packages in virtual environment
    install_packages(venv_python, packages)
    
    # Create activation script
    activate_script = """#!/bin/bash
source venv/bin/activate
python3 main.py
"""
    
    with open('run_installer.sh', 'w') as f:
        f.write(activate_script)
    
    # Make script executable
    os.chmod('run_installer.sh', 0o755)
    
    print("\nSetup completed successfully!")
    print("To run the installer, use: ./run_installer.sh")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error occurred: {str(e)}")
        print("Please report this issue to the development team.")
        sys.exit(1)
