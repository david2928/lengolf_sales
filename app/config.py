#!/usr/bin/env python3

import os
import logging
from typing import Optional
from zoneinfo import ZoneInfo

# Set timezone to Bangkok
TIMEZONE = ZoneInfo("Asia/Bangkok")

def load_env_file():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

class Config:
    """Application configuration"""
    
    def __init__(self):
        # Load environment variables first
        load_env_file()
        
        # Supabase configuration
        self.supabase_url = self._get_env_var('SUPABASE_URL')
        self.supabase_key = self._get_env_var('SUPABASE_SERVICE_KEY')
        
        # Qashier configuration
        self.qashier_username = self._get_env_var('QASHIER_USERNAME')
        self.qashier_password = self._get_env_var('QASHIER_PASSWORD')
        
        # App configuration
        self.port = int(os.getenv('PORT', '8080'))
        self.host = os.getenv('HOST', '0.0.0.0')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        self._setup_logging()
    
    def _get_env_var(self, key: str) -> str:
        """Get environment variable and strip quotes if present"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Missing required environment variable: {key}")
        
        # Strip quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        return value
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @property
    def qashier_base_url(self) -> str:
        """Qashier base URL"""
        return "https://hq.qashier.com/#/login"
    
    @property
    def qashier_transactions_url(self) -> str:
        """Qashier transactions URL"""
        return "https://hq.qashier.com/#/transactions"

# Global config instance
config = Config() 