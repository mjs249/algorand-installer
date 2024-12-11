# main.py
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json
import shutil

class AlgorandInstaller:
    def __init__(self):
        """Initialize the Algorand node installer."""
        self.config: Dict[str, Any] = {
            'install_dir': Path.home() / 'algorand',
            'data_dir': Path.home() / 'algorand' / 'data',
            'bin_dir': Path.home() / 'algorand' / 'bin',
            'network': 'mainnet',
            'version': 'stable',
            'is_relay': False,
            'is_archival': False,
            'enable_telemetry': False
        }
        
        # Initialize components
        self._setup_logging()
        self._load_or_create_config()
        
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            from utils.logging_config import setup_logging
            self.logger = setup_logging(self.config['install_dir'])
        except Exception:
            # Fallback to basic logging if custom logging setup fails
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger(__name__)

    def _load_or_create_config(self) -> None:
        """Load existing config or create default one."""
        config_file = self.config['install_dir'] / 'installer_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {str(e)}")

    def save_config(self) -> None:
        """Save current configuration."""
        config_file = self.config['install_dir'] / 'installer_config.json'
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")

    def run_installation(self) -> bool:
        """Run the complete installation process."""
        try:
            # Create directories
            self._create_directories()
            
            # Run system checks
            self._run_checks()
            
            # Install dependencies
            self._install_dependencies()
            
            # Configure node
            self._configure_node()
            
            # Install Algorand binaries
            self._install_binaries()
            
            # Setup network
            self._setup_network()
            
            # Configure services
            self._configure_services()
            
            # Start node
            self._start_node()
            
            self.logger.info("Installation completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {str(e)}")
            return False

    def _create_directories(self) -> None:
        """Create required directories."""
        try:
            self.config['install_dir'].mkdir(parents=True, exist_ok=True)
            self.config['data_dir'].mkdir(parents=True, exist_ok=True)
            self.config['bin_dir'].mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create directories: {str(e)}")

    def _run_checks(self) -> None:
        """Run all preliminary checks."""
        try:
            from utils.system_checks import check_system_requirements
            from utils.permissions import check_user_permissions
            
            self.logger.info("Running system checks...")
            check_system_requirements()
            check_user_permissions(self.config['install_dir'])
            
        except ImportError as e:
            raise Exception(f"Failed to import check modules: {str(e)}")
        except Exception as e:
            raise Exception(f"System checks failed: {str(e)}")

    def _install_dependencies(self) -> None:
        """Install required dependencies."""
        try:
            from utils.dependencies import check_dependencies
            
            self.logger.info("Installing dependencies...")
            check_dependencies()
            
        except Exception as e:
            raise Exception(f"Failed to install dependencies: {str(e)}")

    def _configure_node(self) -> None:
        """Configure the Algorand node."""
        try:
            from utils.config_manager import AlgorandConfig
            
            self.logger.info("Configuring node...")
            config_manager = AlgorandConfig(
                self.config['data_dir'],
                is_relay=self.config['is_relay']
            )
            
            # Update configuration based on node type
            if self.config['is_archival']:
                config_manager.update_config({"Archival": True})
            
            # Configure telemetry if enabled
            if self.config['enable_telemetry']:
                config_manager.configure_telemetry(enable=True)
            
            # Save configuration
            config_manager.save_config()
            
        except Exception as e:
            raise Exception(f"Failed to configure node: {str(e)}")

    def _install_binaries(self) -> None:
        """Install Algorand binaries."""
        try:
            self.logger.info("Installing Algorand binaries...")
            
            # Add Algorand repository
            subprocess.run([
                'curl', '-O', 'https://releases.algorand.com/key.pub'
            ], check=True)
            
            subprocess.run([
                'sudo', 'apt-key', 'add', 'key.pub'
            ], check=True)
            
            subprocess.run([
                'sudo', 'add-apt-repository',
                'deb [arch=amd64] https://releases.algorand.com/deb/ stable main'
            ], check=True)
            
            # Install Algorand
            subprocess.run([
                'sudo', 'apt-get', 'update'
            ], check=True)
            
            subprocess.run([
                'sudo', 'apt-get', 'install', '-y', 'algorand'
            ], check=True)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install Algorand: {str(e)}")

    def _setup_network(self) -> None:
        """Configure network settings."""
        try:
            from utils.network_manager import NetworkManager
            
            self.logger.info(f"Setting up {self.config['network']}...")
            network_manager = NetworkManager(self.config['data_dir'])
            network_manager.setup_network(self.config['network'])
            
        except Exception as e:
            raise Exception(f"Failed to setup network: {str(e)}")

    def _configure_services(self) -> None:
        """Configure system services."""
        try:
            self.logger.info("Configuring services...")
            
            # Create systemd service file
            service_content = f"""[Unit]
Description=Algorand Node
After=network.target

[Service]
ExecStart=/usr/bin/algod -d {self.config['data_dir']}
PIDFile={self.config['data_dir']}/algod.pid
User={os.getenv('USER')}
Group={os.getenv('USER')}
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
            
            # Write service file
            service_path = Path('/etc/systemd/system/algorand.service')
            if not service_path.exists():
                with open('algorand.service', 'w') as f:
                    f.write(service_content)
                    
                subprocess.run([
                    'sudo', 'mv', 'algorand.service',
                    '/etc/systemd/system/algorand.service'
                ], check=True)
                
                subprocess.run([
                    'sudo', 'systemctl', 'daemon-reload'
                ], check=True)
                
        except Exception as e:
            raise Exception(f"Failed to configure services: {str(e)}")

    def _start_node(self) -> None:
        """Start the Algorand node."""
        try:
            self.logger.info("Starting Algorand node...")
            
            subprocess.run([
                'sudo', 'systemctl', 'enable', 'algorand'
            ], check=True)
            
            subprocess.run([
                'sudo', 'systemctl', 'start', 'algorand'
            ], check=True)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to start node: {str(e)}")

def main():
    """Main entry point for the installer."""
    installer = AlgorandInstaller()
    success = installer.run_installation()
    
    if success:
        print("\nAlgorand node installation completed successfully!")
        print("\nUseful commands:")
        print("- Check node status: goal node status")
        print("- Stop node: sudo systemctl stop algorand")
        print("- Start node: sudo systemctl start algorand")
        print("- View logs: tail -f ~/algorand/data/node.log")
    else:
        print("\nInstallation failed. Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
