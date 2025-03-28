"""
Application settings and environment configuration.

CurAIos - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json

_settings = None


@dataclass
class Settings:
    # LLM Configuration
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-4"
    llm_embedding_model: str = "openai/text-embedding-ada-002"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1000
    
    # External API Configuration
    ncbi_api_key: str = ""
    ncbi_email: str = ""
    ncbi_tool: str = "CurAIos"
    ncbi_rate_limit: float = 0.34  # Requests per second (3 per 10 seconds)
    
    cache_enabled: bool = True
    cache_dir: str = "data/cache"
    cache_ttl: int = 86400  # 24 hours in seconds
    
    output_dir: str = "data/output"
    default_output_format: str = "json"
    
    fuzzy_threshold: float = 0.85
    semantic_threshold: float = 0.75
    
    log_level: str = "INFO"
    log_file: str = "CurAIos.log"
    
    # Plugin Configuration
    plugins_enabled: bool = True
    plugins_dir: str = "plugins"
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        settings = cls()
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        return settings


def load_env_settings() -> Dict[str, Any]:
    env_settings = {}
    
    # LLM settings
    # Look for OPENROUTER_API_KEY first, then fall back to BIODATA_LLM_API_KEY
    env_settings["llm_api_key"] = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("BIODATA_LLM_API_KEY", "")
    env_settings["llm_model"] = os.environ.get("BIODATA_LLM_MODEL", "deepseek/deepseek-chat")
    
    # NCBI settings
    env_settings["ncbi_api_key"] = os.environ.get("BIODATA_NCBI_API_KEY", "")
    env_settings["ncbi_email"] = os.environ.get("BIODATA_NCBI_EMAIL", "")
    
    env_settings["log_level"] = os.environ.get("BIODATA_LOG_LEVEL", "INFO")
    
    return {k: v for k, v in env_settings.items() if v}


def load_config_file(config_path: str = None) -> Dict[str, Any]:
    if not config_path:
        config_path = os.environ.get("BIODATA_CONFIG", "config/config.json")
    
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load config file {config_path}: {e}")
        return {}


def init_settings(config_path: Optional[str] = None) -> None:
    global _settings

    settings_dict = Settings().to_dict()
    
    config_settings = load_config_file(config_path)
    settings_dict.update(config_settings)
    
    env_settings = load_env_settings()
    settings_dict.update(env_settings)
    
    _settings = Settings.from_dict(settings_dict)
    
    os.makedirs(_settings.cache_dir, exist_ok=True)
    os.makedirs(_settings.output_dir, exist_ok=True)


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        init_settings()
    return _settings
