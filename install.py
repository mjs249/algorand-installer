# install.py
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version meets minimum requirements."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current Python version is {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)

def setup_environment():
    """Ensure virtual environment and GUI dependencies are set up properly."""
    try:
        # Install system dependencies including GUI requirements
        subprocess.run(
            ['sudo', 'apt-get', 'update'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Install required packages including tkinter
        subprocess.run(
            ['sudo', 'apt-get', 'install', '-y', 
             'python3-venv', 
             'python3-full',
             'python3-tk'],  # Required for GUI
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Setup virtual environment
        venv_path = Path('venv')
        if not venv_path.exists():
            subprocess.run(
                [sys.executable, '-m', 'venv', str(venv_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
        
        # Install requirements in virtual environment
        venv_pip = venv_path / 'bin' / 'pip'
        subprocess.run(
            [str(venv_pip), 'install', '-r', 'requirements.txt'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Create activation script that launches GUI
        with open('launch_installer.sh', 'w') as f:
            f.write(f'''#!/bin/bash
source venv/bin/activate
python3 -c "from gui.installer_gui import InstallerGUI; InstallerGUI().run()"
''')
        
        # Make script executable
        os.chmod('launch_installer.sh', 0o755)
        
    except Exception as e:
        print(f"Error setting up environment: {str(e)}")
        sys.exit(1)

def main():
    print("Setting up Algorand Installer Environment...")
    check_python_version()
    setup_environment()
    
    print("\nSetup complete!")
    print("To launch the Algorand Node Installer GUI, run:")
    print("./launch_installer.sh")

if __name__ == "__main__":
    main()
