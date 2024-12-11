# utils/permissions.py
import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

def check_user_permissions(install_dir: Path) -> None:
    """
    Check if user has sufficient permissions for installation.
    
    Args:
        install_dir: Installation directory path
        
    Raises:
        Exception: If permissions are insufficient
    """
    logger.info("Checking user permissions...")
    
    # Check sudo access
    if not _can_use_sudo():
        raise Exception(
            "Sudo privileges required for installation. "
            "Please contact your system administrator."
        )
    
    # Check directory permissions
    _check_directory_permissions(install_dir)
    
    # Check port availability (warning only)
    _check_port_availability([4160, 4161, 8080])
    
    logger.info("Permission checks passed")

def _can_use_sudo() -> bool:
    """Check if user can use sudo."""
    try:
        subprocess.run(
            ['sudo', '-n', 'true'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def _check_directory_permissions(path: Path) -> None:
    """Check directory permissions."""
    try:
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Check write permission
        test_file = path / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
        except Exception:
            raise Exception(f"Cannot write to {path}")
        
    except Exception as e:
        logger.error(f"Directory permission check failed: {str(e)}")
        raise

def _check_port_availability(ports: List[int]) -> None:
    """
    Check if required ports are available.
    Issues warnings instead of errors for busy ports.
    """
    for port in ports:
        try:
            result = subprocess.run(
                ['sudo', 'lsof', '-i', f':{port}'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                logger.warning(f"Port {port} is already in use")
        except Exception as e:
            logger.warning(f"Could not check port {port}: {str(e)}")
