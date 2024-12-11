# utils/dependencies.py
import subprocess
import sys
import logging
import os
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = {
    'essential': [
        'curl',
        'gnupg2',
        'software-properties-common',
        'python3-pip',
        'python3-venv',
        'python3-full',
        'sqlite3',
        'net-tools'
    ],
    'optional': [
        'jq',
        'screen',
        'ntp'
    ]
}

PYTHON_PACKAGES = [
    'psutil>=5.8.0',
    'requests>=2.26.0',
    'typing_extensions>=4.0.0',
    'packaging>=21.0'
]

def check_dependencies() -> None:
    """Check and install required system and Python dependencies."""
    logger.info("Installing dependencies...")
    
    # Check system packages
    _check_system_packages()
    
    # Setup and use virtual environment
    _setup_python_environment()
    
    logger.info("All dependencies are satisfied")

def _check_system_packages() -> None:
    """Check and install required system packages."""
    missing_essential = _get_missing_packages(REQUIRED_PACKAGES['essential'])
    missing_optional = _get_missing_packages(REQUIRED_PACKAGES['optional'])
    
    if missing_essential:
        logger.info(f"Installing essential packages: {', '.join(missing_essential)}")
        _install_packages(missing_essential)
    
    if missing_optional:
        logger.info(f"Installing recommended packages: {', '.join(missing_optional)}")
        try:
            _install_packages(missing_optional)
        except Exception as e:
            logger.warning(f"Some optional packages could not be installed: {str(e)}")

def _get_missing_packages(packages: List[str]) -> List[str]:
    """Check which packages are not installed."""
    missing = []
    for package in packages:
        try:
            result = subprocess.run(
                ['dpkg', '-s', package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode != 0:
                missing.append(package)
        except Exception:
            missing.append(package)
    return missing

def _install_packages(packages: List[str]) -> None:
    """Install specified packages using apt-get."""
    try:
        # Update package list
        subprocess.run(
            ['sudo', 'apt-get', 'update'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Install packages
        subprocess.run(
            ['sudo', 'apt-get', 'install', '-y'] + packages,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e.stderr.decode()}")
        raise Exception("Package installation failed")

def _setup_python_environment() -> None:
    """Setup and configure Python virtual environment."""
    try:
        venv_path = Path(__file__).parent.parent / 'venv'
        
        # Create virtual environment if it doesn't exist
        if not venv_path.exists():
            logger.info("Creating virtual environment...")
            subprocess.run(
                [sys.executable, '-m', 'venv', str(venv_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
        
        # Get path to pip in virtual environment
        if sys.platform == "win32":
            venv_pip = venv_path / 'Scripts' / 'pip'
        else:
            venv_pip = venv_path / 'bin' / 'pip'
        
        # Upgrade pip in virtual environment
        subprocess.run(
            [str(venv_pip), 'install', '--upgrade', 'pip'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Install required packages in virtual environment
        logger.info("Installing Python packages in virtual environment...")
        subprocess.run(
            [str(venv_pip), 'install'] + PYTHON_PACKAGES,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        # Create activation script if it doesn't exist
        activate_script = Path(__file__).parent.parent / 'activate_venv.sh'
        if not activate_script.exists():
            with open(activate_script, 'w') as f:
                f.write(f'''#!/bin/bash
source {venv_path}/bin/activate
python3 main.py
''')
            activate_script.chmod(0o755)
            
        logger.info("Python environment setup completed")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup Python environment: {e.stderr.decode()}")
        raise Exception("Python environment setup failed")
    except Exception as e:
        logger.error(f"Failed to setup Python environment: {str(e)}")
        raise Exception("Python environment setup failed")
