# main.py
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
import json

class AlgorandInstaller:
    def __init__(self):
        """Initialize the Algorand node installer."""
        self.config = {
            'data_dir': '/var/lib/algorand'
        }
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _configure_telemetry(self) -> None:
        """Configure telemetry settings for the node post-installation."""
        try:
            self.logger.info("Configuring telemetry...")
            # Disable telemetry by default
            subprocess.run([
                'sudo', '-u', 'algorand', '-H', '-E',
                'diagcfg', 'telemetry', 'disable'
            ], check=True)
            
            # Restart node to apply telemetry settings
            subprocess.run(['sudo', 'systemctl', 'restart', 'algorand'], check=True)
            
        except Exception as e:
            self.logger.error(f"Failed to configure telemetry: {str(e)}")
            raise

    def run_installation(self) -> bool:
        """Run the Ubuntu-specific installation process."""
        try:
            # System updates and prerequisites
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run([
                'sudo', 'apt-get', 'install', '-y',
                'gnupg2', 'curl', 'software-properties-common'
            ], check=True)
            
            # Add Algorand repository
            key_process = subprocess.run(
                ['curl', '-o', '-', 'https://releases.algorand.com/key.pub'],
                capture_output=True,
                check=True
            )
            subprocess.run(
                ['sudo', 'tee', '/etc/apt/trusted.gpg.d/algorand.asc'],
                input=key_process.stdout,
                check=True
            )
            subprocess.run([
                'sudo', 'add-apt-repository',
                'deb [arch=amd64] https://releases.algorand.com/deb/ stable main'
            ], check=True)
            
            # Update and install
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run([
                'sudo', 'apt-get', 'install', '-y', 'algorand-devtools'
            ], check=True)
            
            # Set environment variable
            bashrc_path = os.path.expanduser('~/.bashrc')
            env_var = '\nexport ALGORAND_DATA=/var/lib/algorand\n'
            with open(bashrc_path, 'a') as f:
                if env_var not in open(bashrc_path).read():
                    f.write(env_var)
            
            # Start and enable service
            subprocess.run(['sudo', 'systemctl', 'start', 'algorand'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'algorand'], check=True)
            
            # Configure telemetry after node is running
            self._configure_telemetry()
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Installation failed during step: {e.cmd}")
            self.logger.error(f"Error code: {e.returncode}")
            self.logger.error(f"Error output: {e.output if hasattr(e, 'output') else 'No error output available'}")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error during installation: {str(e)}")
            return False

def print_usage_info():
    """Print helpful usage information after successful installation."""
    print("\nAlgorand Node Installation Complete!")
    print("\nImportant Notes:")
    print("1. Node is installed and running at /var/lib/algorand")
    print("2. Environment variable ALGORAND_DATA has been set")
    print("3. Telemetry is disabled by default")
    print("\nTo enable telemetry:")
    print("  sudo -u algorand -H -E diagcfg telemetry name -n <hostname>")
    print("  sudo systemctl restart algorand")
    print("\nUseful Commands:")
    print("- Node status: goal node status -d /var/lib/algorand")
    print("- Service control: sudo systemctl start/stop/restart algorand")
    print("- Wallet operations: sudo -u algorand -E goal account listpartkeys")

def main():
    """Main entry point for the installer."""
    installer = AlgorandInstaller()
    success = installer.run_installation()
    if success:
        print_usage_info()
        return 0
    print("\nInstallation failed. Check logs for details.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
