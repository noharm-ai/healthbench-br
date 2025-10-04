"""Configuration loader for providers"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ProviderConfigItem:
    """Configuration for a single provider"""
    name: str
    type: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    region: Optional[str] = "us-east-1"
    aws_bearer_token: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 12000
    timeout: int = 120
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigSettings:
    """Global configuration settings"""
    temperature: float = 0.0
    max_tokens: int = 12000
    timeout: int = 120
    parallelism: int = 10


class ConfigLoader:
    """Loads and manages provider configurations"""
    
    def __init__(self, config_path: str = "providers.json"):
        self.config_path = Path(config_path)
        self.providers: List[ProviderConfigItem] = []
        self.default_settings: ConfigSettings = ConfigSettings()
        self._load_config()
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """Substitute environment variables in configuration values"""
        if isinstance(value, str):
            # Find all ${VAR_NAME} patterns
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, value)
            
            for var_name in matches:
                env_value = os.environ.get(var_name)
                if env_value:
                    value = value.replace(f'${{{var_name}}}', env_value)
                else:
                    # Keep the placeholder if env var not found
                    pass
            
            # Return None if the value is still a placeholder
            if value.startswith('${') and value.endswith('}'):
                return None
                
        return value
    
    def _process_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process a configuration dictionary to substitute env vars"""
        processed = {}
        for key, value in config_dict.items():
            if isinstance(value, dict):
                processed[key] = self._process_config_dict(value)
            elif isinstance(value, list):
                processed[key] = [
                    self._process_config_dict(item) if isinstance(item, dict) 
                    else self._substitute_env_vars(item) 
                    for item in value
                ]
            else:
                processed[key] = self._substitute_env_vars(value)
        return processed
    
    def _load_config(self):
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Process environment variables
        config_data = self._process_config_dict(config_data)
        
        # Load default settings
        if 'default_settings' in config_data:
            settings = config_data['default_settings']
            self.default_settings = ConfigSettings(
                temperature=settings.get('temperature', 0.0),
                max_tokens=settings.get('max_tokens', 12000),
                timeout=settings.get('timeout', 120),
                parallelism=settings.get('parallelism', 10)
            )
        
        # Load providers
        if 'providers' not in config_data:
            raise ValueError("Configuration must contain 'providers' key")
        
        for provider_data in config_data['providers']:
            # Merge with default settings
            provider_config = ProviderConfigItem(
                name=provider_data['name'],
                type=provider_data['type'],
                model=provider_data['model'],
                api_key=provider_data.get('api_key'),
                base_url=provider_data.get('base_url'),
                region=provider_data.get('region', 'us-east-1'),
                aws_bearer_token=provider_data.get('aws_bearer_token'),
                temperature=provider_data.get('temperature', self.default_settings.temperature),
                max_tokens=provider_data.get('max_tokens', self.default_settings.max_tokens),
                timeout=provider_data.get('timeout', self.default_settings.timeout)
            )
            
            # Store any extra parameters
            known_keys = {
                'name', 'type', 'model', 'api_key', 'base_url', 
                'region', 'aws_bearer_token', 'temperature', 'max_tokens', 'timeout'
            }
            for key, value in provider_data.items():
                if key not in known_keys:
                    provider_config.extra_params[key] = value
            
            self.providers.append(provider_config)
    
    def get_provider(self, name: str) -> Optional[ProviderConfigItem]:
        """Get a specific provider configuration by name"""
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None
    
    def get_providers_by_type(self, provider_type: str) -> List[ProviderConfigItem]:
        """Get all providers of a specific type"""
        return [p for p in self.providers if p.type == provider_type]
    
    def list_providers(self) -> List[str]:
        """List all available provider names"""
        return [p.name for p in self.providers]
    
    def validate_provider(self, provider: ProviderConfigItem) -> List[str]:
        """Validate a provider configuration and return list of issues"""
        issues = []
        
        # Check required fields based on provider type
        if provider.type in ['openai', 'maritaca']:
            if not provider.api_key:
                issues.append(f"API key missing for {provider.name} (type: {provider.type})")
        
        if provider.type == 'aws_bedrock':
            if not provider.aws_bearer_token:
                issues.append(f"AWS bearer token missing for {provider.name}")
        
        if provider.type == 'ollama':
            if not provider.base_url:
                issues.append(f"Base URL missing for {provider.name} (type: ollama)")
        
        return issues
    
    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all provider configurations"""
        validation_results = {}
        for provider in self.providers:
            issues = self.validate_provider(provider)
            if issues:
                validation_results[provider.name] = issues
        return validation_results