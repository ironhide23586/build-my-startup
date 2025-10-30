"""
Configuration Manager - Centralized config from config.json

All framework components read from this single source of truth.
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration from config.json and environment variables."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    _config_file: str = ""
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from JSON file."""
        # Find config.json
        framework_dir = Path(__file__).parent
        self._config_file = framework_dir / "config.json"
        
        if not self._config_file.exists():
            print(f"⚠️  config.json not found at {self._config_file}", flush=True)
            print("⚠️  Using default configuration", flush=True)
            self._config = self._get_default_config()
            return
        
        try:
            with open(self._config_file, 'r') as f:
                self._config = json.load(f)
            print(f"✅ Configuration loaded from {self._config_file}", flush=True)
        except Exception as e:
            print(f"⚠️  Failed to load config.json: {e}", flush=True)
            print("⚠️  Using default configuration", flush=True)
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config.json doesn't exist."""
        return {
            "api_keys": {},
            "default_models": {
                "code_generation": "gpt-4o-mini",
                "code_review": "gpt-4o-mini",
                "test_generation": "gpt-4o-mini",
                "planning": "gpt-4o",
                "ideation": "gpt-4o",
                "git_commits": "gpt-4o-mini"
            },
            "build_settings": {
                "max_fix_attempts": 3,
                "timeout": 600,
                "enable_git": True,
                "use_ai_commit_messages": True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation.
        
        Examples:
            config.get("api_keys.openai")
            config.get("build_settings.max_fix_attempts")
            config.get("default_models.code_generation")
        """
        keys = key_path.split('.')
        value = self._config
        
        # Check environment variable override first
        env_var = "BUILD_MY_STARTUP_" + "_".join(keys).upper()
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Try to parse as JSON, otherwise return as string
            try:
                return json.loads(env_value)
            except:
                # Handle boolean strings
                if env_value.lower() in ['true', 'false']:
                    return env_value.lower() == 'true'
                # Handle numeric strings
                try:
                    if '.' in env_value:
                        return float(env_value)
                    return int(env_value)
                except:
                    return env_value
        
        # Get from config file
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set config value using dot notation.
        Note: This only updates in-memory config, not the file.
        """
        keys = key_path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def save(self):
        """Save current configuration to config.json."""
        try:
            with open(self._config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            print(f"✅ Configuration saved to {self._config_file}", flush=True)
            return True
        except Exception as e:
            print(f"❌ Failed to save config: {e}", flush=True)
            return False
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider.
        Checks in order: environment variable, config.json, legacy config.py
        """
        # 1. Check environment variables
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "aws": "AWS_ACCESS_KEY_ID"
        }
        
        env_var = env_vars.get(provider)
        if env_var:
            env_value = os.getenv(env_var)
            if env_value:
                return env_value
        
        # 2. Check config.json
        api_key = self.get(f"api_keys.{provider}")
        if api_key:
            return api_key
        
        # 3. Check legacy config.py for OpenAI
        if provider == "openai":
            try:
                from .config import OPENAI_API_KEY
                if OPENAI_API_KEY:
                    return OPENAI_API_KEY
            except:
                pass
        
        return None
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get the configured model for a specific task type."""
        return self.get(f"default_models.{task_type}", "gpt-4o-mini")
    
    def get_build_config(self) -> Dict[str, Any]:
        """Get all build settings as a dictionary."""
        return self.get("build_settings", {})
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return self._config.copy()
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        issues = []
        warnings = []
        
        # Check API keys
        openai_key = self.get_api_key("openai")
        if not openai_key:
            warnings.append("OpenAI API key not configured")
        
        # Check model settings
        for task_type in ["code_generation", "code_review", "ideation"]:
            model = self.get_model_for_task(task_type)
            if not model:
                issues.append(f"No model configured for {task_type}")
        
        # Check paths
        apps_dir = self.get("paths.apps_dir")
        if not apps_dir:
            issues.append("paths.apps_dir not configured")
        
        # Check numeric ranges
        max_fix = self.get("build_settings.max_fix_attempts", 3)
        if not isinstance(max_fix, int) or max_fix < 1:
            issues.append("build_settings.max_fix_attempts must be positive integer")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config_file": str(self._config_file),
            "config_exists": self._config_file.exists()
        }


# Global singleton instance
config = ConfigManager()


# Convenience functions
def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider."""
    return config.get_api_key(provider)


def get_model(task_type: str) -> str:
    """Get model for a task type."""
    return config.get_model_for_task(task_type)


def get_config(key_path: str, default: Any = None) -> Any:
    """Get config value."""
    return config.get(key_path, default)


def validate_config() -> Dict[str, Any]:
    """Validate current configuration."""
    return config.validate()


def reload_config():
    """Reload configuration from file."""
    config.reload()

