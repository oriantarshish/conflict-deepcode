"""
Configuration management for DeepCode
Handles loading and managing configuration from YAML files
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(Path.home() / '.conflict-deepcode' / 'config.yaml')
        self.config_data = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with defaults"""
        default_config = {
            'ollama': {
                'host': 'http://localhost:11434',
                'model': 'deepseek-coder-v2',
                'timeout': 120,
                'num_ctx': 32768,
                'num_predict': 2048,
                'temperature': 0.2,
                'top_p': 0.9,
                'max_tokens': 32768
            },
            'agent': {
                'use_optimized': True,
                'enable_caching': True,
                'enable_streaming': True,
                'parallel_analysis': True,
                'max_context_length': 32768,  # Increased for better context
                'cache_ttl_minutes': 15,
                'max_conversation_history': 50,  # Increased conversation history
                'enable_dangerous_action_confirmation': True  # New setting for user confirmation
            },
            'analyzer': {
                'enable_ast_parsing': True,
                'cache_ttl_minutes': 5,
                'max_complexity_threshold': 50,
                'enable_conflict_detection': True,
                'parallel_processing': True
            },
            'editor': {
                'default': 'code',
                'backup': True,
                'auto_format': True,
                'smart_suggestions': True
            },
            'project': {
                'ignore_patterns': [
                    '.git',
                    'node_modules',
                    '__pycache__',
                    '*.pyc',
                    '.conflict-deepcode'
                ],
                'max_file_size': '5MB',
                'context_lines': 50,
                'auto_analyze_on_edit': True
            },
            'ui': {
                'color_scheme': 'dark',
                'show_progress': True,
                'verbose_errors': False,
                'typing_animation': True,
                'show_performance_stats': True
            },
            'performance': {
                'enable_profiling': False,
                'log_response_times': True,
                'optimize_for_speed': True,
                'memory_limit_mb': 512
            }
        }
        
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                
                # Deep merge user config with defaults
                merged_config = self._deep_merge(default_config, user_config)
                return merged_config
                
            except Exception as e:
                print(f"Warning: Error loading config file {config_file}: {e}")
                return default_config
        else:
            # Create default config file
            self._create_default_config(config_file, default_config)
            return default_config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _create_default_config(self, config_file: Path, default_config: Dict):
        """Create default configuration file"""
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
                
            print(f"Created default config file: {config_file}")
            
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final key
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """Save current configuration to file"""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config_data.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config_data = self._load_config()
    
    def validate(self) -> Dict[str, str]:
        """Validate configuration and return errors"""
        errors = {}
        
        # Validate Ollama settings
        ollama_host = self.get('ollama.host')
        if not ollama_host or not ollama_host.startswith('http'):
            errors['ollama.host'] = 'Must be a valid HTTP URL'
        
        timeout = self.get('ollama.timeout')
        if not isinstance(timeout, int) or timeout < 1:
            errors['ollama.timeout'] = 'Must be a positive integer'
        
        max_tokens = self.get('ollama.max_tokens')
        if not isinstance(max_tokens, int) or max_tokens < 100:
            errors['ollama.max_tokens'] = 'Must be an integer >= 100'
        
        # Validate agent settings
        cache_ttl = self.get('agent.cache_ttl_minutes')
        if not isinstance(cache_ttl, int) or cache_ttl < 1:
            errors['agent.cache_ttl_minutes'] = 'Must be a positive integer'
        
        max_context = self.get('agent.max_context_length')
        if not isinstance(max_context, int) or max_context < 1000:
            errors['agent.max_context_length'] = 'Must be an integer >= 1000'
        
        # Validate analyzer settings
        analyzer_cache_ttl = self.get('analyzer.cache_ttl_minutes')
        if not isinstance(analyzer_cache_ttl, int) or analyzer_cache_ttl < 1:
            errors['analyzer.cache_ttl_minutes'] = 'Must be a positive integer'
        
        complexity_threshold = self.get('analyzer.max_complexity_threshold')
        if not isinstance(complexity_threshold, int) or complexity_threshold < 1:
            errors['analyzer.max_complexity_threshold'] = 'Must be a positive integer'
        
        # Validate project settings
        max_file_size = self.get('project.max_file_size')
        if not isinstance(max_file_size, str):
            errors['project.max_file_size'] = 'Must be a string like "1MB"'
        
        context_lines = self.get('project.context_lines')
        if not isinstance(context_lines, int) or context_lines < 1:
            errors['project.context_lines'] = 'Must be a positive integer'
        
        # Validate performance settings
        memory_limit = self.get('performance.memory_limit_mb')
        if not isinstance(memory_limit, int) or memory_limit < 64:
            errors['performance.memory_limit_mb'] = 'Must be an integer >= 64'
        
        return errors
    
    def get_display_config(self) -> Dict[str, Any]:
        """Get configuration formatted for display"""
        display_config = {}
        
        def flatten_dict(d: Dict, prefix: str = '') -> Dict:
            items = {}
            for key, value in d.items():
                new_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    items.update(flatten_dict(value, new_key))
                else:
                    items[new_key] = value
            return items
        
        return flatten_dict(self.config_data)