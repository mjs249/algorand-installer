# utils/config_manager.py
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AlgorandConfig:
    """Manages Algorand node configuration settings."""
    
    DEFAULT_CONFIG = {
        "Version": 34,
        "GossipFanout": 4,
        "NetAddress": "",  # Will be set based on node type
        "BaseLoggerDebugLevel": 4,
        "IncomingConnectionsLimit": 2400,
        "Archival": False,
        "EnableMetricReporting": False,
        "EnableDeveloperAPI": False,
        "EnableProfiler": False,
        "EndpointAddress": "127.0.0.1:8080",
        "RestReadTimeoutSeconds": 15,
        "RestWriteTimeoutSeconds": 120,
        "RunHosted": False,
        "SuggestedFeeBlockHistory": 3,
        "TxPoolSize": 75000,
        "EnableLedgerService": False,
        "EnableBlockService": False,
        "EnableGossipBlockService": True,
        "CatchupBlockFetchTimeoutSec": 4,
        "DeadlockDetection": 0,
        "DNSBootstrapID": "<network>.algorand.network",
        "EnableTelemetry": False,
        "TelemetryURI": "",
        "EnableAPIAuth": True,
        "NodeExporterListenAddress": "",
        "CatchupParallelBlocks": 16,
    }
    
    RELAY_SPECIFIC_CONFIG = {
        "NetAddress": ":4160",  # For MainNet
        "IncomingConnectionsLimit": 10000,
        "Archival": True,
        "EnableBlockService": True,
        "EnableLedgerService": True,
    }
    
    def __init__(self, data_dir: Path, is_relay: bool = False):
        self.data_dir = data_dir
        self.config_file = data_dir / 'config.json'
        self.is_relay = is_relay
        self.config = self.DEFAULT_CONFIG.copy()
        
        if is_relay:
            self.config.update(self.RELAY_SPECIFIC_CONFIG)
    
    def load_existing_config(self) -> bool:
        """Load existing configuration if available."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    existing_config = json.load(f)
                    self.config.update(existing_config)
                return True
        except Exception as e:
            logger.error(f"Failed to load existing config: {str(e)}")
        return False
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(updates)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            return False
    
    def configure_telemetry(self, 
                          enable: bool = False,
                          hostname: Optional[str] = None) -> None:
        """Configure telemetry settings."""
        telemetry_config = {
            "Enable": enable,
            "SendToLog": True,
            "URI": "",  # Default Algorand telemetry server
            "MinLogLevel": 4,
            "ReportHistoryLevel": 4,
        }
        
        if hostname:
            telemetry_config["Name"] = hostname
        
        # Save telemetry config
        telemetry_file = self.data_dir / 'logging.config'
        try:
            with open(telemetry_file, 'w') as f:
                json.dump(telemetry_config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save telemetry config: {str(e)}")
    
    def configure_kmd(self, 
                     port: int = 7833,
                     token_validity_mins: int = 60) -> None:
        """Configure kmd settings."""
        kmd_config = {
            "address": f"127.0.0.1:{port}",
            "allowed_origins": [],
            "session_lifetime_secs": token_validity_mins * 60
        }
        
        # Save kmd config
        kmd_config_file = self.data_dir / 'kmd-v0.5' / 'kmd_config.json'
        try:
            kmd_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(kmd_config_file, 'w') as f:
                json.dump(kmd_config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save kmd config: {str(e)}")
