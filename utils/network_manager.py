# utils/network_manager.py
import os
import shutil
import logging
import json
import requests
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)

NetworkType = Literal['mainnet', 'testnet', 'betanet']

class NetworkManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.genesis_dir = data_dir / 'genesis'
        self.config_file = data_dir / 'config.json'
        
        # Genesis file URLs
        self.genesis_urls = {
            'mainnet': 'https://github.com/algorand/go-algorand/blob/master/installer/genesis/mainnet/genesis.json',
            'testnet': 'https://github.com/algorand/go-algorand/blob/master/installer/genesis/testnet/genesis.json',
            'betanet': 'https://github.com/algorand/go-algorand/blob/master/installer/genesis/betanet/genesis.json'
        }

    def setup_network(self, network: NetworkType) -> None:
        """Configure node for specified network."""
        logger.info(f"Setting up {network}...")
        
        try:
            # Create genesis directory
            self.genesis_dir.mkdir(parents=True, exist_ok=True)
            
            # Download and set up genesis files
            self._setup_genesis_files(network)
            
            # Configure network settings
            self._configure_network(network)
            
            logger.info(f"Successfully configured node for {network}")
            
        except Exception as e:
            logger.error(f"Failed to setup {network}: {str(e)}")
            raise Exception(f"Network setup failed: {str(e)}")

    def _setup_genesis_files(self, network: NetworkType) -> None:
        """Download and set up genesis files."""
        try:
            # Create network-specific directory
            network_dir = self.genesis_dir / network
            network_dir.mkdir(parents=True, exist_ok=True)
            
            # Download genesis file
            genesis_path = network_dir / 'genesis.json'
            if not genesis_path.exists():
                logger.info(f"Downloading {network} genesis file...")
                response = requests.get(self.genesis_urls[network])
                response.raise_for_status()
                
                with open(genesis_path, 'w') as f:
                    f.write(response.text)
            
            # Copy to data directory
            shutil.copy2(genesis_path, self.data_dir / 'genesis.json')
            logger.info(f"Genesis file set up for {network}")
            
        except Exception as e:
            raise Exception(f"Failed to setup genesis files: {str(e)}")

    def _configure_network(self, network: NetworkType) -> None:
        """Set network-specific configuration."""
        config = {
            "Version": 12,
            "GossipFanout": 4,
            "NetAddress": "",  # Will be set if this is a relay node
            "DNSBootstrapID": f"{network}.algorand.network"
        }
        
        # Special configuration for betanet
        if network == 'betanet':
            config["DNSBootstrapID"] = "betanet.algodev.network"
        
        # Write config file
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created network configuration for {network}")

    def get_current_network(self) -> Optional[NetworkType]:
        """Determine current network from genesis file."""
        genesis_file = self.data_dir / 'genesis.json'
        if not genesis_file.exists():
            return None
        
        try:
            with open(genesis_file, 'r') as f:
                data = json.load(f)
                network = data.get('network', '').lower()
                if 'mainnet' in network:
                    return 'mainnet'
                elif 'testnet' in network:
                    return 'testnet'
                elif 'betanet' in network:
                    return 'betanet'
        except Exception as e:
            logger.error(f"Failed to read genesis file: {str(e)}")
        
        return None
