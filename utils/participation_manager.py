# utils/participation_manager.py
import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class ParticipationManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        
    def generate_participation_key(self, 
                                 address: str,
                                 first_round: int,
                                 last_round: int,
                                 key_dilution: Optional[int] = None) -> bool:
        """
        Generate participation key for an account.
        
        Args:
            address: Account address
            first_round: First valid round
            last_round: Last valid round
            key_dilution: Optional key dilution parameter
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = [
                'goal', 'account', 'addpartkey',
                '-a', address,
                '--roundFirstValid', str(first_round),
                '--roundLastValid', str(last_round)
            ]
            
            if key_dilution:
                cmd.extend(['--keyDilution', str(key_dilution)])
            
            # Add data directory
            cmd.extend(['-d', str(self.data_dir)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Generated participation key for {address}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate participation key: {e.stderr}")
            return False

    def list_participation_keys(self) -> Dict[str, Dict]:
        """List all participation keys on the node."""
        try:
            cmd = ['goal', 'account', 'listpartkeys', '-d', str(self.data_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the output
            keys = {}
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                if line:
                    parts = line.split()
                    keys[parts[1]] = {
                        'registered': parts[0] == 'yes',
                        'participation_id': parts[2],
                        'first_round': int(parts[4]),
                        'last_round': int(parts[5])
                    }
            
            return keys
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list participation keys: {e.stderr}")
            return {}

    def register_online(self, address: str) -> bool:
        """
        Register an account online.
        
        Args:
            address: Account address to register online
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = [
                'goal', 'account', 'changeonlinestatus',
                '--address', address,
                '--online',
                '--transaction-file', str(self.data_dir / 'online.txn'),
                '-d', str(self.data_dir)
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Created online registration transaction for {address}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create online registration: {e.stderr}")
            return False

    def register_offline(self, address: str) -> bool:
        """
        Register an account offline.
        
        Args:
            address: Account address to register offline
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = [
                'goal', 'account', 'changeonlinestatus',
                '--address', address,
                '--offline',
                '--transaction-file', str(self.data_dir / 'offline.txn'),
                '-d', str(self.data_dir)
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Created offline registration transaction for {address}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create offline registration: {e.stderr}")
            return False

    def check_participation_status(self, address: str) -> Optional[bool]:
        """
        Check if an account is participating.
        
        Args:
            address: Account address to check
            
        Returns:
            Optional[bool]: True if online, False if offline, None if error
        """
        try:
            cmd = ['goal', 'account', 'dump', '-a', address, '-d', str(self.data_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse JSON output
            data = json.loads(result.stdout)
            return data.get('onl', False)
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to check participation status: {str(e)}")
            return None
