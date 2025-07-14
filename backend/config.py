"""
Configuration Module for SecureCart AI Fraud Detection System.
This module manages all application configurations including database settings,
security parameters, ML model configurations, and environment-specific settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    # Connection settings
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'securecart_fraud_detection')
    username: str = os.getenv('DB_USERNAME', 'postgres')
    password: str = os.getenv('DB_PASSWORD', 'password')

    # Connection pool settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))

    # Development settings
    echo: bool = os.getenv('SQL_DEBUG', 'False').lower() == 'true'

    @property
    def url(self) -> str:
        """Get database URL based on environment."""
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')

        if os.getenv('FLASK_ENV') == 'production':
            return f'postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}'
        else:
            # Use SQLite for development
            return 'sqlite:///securecart_fraud_detection.db'

@dataclass
class RedisConfig:
    """Redis configuration for caching and session management."""

    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    password: Optional[str] = os.getenv('REDIS_PASSWORD')
    database: int = int(os.getenv('REDIS_DB', '0'))

    # Connection settings
    max_connections: int = int(os.getenv('REDIS_MAX_CONNECTIONS', '20'))
    socket_timeout: float = float(os.getenv('REDIS_SOCKET_TIMEOUT', '5.0'))
    connection_timeout: float = float(os.getenv('REDIS_CONNECTION_TIMEOUT', '5.0'))

    @property
    def url(self) -> str:
        """Get Redis URL."""
        if self.password:
            return f'redis://:{self.password}@{self.host}:{self.port}/{self.database}'
        return f'redis://{self.host}:{self.port}/{self.database}'

@dataclass
class SecurityConfig:
    """Security and authentication configuration."""

    # JWT settings
    jwt_secret_key: str = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    jwt_access_token_expires: int = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    jwt_refresh_token_expires: int = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '604800'))  # 7 days
    jwt_algorithm: str = os.getenv('JWT_ALGORITHM', 'HS256')

    # Password settings
    password_min_length: int = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
    password_require_uppercase: bool = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'True').lower() == 'true'
    password_require_lowercase: bool = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'True').lower() == 'true'
    password_require_numbers: bool = os.getenv('PASSWORD_REQUIRE_NUMBERS', 'True').lower() == 'true'
    password_require_symbols: bool = os.getenv('PASSWORD_REQUIRE_SYMBOLS', 'True').lower() == 'true'

    # Rate limiting
    rate_limit_enabled: bool = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    rate_limit_requests_per_minute: int = int(os.getenv('RATE_LIMIT_RPM', '100'))
    rate_limit_requests_per_hour: int = int(os.getenv('RATE_LIMIT_RPH', '1000'))

    # Session security
    session_timeout_minutes: int = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))
    max_failed_login_attempts: int = int(os.getenv('MAX_FAILED_LOGIN_ATTEMPTS', '5'))
    account_lockout_duration_minutes: int = int(os.getenv('ACCOUNT_LOCKOUT_DURATION', '30'))

    # CORS settings
    cors_origins: list = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    cors_allow_credentials: bool = os.getenv('CORS_ALLOW_CREDENTIALS', 'True').lower() == 'true'

@dataclass
class MLConfig:
    """Machine Learning model configuration."""

    # Model settings
    model_path: str = os.getenv('ML_MODEL_PATH', './models')
    active_model_name: str = os.getenv('ACTIVE_MODEL_NAME', 'ensemble_fraud_detector')
    model_version: str = os.getenv('MODEL_VERSION', '1.0.0')

    # Fraud detection thresholds
    fraud_threshold: float = float(os.getenv('FRAUD_THRESHOLD', '0.7'))
    high_risk_threshold: float = float(os.getenv('HIGH_RISK_THRESHOLD', '0.5'))
    medium_risk_threshold: float = float(os.getenv('MEDIUM_RISK_THRESHOLD', '0.3'))

    # Feature engineering
    feature_window_hours: int = int(os.getenv('FEATURE_WINDOW_HOURS', '24'))
    velocity_check_enabled: bool = os.getenv('VELOCITY_CHECK_ENABLED', 'True').lower() == 'true'
    location_check_enabled: bool = os.getenv('LOCATION_CHECK_ENABLED', 'True').lower() == 'true'

    # Model training
    training_data_min_size: int = int(os.getenv('TRAINING_DATA_MIN_SIZE', '10000'))
    retrain_frequency_days: int = int(os.getenv('RETRAIN_FREQUENCY_DAYS', '7'))
    model_performance_threshold: float = float(os.getenv('MODEL_PERFORMANCE_THRESHOLD', '0.85'))

    # Real-time processing
    batch_size: int = int(os.getenv('ML_BATCH_SIZE', '100'))
    max_processing_time_seconds: float = float(os.getenv('MAX_PROCESSING_TIME', '2.0'))

@dataclass
class BlockchainConfig:
    """Blockchain integration configuration."""

    # Network settings
    provider_url: str = os.getenv('BLOCKCHAIN_PROVIDER_URL', 'http://localhost:8545')
    network_name: str = os.getenv('BLOCKCHAIN_NETWORK', 'development')
    chain_id: int = int(os.getenv('BLOCKCHAIN_CHAIN_ID', '1337'))

    # Contract settings
    contract_address: Optional[str] = os.getenv('FRAUD_CONTRACT_ADDRESS')
    private_key: Optional[str] = os.getenv('BLOCKCHAIN_PRIVATE_KEY')
    gas_limit: int = int(os.getenv('BLOCKCHAIN_GAS_LIMIT', '200000'))
    gas_price_gwei: int = int(os.getenv('BLOCKCHAIN_GAS_PRICE', '20'))

    # Transaction settings
    confirmation_blocks: int = int(os.getenv('BLOCKCHAIN_CONFIRMATIONS', '1'))
    timeout_seconds: int = int(os.getenv('BLOCKCHAIN_TIMEOUT', '60'))

    # Integration settings
    enabled: bool = os.getenv('BLOCKCHAIN_ENABLED', 'False').lower() == 'true'
    record_all_transactions: bool = os.getenv('BLOCKCHAIN_RECORD_ALL', 'False').lower() == 'true'
    verify_on_startup: bool = os.getenv('BLOCKCHAIN_VERIFY_STARTUP', 'True').lower() == 'true'

@dataclass
class WebSocketConfig:
    """WebSocket configuration for real-time updates."""

    # Connection settings
    cors_allowed_origins: list = os.getenv('WEBSOCKET_CORS_ORIGINS', '*').split(',')
    async_mode: str = os.getenv('WEBSOCKET_ASYNC_MODE', 'threading')
    ping_timeout: int = int(os.getenv('WEBSOCKET_PING_TIMEOUT', '60'))
    ping_interval: int = int(os.getenv('WEBSOCKET_PING_INTERVAL', '25'))

    # Authentication
    auth_required: bool = os.getenv('WEBSOCKET_AUTH_REQUIRED', 'True').lower() == 'true'
    auth_timeout_seconds: int = int(os.getenv('WEBSOCKET_AUTH_TIMEOUT', '30'))

    # Message settings
    max_message_size: int = int(os.getenv('WEBSOCKET_MAX_MESSAGE_SIZE', '1048576'))  # 1MB
    message_rate_limit: int = int(os.getenv('WEBSOCKET_MESSAGE_RATE_LIMIT', '100'))  # per minute

    # Room settings
    max_rooms_per_client: int = int(os.getenv('WEBSOCKET_MAX_ROOMS', '10'))
    room_cleanup_interval_seconds: int = int(os.getenv('WEBSOCKET_ROOM_CLEANUP', '300'))

@dataclass
class LoggingConfig:
    """Logging configuration."""

    # Log levels
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File logging
    file_enabled: bool = os.getenv('LOG_FILE_ENABLED', 'True').lower() == 'true'
    file_path: str = os.getenv('LOG_FILE_PATH', './logs/app.log')
    file_max_size_mb: int = int(os.getenv('LOG_FILE_MAX_SIZE_MB', '10'))
    file_backup_count: int = int(os.getenv('LOG_FILE_BACKUP_COUNT', '5'))

    # Database logging
    db_enabled: bool = os.getenv('LOG_DB_ENABLED', 'True').lower() == 'true'
    db_level: str = os.getenv('LOG_DB_LEVEL', 'WARNING')

    # External logging services
    sentry_dsn: Optional[str] = os.getenv('SENTRY_DSN')
    elasticsearch_enabled: bool = os.getenv('LOG_ELASTICSEARCH_ENABLED', 'False').lower() == 'true'
    elasticsearch_host: str = os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')

@dataclass
class MonitoringConfig:
    """System monitoring and alerting configuration."""

    # Health checks
    health_check_enabled: bool = os.getenv('HEALTH_CHECK_ENABLED', 'True').lower() == 'true'
    health_check_interval_seconds: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))

    # Performance monitoring
    performance_monitoring_enabled: bool = os.getenv('PERFORMANCE_MONITORING_ENABLED', 'True').lower() == 'true'
    metrics_collection_interval_seconds: int = int(os.getenv('METRICS_INTERVAL', '60'))

    # Alerting
    email_alerts_enabled: bool = os.getenv('EMAIL_ALERTS_ENABLED', 'False').lower() == 'true'
    slack_alerts_enabled: bool = os.getenv('SLACK_ALERTS_ENABLED', 'False').lower() == 'true'
    slack_webhook_url: Optional[str] = os.getenv('SLACK_WEBHOOK_URL')

    # Thresholds
    cpu_usage_threshold: float = float(os.getenv('CPU_THRESHOLD', '80.0'))
    memory_usage_threshold: float = float(os.getenv('MEMORY_THRESHOLD', '80.0'))
    disk_usage_threshold: float = float(os.getenv('DISK_THRESHOLD', '90.0'))
    response_time_threshold_ms: float = float(os.getenv('RESPONSE_TIME_THRESHOLD', '2000'))

class Config:
    """
    Main configuration class that aggregates all configuration settings.
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration based on environment.

        Args:
            environment: Environment name (development, testing, production)
        """
        self.environment = environment or os.getenv('FLASK_ENV', 'development')

        # Initialize all configuration sections
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.security = SecurityConfig()
        self.ml = MLConfig()
        self.blockchain = BlockchainConfig()
        self.websocket = WebSocketConfig()
        self.logging = LoggingConfig()
        self.monitoring = MonitoringConfig()

        # Application settings
        self.app_name = os.getenv('APP_NAME', 'SecureCart AI Fraud Detection')
        self.app_version = os.getenv('APP_VERSION', '1.0.0')
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.testing = os.getenv('TESTING', 'False').lower() == 'true'

        # Server settings
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', '5000'))
        self.workers = int(os.getenv('WORKERS', '4'))

        # Feature flags
        self.feature_flags = self._load_feature_flags()

        # Validate configuration
        self._validate_config()

    def _load_feature_flags(self) -> Dict[str, bool]:
        """Load feature flags from environment variables."""
        return {
            'fraud_detection_enabled': os.getenv('FEATURE_FRAUD_DETECTION', 'True').lower() == 'true',
            'blockchain_integration': os.getenv('FEATURE_BLOCKCHAIN', 'False').lower() == 'true',
            'real_time_monitoring': os.getenv('FEATURE_REAL_TIME_MONITORING', 'True').lower() == 'true',
            'ml_model_training': os.getenv('FEATURE_ML_TRAINING', 'True').lower() == 'true',
            'advanced_analytics': os.getenv('FEATURE_ADVANCED_ANALYTICS', 'True').lower() == 'true',
            'user_notifications': os.getenv('FEATURE_USER_NOTIFICATIONS', 'True').lower() == 'true',
            'api_rate_limiting': os.getenv('FEATURE_RATE_LIMITING', 'True').lower() == 'true',
            'audit_logging': os.getenv('FEATURE_AUDIT_LOGGING', 'True').lower() == 'true'
        }

    def _validate_config(self):
        """Validate configuration settings."""
        errors = []

        # Validate security settings
        if len(self.security.jwt_secret_key) < 32:
            errors.append("JWT secret key must be at least 32 characters long")

        if self.security.jwt_access_token_expires <= 0:
            errors.append("JWT access token expiration must be positive")

        # Validate ML settings
        if not (0 <= self.ml.fraud_threshold <= 1):
            errors.append("Fraud threshold must be between 0 and 1")

        if not (0 <= self.ml.high_risk_threshold <= 1):
            errors.append("High risk threshold must be between 0 and 1")

        # Validate database settings
        if self.environment == 'production' and 'sqlite' in self.database.url.lower():
            errors.append("SQLite should not be used in production")

        # Validate blockchain settings
        if self.blockchain.enabled and not self.blockchain.provider_url:
            errors.append("Blockchain provider URL is required when blockchain is enabled")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    def get_flask_config(self) -> Dict[str, Any]:
        """
        Get Flask-specific configuration dictionary.

        Returns:
            Dict: Flask configuration
        """
        return {
            'SECRET_KEY': self.security.jwt_secret_key,
            'DEBUG': self.debug,
            'TESTING': self.testing,
            'SQLALCHEMY_DATABASE_URI': self.database.url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': self.database.pool_size,
                'max_overflow': self.database.max_overflow,
                'pool_timeout': self.database.pool_timeout,
                'pool_recycle': self.database.pool_recycle,
                'echo': self.database.echo
            },
            'REDIS_URL': self.redis.url,
            'JWT_SECRET_KEY': self.security.jwt_secret_key,
            'JWT_ACCESS_TOKEN_EXPIRES': self.security.jwt_access_token_expires,
            'CORS_ORIGINS': self.security.cors_origins,
            'CORS_SUPPORTS_CREDENTIALS': self.security.cors_allow_credentials
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (excluding sensitive data).

        Returns:
            Dict: Configuration dictionary
        """
        return {
            'environment': self.environment,
            'app_name': self.app_name,
            'app_version': self.app_version,
            'debug': self.debug,
            'feature_flags': self.feature_flags,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'name': self.database.name,
                'pool_size': self.database.pool_size
            },
            'ml': {
                'active_model_name': self.ml.active_model_name,
                'model_version': self.ml.model_version,
                'fraud_threshold': self.ml.fraud_threshold,
                'high_risk_threshold': self.ml.high_risk_threshold
            },
            'blockchain': {
                'enabled': self.blockchain.enabled,
                'network_name': self.blockchain.network_name,
                'chain_id': self.blockchain.chain_id
            }
        }

# =============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# =============================================================================

class DevelopmentConfig(Config):
    """Configuration for development environment."""

    def __init__(self):
        super().__init__('development')
        self.debug = True
        self.database.echo = True
        self.security.rate_limit_enabled = False
        self.blockchain.enabled = False

class TestingConfig(Config):
    """Configuration for testing environment."""

    def __init__(self):
        super().__init__('testing')
        self.testing = True
        self.database = DatabaseConfig()
        self.database.url = 'sqlite:///:memory:'  # In-memory database for tests
        self.security.rate_limit_enabled = False
        self.blockchain.enabled = False
        self.ml.fraud_threshold = 0.5  # Lower threshold for testing

class ProductionConfig(Config):
    """Configuration for production environment."""

    def __init__(self):
        super().__init__('production')
        self.debug = False

        # Enhanced security for production
        self.security.rate_limit_enabled = True
        self.security.session_timeout_minutes = 30
        self.security.max_failed_login_attempts = 3

        # Production ML settings
        self.ml.fraud_threshold = 0.8
        self.ml.high_risk_threshold = 0.6

        # Enable blockchain in production
        self.blockchain.enabled = True

        # Production monitoring
        self.monitoring.health_check_enabled = True
        self.monitoring.performance_monitoring_enabled = True

# =============================================================================
# CONFIGURATION FACTORY
# =============================================================================

def get_config(environment: Optional[str] = None) -> Config:
    """
    Get configuration instance based on environment.

    Args:
        environment: Environment name

    Returns:
        Config: Configuration instance
    """
    env = environment or os.getenv('FLASK_ENV', 'development')

    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }

    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()

# =============================================================================
# CONFIGURATION UTILITIES
# =============================================================================

def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON or YAML file.

    Args:
        file_path: Path to configuration file

    Returns:
        Dict: Configuration data
    """
    import json

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, 'r') as f:
        if file_path.suffix.lower() == '.json':
            return json.load(f)
        elif file_path.suffix.lower() in ['.yml', '.yaml']:
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML configuration files")
        else:
            raise ValueError(f"Unsupported configuration file format: {file_path.suffix}")

def validate_environment_variables() -> Dict[str, str]:
    """
    Validate required environment variables.

    Returns:
        Dict: Missing or invalid environment variables
    """
    required_vars = {
        'production': [
            'JWT_SECRET_KEY',
            'DB_HOST',
            'DB_NAME',
            'DB_USERNAME',
            'DB_PASSWORD'
        ],
        'development': [],
        'testing': []
    }

    env = os.getenv('FLASK_ENV', 'development')
    missing_vars = {}

    for var in required_vars.get(env, []):
        value = os.getenv(var)
        if not value:
            missing_vars[var] = 'Required but not set'
        elif var == 'JWT_SECRET_KEY' and len(value) < 32:
            missing_vars[var] = 'Must be at least 32 characters long'

    return missing_vars

# =============================================================================
# MAIN EXECUTION FOR CONFIGURATION VALIDATION
# =============================================================================

if __name__ == '__main__':
    """
    Main execution block for configuration validation and testing.
    """
    try:
        print("=== SecureCart AI Configuration Validation ===")

        # Check environment variables
        missing_vars = validate_environment_variables()
        if missing_vars:
            print("\nMissing or invalid environment variables:")
            for var, issue in missing_vars.items():
                print(f"  {var}: {issue}")
        else:
            print("\n✅ All required environment variables are set")

        # Test configuration loading
        environments = ['development', 'testing', 'production']

        for env in environments:
            print(f"\n=== Testing {env.upper()} Configuration ===")
            try:
                config = get_config(env)
                print(f"✅ {env} configuration loaded successfully")
                print(f"   App: {config.app_name} v{config.app_version}")
                print(f"   Database: {config.database.url}")
                print(f"   Debug: {config.debug}")
                print(f"   Feature flags: {sum(config.feature_flags.values())}/{len(config.feature_flags)} enabled")

                # Test Flask config
                flask_config = config.get_flask_config()
                print(f"   Flask config keys: {len(flask_config)}")

            except Exception as e:
                print(f"❌ Error loading {env} configuration: {e}")

        print("\n=== Configuration Validation Complete ===")

    except Exception as e:
        print(f"Error during configuration validation: {e}")
