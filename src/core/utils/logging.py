"""
Logging System for Tactical RPG Engine

Provides structured logging with performance considerations.
Designed to have minimal impact on release builds.
"""

import logging
import sys
import time
from typing import Dict, Any, Optional
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Logger:
    """
    Centralized logging system for the engine.
    
    Provides structured logging with context and performance tracking.
    """
    
    _initialized = False
    _logger = None
    _log_level = LogLevel.INFO
    
    @classmethod
    def initialize(cls, log_level: str = "INFO", log_file: Optional[str] = None):
        """
        Initialize the logging system.
        
        Args:
            log_level: Minimum log level to output
            log_file: Optional file to write logs to
        """
        if cls._initialized:
            return
        
        cls._log_level = LogLevel(log_level.upper())
        
        # Configure Python logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logging.getLogger().addHandler(file_handler)
        
        cls._logger = logging.getLogger("TacticalRPG")
        cls._initialized = True
    
    @classmethod
    def debug(cls, message: str, **kwargs):
        """Log debug message with optional context"""
        if not cls._initialized:
            cls.initialize()
        
        context = cls._format_context(kwargs)
        cls._logger.debug(f"{message}{context}")
    
    @classmethod
    def info(cls, message: str, **kwargs):
        """Log info message with optional context"""
        if not cls._initialized:
            cls.initialize()
        
        context = cls._format_context(kwargs)
        cls._logger.info(f"{message}{context}")
    
    @classmethod
    def warning(cls, message: str, **kwargs):
        """Log warning message with optional context"""
        if not cls._initialized:
            cls.initialize()
        
        context = cls._format_context(kwargs)
        cls._logger.warning(f"{message}{context}")
    
    @classmethod
    def error(cls, message: str, **kwargs):
        """Log error message with optional context"""
        if not cls._initialized:
            cls.initialize()
        
        context = cls._format_context(kwargs)
        cls._logger.error(f"{message}{context}")
    
    @classmethod
    def critical(cls, message: str, **kwargs):
        """Log critical message with optional context"""
        if not cls._initialized:
            cls.initialize()
        
        context = cls._format_context(kwargs)
        cls._logger.critical(f"{message}{context}")
    
    @classmethod
    def _format_context(cls, context: Dict[str, Any]) -> str:
        """Format context dictionary as string"""
        if not context:
            return ""
        
        context_items = [f"{k}={v}" for k, v in context.items()]
        return f" [{', '.join(context_items)}]"