"""
Configuration settings for the application.
Provides different configuration classes for different environments.
"""
import os
from pathlib import Path

class BaseConfig:
    """Base configuration with common settings."""
    
    # Project structure
    PROJECT_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    APP_DIR = PROJECT_ROOT / "app"
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"
    MODELS_DIR = PROJECT_ROOT / "models"
    ANALYSIS_DIR = PROJECT_ROOT / "analysis"
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    
    # Database
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASEDIR, '../../betting_data.db')
    
    # Caching
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Scraping
    PAGE_LOAD_WAIT = int(os.environ.get('PAGE_LOAD_WAIT', '10'))
    TARGET_URL = os.environ.get('TARGET_URL', 'https://oddsjam.com/positive-ev')
    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', '300'))  # 5 minutes
    
    # Backup
    BACKUP_DIR = APP_DIR / 'backups'
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '7'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', '7'))
    
    # Chrome
    CHROME_PROFILE = Path(os.path.expanduser('~')) / 'Library/Application Support/Google/Chrome/ScraperProfile'
    CHROME_OPTIONS = [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--disable-blink-features=AutomationControlled'
    ]
    
    # Selectors for scraping
    SELECTORS = {
        'bet_blocks': "div#betting-tool-table-row",
        'ev_percent': "p#percent-cell",
        'event_time': "div[data-testid='event-cell'] > p.text-xs",
        'participant': "p.text-sm.font-semibold",
        'sport': "p.text-sm:not(.font-semibold)",
        'league': "p.text-sm:not(.font-semibold)",
        'bet_type': "p.text-sm.text-brand-purple",
        'description': "div.tour__bet_and_books p.flex-1",
        'odds': "p.text-sm.font-bold",
        'sportsbook': "img[alt]",
        'bet_size': "p.text-sm.__className_179fbf.self-center.font-semibold.text-white",
        'win_probability': "p.text-sm.text-white:last-child"
    }
    
    # Model settings
    MODEL_SETTINGS = {
        'min_samples_for_training': 1000,
        'test_size': 0.2,
        'random_state': 42,
        'cv_folds': 5,
        'confidence_threshold': 0.6
    }
    
    # Feature engineering settings
    FEATURE_SETTINGS = {
        'rolling_window_sizes': [5, 10, 20],
        'min_games_for_stats': 5,
        'max_games_for_stats': 82
    }

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    CACHE_TYPE = "simple"
    LOG_LEVEL = "DEBUG"
    
    # Development database
    DATABASE_PATH = os.path.join(BaseConfig.BASEDIR, '../../dev_betting_data.db')

class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    
    # Test database
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests
    
    # Test-specific settings
    CACHE_TYPE = "null"
    LOG_LEVEL = "DEBUG"
    PAGE_LOAD_WAIT = 1
    SCRAPE_INTERVAL = 10

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production settings must be set via environment variables
    # Provide a fallback for SECRET_KEY, but log a warning if it's not set
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    
    # Production-specific settings
    CACHE_TYPE = "simple"  # Use simple cache for Vercel
    LOG_LEVEL = "INFO"
    LOG_TO_STDOUT = True  # Vercel logs to stdout
    
    # Vercel-specific settings
    IS_VERCEL = os.environ.get('VERCEL', False)
    VERCEL_ENV = os.environ.get('VERCEL_ENV', 'development')
    
    def __init__(self):
        """Initialize the production configuration."""
        super().__init__()
        # Log a warning if SECRET_KEY is not set
        if os.environ.get('SECRET_KEY') is None:
            import logging
            logging.warning("SECRET_KEY is not set in environment variables. Using default value, which is not secure for production.")

# Dictionary to map environment names to config classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])() 