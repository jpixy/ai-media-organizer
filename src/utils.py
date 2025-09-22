"""
Utility functions for media organizer
"""

import yaml
import logging
import os
from typing import Dict, Any

def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables
        if 'TMDB_API_KEY' in os.environ:
            config.setdefault('api', {})['tmdb_api_key'] = os.environ['TMDB_API_KEY']
        
        if 'LOCAL_AI_URL' in os.environ:
            config.setdefault('api', {})['local_ai_url'] = os.environ['LOCAL_AI_URL']
        
        return config
    
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise

def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    import os
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    file_handler = logging.FileHandler('logs/media_organizer.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Separate handler for AI responses
    ai_handler = logging.FileHandler('logs/ai_responses.log', encoding='utf-8')
    ai_handler.setLevel(logging.DEBUG)
    ai_handler.setFormatter(detailed_formatter)
    
    # Add AI handler to scanner logger
    ai_logger = logging.getLogger('src.scanner')
    ai_logger.addHandler(ai_handler)
