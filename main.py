import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
import json
import uuid

class AlgorandInstaller:
    DEFAULT_DATA_DIR = '/var/lib/algorand'  # Ubuntu default path constant

    def __init__(self):
        """Initialize the Algorand node installer."""
        self.config = {
            'data_dir': self.DEFAULT_DATA_DIR,
            'logging_config': {
                'Enable': False,
                'SendToLog': True,
                'URI': '',
                'Name': os.uname()[1],
                'GUID': str(uuid.uuid4()),
                'MinLogLevel': 2,
                'ReportHistoryLevel': 3,
                'FilePath': '',
                'UserName': '',
                'Password': ''
            }
        }
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _configure_telemetry(self) -> None:
        """Configure telemetry settings for the node."""
        try:
            self.logger.info("Setting up telemetry configuration...")
            
            # Ensure data directory exists
            data_dir = Path(self.DEFAULT_DATA_DIR)
            if not data_dir.exists():
                self.logger.error(f"Data directory {data_dir} does not exist!")
                raise FileNotFoundError(f"Data directory {data_dir} not found")
            
            # Create global config directory
            global_config_dir = Path.home() / '.algorand'
            global_config_dir.mkdir(parents=True, exist_ok=True)
            global_config_file = global_config_dir / 'logging.config'
            
            # Update config files
            for config_path in [global_config_file, data_dir / 'logging.config']:
                self.config['logging_config']['FilePath'] = str(config_path)
                config_content = self.config['logging_config'].copy()
                
                if str(config_path).startswith(self.DEFAULT_DATA_DIR):
                    # For system paths, use temporary file and sudo
                    temp_path = '/tmp/logging.config.tmp'
                    with open(temp_path, 'w') as f:
                        json.dump(config_content, f, indent=2)
                    
                    # Move to final location with proper ownership
                    subprocess.run([
                        'sudo', 'cp', temp_path, str(config_path)
                    ], check=True)
                    
                    subprocess.run([
                        'sudo', 'chown', 'algorand:algorand', str(config_path)
                    ], check=True)
                    
                    subprocess.run([
                        'sudo', 'chmod', '644', str(config_path)
                    ], check=True)
                    
                    # Clean up temp file
                    os.remove(temp_path)
                else:
                    # Global config in user's home directory
                    with open(config_path, 'w') as f:
                        json.dump(config_content, f, indent=2)
            
            # Initialize telemetry settings
            self.logger.info("Initializing telemetry settings...")
            result = subprocess.run([
                'sudo', '-u', 'algorand', '-H', '-E',
                'diagcfg', 'telemetry', 'disable',
                '-d', self.DEFAULT_DATA_DIR
            ], capture_output=True, text=True, check=True)
            self.logger.info(f"Telemetry disable result: {result.stdout.strip()}")
            
            # Verify telemetry configuration
            self.logger.info("Verifying telemetry configuration...")
            result = subprocess.run([
                'sudo', '-u', 'algorand', '-H', '-E',
                'diagcfg', 'telemetry',
                '-d', self.DEFAULT_DATA_DIR
            ], capture_output=True, text=True, check=True)
            
            # Check for either format of disabled message
            valid_disabled_messages = [
                "Telemetry logging disabled",
                "Remote logging is currently disabled"
            ]
            
            if not any(msg in result.stdout for msg in valid_disabled_messages):
                self.logger.error(f"Unexpected telemetry output: {result.stdout}")
                raise Exception("Telemetry verification failed - unexpected output")
            
            self.logger.info(f"Telemetry status: {result.stdout.strip()}")
            
            # Restart node to apply settings
            self.logger.info("Restarting node to apply telemetry settings...")
            subprocess.run(['sudo', 'systemctl', 'restart', 'algorand'], check=True)
            
            # Wait for service to start
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
            env_var = f'\nexport ALGORAND_DATA={self.DEFAULT_DATA_DIR}\n'
            with open(bashrc_path, 'a') as f:
                if env_var not in open(bashrc_path).read():
                    f.write(env_var)
            
            # Start and enable service
            self.logger.info("Starting Algorand service...")
            subprocess.run(['sudo', 'systemctl', 'start', 'algorand'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'algorand'], check=True)
            
            # Wait for service to start
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
    print(f"1. Node is installed and running at {AlgorandInstaller.DEFAULT_DATA_DIR}")
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
    print(f"- Node status: goal node status -d {AlgorandInstaller.DEFAULT_DATA_DIR}")
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
