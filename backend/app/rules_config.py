"""
Portfolio Rules Configuration Loader

Loads and validates portfolio evaluation rules from YAML configuration.
"""
import yaml
import os
from typing import Dict, Any
from pathlib import Path


class RulesConfig:
    """Singleton configuration loader for portfolio rules."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load rules from YAML file."""
        config_path = Path(__file__).parent.parent / "config" / "portfolio_rules.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Rules config not found at {config_path}")
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    @property
    def concentration(self) -> Dict[str, Any]:
        """Get concentration risk rules."""
        return self._config.get("concentration", {})
    
    @property
    def diversification(self) -> Dict[str, Any]:
        """Get diversification rules."""
        return self._config.get("diversification", {})
    
    @property
    def asset_allocation(self) -> Dict[str, Any]:
        """Get asset allocation rules."""
        return self._config.get("asset_allocation", {})
    
    @property
    def fund_overlap(self) -> Dict[str, Any]:
        """Get fund overlap detection rules."""
        return self._config.get("fund_overlap", {})
    
    @property
    def performance(self) -> Dict[str, Any]:
        """Get performance analysis rules."""
        return self._config.get("performance", {})
    
    @property
    def health_score(self) -> Dict[str, Any]:
        """Get health score calculation rules."""
        return self._config.get("health_score", {})
    
    def get_all(self) -> Dict[str, Any]:
        """Get all rules."""
        return self._config


# Global instance
rules = RulesConfig()
