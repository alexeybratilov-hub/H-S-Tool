"""
Configuration Loader

Loads settings from YAML configuration files and environment variables.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from hs_tool.config.settings import (
    Settings,
    AppSettings,
    DatabaseSettings,
    LLMSettings,
    PathSettings,
    SecuritySettings,
)


class ConfigLoader:
    """
    Configuration loader that reads settings from YAML files.
    
    Supports loading from multiple files with precedence:
    1. Environment variables (highest priority)
    2. User config file (~/.config/hs_tool/settings.yaml)
    3. Project config file (00_SYS/config/app_settings.yaml)
    4. Default values (lowest priority)
    """
    
    DEFAULT_CONFIG_PATH = Path("00_SYS/config/app_settings.yaml")
    USER_CONFIG_PATH = Path.home() / ".config" / "hs_tool" / "settings.yaml"
    
    def __init__(self, config_path: Optional[Union[Path, str]] = None):
        """
        Initialize the config loader.
        
        Args:
            config_path: Optional path to configuration file.
                        If None, uses default paths.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.DEFAULT_CONFIG_PATH
        
        self._loaded_files: list[Path] = []
        self._data: Dict[str, Any] = {}
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from files.
        
        Returns:
            Dictionary containing merged configuration from all loaded files.
        """
        self._data = {}
        self._loaded_files = []
        
        # Load from default paths
        paths_to_try = [
            self.config_path,
            self.USER_CONFIG_PATH,
            self.DEFAULT_CONFIG_PATH,
        ]
        
        for path in paths_to_try:
            if path.exists():
                self._load_file(path)
        
        return self._data
    
    def _load_file(self, path: Path) -> None:
        """Load a single configuration file."""
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        if isinstance(data, dict):
            self._deep_merge(self._data, data)
            self._loaded_files.append(path)
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get_loaded_files(self) -> list[Path]:
        """Get list of loaded configuration files."""
        return self._loaded_files.copy()
    
    def to_settings(self) -> Settings:
        """
        Convert loaded data to Settings instance.
        
        Returns:
            Settings instance populated with loaded configuration.
        """
        # Set config file info
        settings_data = {
            "config_file_loaded": len(self._loaded_files) > 0,
            "config_file_path": self._loaded_files[0] if self._loaded_files else None,
        }
        
        # Merge loaded data
        settings_data.update(self._data)
        
        return Settings(**settings_data)


def load_settings(config_path: Optional[Union[Path, str]] = None) -> Settings:
    """
    Load settings from configuration files and environment variables.
    
    This function provides backward compatibility with the legacy
    `ot_agent/config.py` module.
    
    Args:
        config_path: Optional path to configuration file.
                    If None, uses default paths.
    
    Returns:
        Settings instance with loaded configuration.
    
    Example:
        from hs_tool.config import load_settings
        
        settings = load_settings()
        print(settings.app.app_name)
        print(settings.database.database_path)
    """
    loader = ConfigLoader(config_path)
    loader.load()
    return loader.to_settings()


def load_app_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load app settings from YAML file (legacy compatibility).
    
    This function provides backward compatibility with the legacy
    `ot_agent/config.load_app_settings()` function.
    
    Args:
        path: Optional path to configuration file.
    
    Returns:
        Dictionary with configuration data.
    """
    config_path = path or ConfigLoader.DEFAULT_CONFIG_PATH
    
    if not config_path.exists():
        return {}
    
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    
    return data if isinstance(data, dict) else {}


def get_config_path() -> Path:
    """
    Get the default configuration file path.
    
    Returns:
        Path to the default configuration file.
    """
    return ConfigLoader.DEFAULT_CONFIG_PATH
