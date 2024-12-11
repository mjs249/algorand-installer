# main.py

import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
import json
import uuid

class AlgorandInstaller:
    def __init__(self):
        """Initialize the Algorand node installer."""
        self.config = {
            'data_dir': '/var/lib/algorand',
            'logging_config': {
                'Enable': False,
                'SendToLog': True,
                'URI': '',  # Default Algorand telemetry endpoint
                'Name': os.uname()[1],  # Default to system hostname
                'GUID': str(uuid.uuid4()),  # Generate unique identifier
                'MinLogLevel': 2,  # Info level
                'ReportHistoryLevel': 3,  # Warning level
                'FilePath': '',  # Will be set during configuration
                'UserName': '',  # Default empty for Algorand hosted endpoint
                'Password': ''   # Default empty for Algorand hosted endpoint
            }
        }
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _configure_telemetry(self) -> None:
        """Configure telemetry settings for the node."""
        try:
            self.logger.info("Setting up telemetry configuration...")
            
            # Create global config directory
            global_config_dir = Path.home() / '.algorand'
            global_config_dir.mkdir(parents=True, exist_ok=True)
            global_config_file = global_config_dir / 'logging.config'
            
            # Create node-specific config directory
            node_config_dir = Path(self.config['data_dir'])
            node_config_file = node_config_dir / 'logging.config'
            
            # Update config files
            for config_path in [global_config_file, node_config_file]:
                self.config['logging_config']['FilePath'] = str(config_path)
                config_content = self.config['logging_config'].copy()
                
                # Write config with proper permissions
                if config_path == node_config_file:
                    # Write to temporary file first for node config
                    temp_path = Path('/tmp/logging.config.tmp')
                    with open(temp_path, 'w') as f:
                        json.dump(config_content, f, indent=2)
                    
                    # Move to final location with proper ownership
                    subprocess.run([
                        'sudo', 'mv', str(temp_path), str(config_path)
                    ], check=True)
                    
                    subprocess.run([
                        'sudo', 'chown', 'algorand:algorand', str(config_path)
                    ], check=True)
                    
                    subprocess.run([
                        'sudo', 'chmod', '644', str(config_path)
                    ], check=True)
                else:
                    # Global config can be written directly
                    with open(config_path, 'w') as f:
                        json.dump(config_content, f, indent=2)
            
            # Disable telemetry initially using diagcfg
            self.logger.info("Initializing telemetry settings...")
            subprocess.run([
                'sudo', '-u', 'algorand', '-H', '-E',
                'diagcfg', 'telemetry', 'disable'
            ], check=True)
            
            # Verify telemetry configuration
            self.logger.info("Verifying telemetry configuration...")
            result = subprocess.run([
                'sudo', '-u', 'algorand', '-H', '-E',
                'diagcfg', 'telemetry'
            ], capture_output=True, text=True, check=True)
            
            if "is disabled" not in result.stdout:
                raise Exception("Telemetry verification failed")
            
            # Restart node to apply telemetry settings
            self.logger.info("Restarting node to apply telemetry settings...")
            subprocess.run(['sudo', 'systemctl', 'restart', 'algorand'], check=True)
            
            # Wait for service to fully start
            subprocess.run(['sleep', '5'], check=True)
            
            # Verify service is running
            result = subprocess.run([
                'sudo', 'systemctl', 'status', 'algorand'
            ], capture_output=True, text=True)
            if "active (running)" not in result.stdout:
                raise Exception("Node failed to restart after telemetry configuration")
                
        except Exception as e:
            self.logger.error(f"Failed to configure telemetry: {str(e)}")
            raise

    def run_installation(self) -> bool:
        """Run the Ubuntu-specific installation process."""
        try:
            # System updates
            self.logger.info("Updating system packages...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            
            # Install prerequisites
            self.logger.info("Installing prerequisites...")
            subprocess.run([
                'sudo', 'apt-get', 'install', '-y',
                'gnupg2', 'curl', 'software-properties-common'
            ], check=True)
            
            # Add Algorand repository key
            self.logger.info("Adding Algorand repository key...")
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
            
            # Add repository
            self.logger.info("Adding Algorand repository...")
            subprocess.run([
                'sudo', 'add-apt-repository',
                'deb [arch=amd64] https://releases.algorand.com/deb/ stable main'
            ], check=True)
            
            # Update again after adding repo
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            
            # Install Algorand with devtools
            self.logger.info("Installing Algorand and developer tools...")
            subprocess.run([
                'sudo', 'apt-get', 'install', '-y', 'algorand-devtools'
            ], check=True)
            
            # Set environment variable
            self.logger.info("Setting up environment variables...")
            bashrc_path = os.path.expanduser('~/.bashrc')
            env_var = '\nexport ALGORAND_DATA=/var/lib/algorand\n'
            with open(bashrc_path, 'a') as f:
                if env_var not in open(bashrc_path).read():
                    f.write(env_var)
            
            # Start and enable service
            self.logger.info("Starting Algorand service...")
            subprocess.run(['sudo', 'systemctl', 'start', 'algorand'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'algorand'], check=True)
            
            # Wait for service to fully start before configuring telemetry
            subprocess.run(['sleep', '5'], check=True)
            
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
    print("\nTo enable telemetry with hostname:")
    print("  sudo -u algorand -H -E diagcfg telemetry name -n <hostname>")
    print("  sudo systemctl restart algorand")
    print("\nTo enable telemetry without hostname:")
    print("  sudo -u algorand -H -E diagcfg telemetry enable")
    print("  sudo systemctl restart algorand")
    print("\nTo check telemetry status:")
    print("  sudo -u algorand -H -E diagcfg telemetry")
    print("  sudo netstat -an | grep :9243")
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
