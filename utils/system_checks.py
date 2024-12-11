# utils/system_checks.py
import os
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

def check_system_requirements() -> None:
    """
    Check if the system meets the minimum requirements for running an Algorand node.
    Raises Exception if requirements are not met.
    """
    logger.info("Checking system requirements...")
    
    # Check if system is Ubuntu
    if not _is_ubuntu():
        raise Exception("This installer requires Ubuntu")
    
    # Get Ubuntu version
    ubuntu_version = _get_ubuntu_version()
    logger.info(f"Detected Ubuntu version: {ubuntu_version[0]}.{ubuntu_version[1]}")
    
    if ubuntu_version < (18, 4):
        raise Exception(f"Ubuntu version {ubuntu_version[0]}.{ubuntu_version[1]} is not supported. Minimum required is 18.04")
    
    # Check CPU cores
    cpu_count = os.cpu_count() or 0
    if cpu_count < 4:
        raise Exception(f"Your system has {cpu_count} CPU cores. Minimum requirement is 4 cores.")
    
    # Check RAM
    total_ram = _get_total_ram()
    if total_ram < 4:
        raise Exception(f"Your system has {total_ram:.1f}GB RAM. Minimum requirement is 4GB.")
    
    # Check available disk space
    available_space = _get_available_space()
    if available_space < 10:
        raise Exception(f"You have {available_space:.1f}GB available disk space. Minimum requirement is 100GB.")
    
    logger.info("System requirements check passed")

def _is_ubuntu() -> bool:
    """Check if the system is running Ubuntu."""
    try:
        # Try multiple methods to detect Ubuntu
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                return 'ubuntu' in content
        return False
    except Exception as e:
        logger.error(f"Error checking Ubuntu: {str(e)}")
        return False

def _get_ubuntu_version() -> Tuple[int, int]:
    """Get Ubuntu version as tuple (major, minor)."""
    try:
        version = ""
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('VERSION_ID'):
                        # Remove quotes and clean the version string
                        version = line.split('=')[1].strip().strip('"').strip("'")
                        break
        
        if not version:
            # Fallback to lsb_release command
            try:
                result = subprocess.run(
                    ['lsb_release', '-r'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                version = result.stdout.split(':')[1].strip()
            except subprocess.CalledProcessError:
                raise Exception("Could not determine Ubuntu version using lsb_release")
        
        # Split version and convert to numbers
        parts = version.split('.')
        if len(parts) >= 2:
            major = int(parts[0])
            # Handle cases where minor version might have additional characters
            minor = int(''.join(filter(str.isdigit, parts[1])))
            return (major, minor)
        else:
            raise Exception(f"Invalid version format: {version}")
            
    except Exception as e:
        logger.error(f"Error getting Ubuntu version: {str(e)}")
        raise Exception("Could not determine Ubuntu version.")

def _get_total_ram() -> float:
    """Get total RAM in GB."""
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal'):
                    # Convert KB to GB
                    return int(line.split()[1]) / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error checking RAM: {str(e)}")
        return 0

def _get_available_space() -> float:
    """Get available disk space in GB."""
    try:
        stat = os.statvfs(str(Path.home()))
        return (stat.f_frsize * stat.f_bavail) / (1024**3)
    except Exception as e:
        logger.error(f"Error checking disk space: {str(e)}")
        return 0

def _is_ssd(path: str = '/') -> bool:
    """Check if the path is on an SSD."""
    try:
        # Get device name
        df = subprocess.run(
            ['df', path],
            capture_output=True,
            text=True,
            check=True
        )
        device = df.stdout.split('\n')[1].split()[0]
        
        # Get the base device (remove partition numbers)
        base_device = ''.join(c for c in device if not c.isdigit())
        device_name = os.path.basename(base_device)
        
        # Check rotational flag
        with open(f"/sys/block/{device_name}/queue/rotational", 'r') as f:
            return f.read().strip() == '0'
    except Exception:
        logger.warning("Could not determine storage type")
        return False
