"""
Database Models and Setup for SecureCart AI Fraud Detection System.
This module defines all database models, relationships, and database configuration
for storing transaction data, user information, fraud detection results, and system logs.
"""

# Standard library imports
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import json

# Third-party imports
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime,
    Text, JSON, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

# Create declarative base for all models
Base = declarative_base()

# =============================================================================
# USER MANAGEMENT MODELS
# =============================================================================

class User(Base):
    """
    User model for authentication and user management.

    This model stores:
    - User authentication information
    - Profile data and preferences
    - Security settings and permissions
    - Account status and metadata
    """
    __tablename__ = 'users'

    # Primary key and basic info
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone_number = Column(String(20))
    date_of_birth = Column(DateTime)

    # Account settings
    role = Column(String(20), default='user', nullable=False)  # user, analyst, admin
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Security settings
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime)
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(80))

    # Relationships
    transactions = relationship("Transaction", back_populates="user", lazy='dynamic')
    fraud_reports = relationship("FraudReport", back_populates="reported_by", lazy='dynamic')
    user_sessions = relationship("UserSession", back_populates="user", lazy='dynamic')

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email_username', 'email', 'username'),
        Index('idx_user_role_active', 'role', 'is_active'),
        CheckConstraint("role IN ('user', 'analyst', 'admin')", name='check_user_role')
    )

    def set_password(self, password: str) -> None:
        """
        Hash and set user password using bcrypt.

        Args:
            password (str): Plain text password
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Verify user password against stored hash.

        Args:
            password (str): Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary (excluding sensitive data)."""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'two_factor_enabled': self.two_factor_enabled,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<User {self.username}>'

class UserSession(Base):
    """
    Model for tracking user sessions and authentication tokens.
    """
    __tablename__ = 'user_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True)

    # Session metadata
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_info = Column(JSON)
    location_data = Column(JSON)

    # Session lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    logout_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="user_sessions")

    # Indexes
    __table_args__ = (
        Index('idx_session_token_active', 'session_token', 'is_active'),
        Index('idx_session_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self):
        return f'<UserSession {self.user_id}>'

# =============================================================================
# TRANSACTION MODELS
# =============================================================================

class Transaction(Base):
    """
    Model for storing transaction data and metadata.

    This model stores:
    - Transaction details (amount, merchant, payment method)
    - Location and timing information
    - Processing status and fraud check results
    - Blockchain verification data
    """
    __tablename__ = 'transactions'

    # Primary key and basic transaction info
    id = Column(String(50), primary_key=True)  # External transaction ID
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Transaction details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    merchant_name = Column(String(200), nullable=False)
    merchant_category = Column(String(100))
    merchant_id = Column(String(50))

    # Payment information
    payment_method = Column(String(50), nullable=False)  # card, bank, digital_wallet
    card_type = Column(String(20))  # visa, mastercard, amex
    card_last_four = Column(String(4))
    bank_name = Column(String(100))

    # Location data
    location_country = Column(String(2))  # ISO country code
    location_city = Column(String(100))
    location_coordinates = Column(JSON)  # {lat, lng}
    ip_address = Column(String(45))

    # Transaction timing
    transaction_time = Column(DateTime, nullable=False)
    processing_time = Column(DateTime, default=datetime.utcnow)
    timezone_offset = Column(Integer)  # Minutes from UTC

    # Status and processing
    status = Column(String(20), default='pending', nullable=False)  # pending, approved, declined, flagged
    processor_response = Column(String(100))
    authorization_code = Column(String(20))

    # Fraud detection integration
    risk_score = Column(Float)
    fraud_probability = Column(Float)
    fraud_reasons = Column(JSON)  # List of fraud indicators
    ml_model_version = Column(String(20))

    # Blockchain integration
    blockchain_hash = Column(String(66))  # Ethereum transaction hash
    blockchain_verified = Column(Boolean, default=False)
    blockchain_verification_time = Column(DateTime)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="transactions")
    fraud_reports = relationship("FraudReport", back_populates="transaction", lazy='dynamic')

    # Indexes for performance
    __table_args__ = (
        Index('idx_transaction_user_time', 'user_id', 'transaction_time'),
        Index('idx_transaction_amount_status', 'amount', 'status'),
        Index('idx_transaction_risk_score', 'risk_score'),
        Index('idx_transaction_merchant', 'merchant_name'),
        Index('idx_transaction_blockchain', 'blockchain_hash'),
        CheckConstraint("status IN ('pending', 'approved', 'declined', 'flagged')", name='check_transaction_status'),
        CheckConstraint("amount > 0", name='check_positive_amount')
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction object to dictionary."""
        return {
            'id': self.id,
            'user_id': str(self.user_id),
            'amount': self.amount,
            'currency': self.currency,
            'merchant_name': self.merchant_name,
            'merchant_category': self.merchant_category,
            'payment_method': self.payment_method,
            'card_type': self.card_type,
            'location': {
                'country': self.location_country,
                'city': self.location_city,
                'coordinates': self.location_coordinates
            },
            'transaction_time': self.transaction_time.isoformat(),
            'status': self.status,
            'risk_score': self.risk_score,
            'fraud_probability': self.fraud_probability,
            'fraud_reasons': self.fraud_reasons,
            'blockchain_verified': self.blockchain_verified,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Transaction {self.id}: ${self.amount}>'

# =============================================================================
# FRAUD DETECTION MODELS
# =============================================================================

class FraudReport(Base):
    """
    Model for storing fraud detection results and reports.

    This model stores:
    - Detailed fraud analysis results
    - ML model predictions and confidence scores
    - Manual review decisions and notes
    - Investigation status and outcomes
    """
    __tablename__ = 'fraud_reports'

    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(50), ForeignKey('transactions.id'), nullable=False)
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Fraud detection results
    is_fraud = Column(Boolean, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence_score = Column(Float)

    # ML model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    feature_importance = Column(JSON)  # Feature importance scores
    prediction_explanation = Column(JSON)  # SHAP/LIME explanations

    # Fraud indicators and reasons
    fraud_indicators = Column(JSON, nullable=False)  # List of detected fraud patterns
    rule_triggers = Column(JSON)  # Business rules that triggered
    anomaly_scores = Column(JSON)  # Scores from different anomaly detection models

    # Investigation and review
    investigation_status = Column(String(20), default='pending')  # pending, investigating, resolved
    manual_review_required = Column(Boolean, default=False)
    reviewer_notes = Column(Text)
    final_decision = Column(String(20))  # confirmed_fraud, false_positive, inconclusive

    # Actions taken
    action_taken = Column(String(50))  # block_transaction, flag_account, contact_user
    notification_sent = Column(Boolean, default=False)
    user_contacted = Column(Boolean, default=False)

    # Timing information
    detection_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    investigation_started = Column(DateTime)
    investigation_completed = Column(DateTime)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="fraud_reports")
    reported_by = relationship("User", back_populates="fraud_reports")

    # Indexes
    __table_args__ = (
        Index('idx_fraud_report_transaction', 'transaction_id'),
        Index('idx_fraud_report_risk_score', 'risk_score'),
        Index('idx_fraud_report_status', 'investigation_status'),
        Index('idx_fraud_report_detection_time', 'detection_time'),
        CheckConstraint("investigation_status IN ('pending', 'investigating', 'resolved')", name='check_investigation_status'),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name='check_risk_score_range')
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert fraud report object to dictionary."""
        return {
            'id': str(self.id),
            'transaction_id': self.transaction_id,
            'is_fraud': self.is_fraud,
            'fraud_probability': self.fraud_probability,
            'risk_score': self.risk_score,
            'confidence_score': self.confidence_score,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'fraud_indicators': self.fraud_indicators,
            'investigation_status': self.investigation_status,
            'manual_review_required': self.manual_review_required,
            'action_taken': self.action_taken,
            'detection_time': self.detection_time.isoformat(),
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<FraudReport {self.transaction_id}: {self.risk_score}%>'

class MLModel(Base):
    """
    Model for tracking ML model versions, performance, and metadata.
    """
    __tablename__ = 'ml_models'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    algorithm = Column(String(50), nullable=False)

    # Model performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_score = Column(Float)

    # Training information
    training_data_size = Column(Integer)
    training_start_time = Column(DateTime)
    training_end_time = Column(DateTime)
    hyperparameters = Column(JSON)
    feature_list = Column(JSON)

    # Model metadata
    model_file_path = Column(String(255))
    model_size_mb = Column(Float)
    is_active = Column(Boolean, default=False)
    deployment_date = Column(DateTime)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(80))

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_model_name_version'),
        Index('idx_model_active', 'is_active'),
    )

    def __repr__(self):
        return f'<MLModel {self.name} v{self.version}>'

# =============================================================================
# SYSTEM MONITORING MODELS
# =============================================================================

class SystemLog(Base):
    """
    Model for storing system logs, errors, and monitoring data.
    """
    __tablename__ = 'system_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Log details
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    logger_name = Column(String(100))
    module = Column(String(100))
    function_name = Column(String(100))

    # Context information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    transaction_id = Column(String(50), nullable=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45))

    # Additional data
    extra_data = Column(JSON)  # Additional context data
    stack_trace = Column(Text)  # For error logs

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_system_log_level_timestamp', 'level', 'timestamp'),
        Index('idx_system_log_user', 'user_id'),
        Index('idx_system_log_transaction', 'transaction_id'),
    )

    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}>'

class PerformanceMetric(Base):
    """
    Model for storing system performance metrics and KPIs.
    """
    __tablename__ = 'performance_metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), nullable=False)  # fraud_detection, system, business

    # Metric values
    value = Column(Float, nullable=False)
    unit = Column(String(20))  # percentage, count, seconds, etc.
    target_value = Column(Float)  # Target/threshold value

    # Time window
    measurement_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    time_window_minutes = Column(Integer, default=60)  # Measurement window

    # Additional metadata
    metadata = Column(JSON)  # Additional metric context

    # Indexes
    __table_args__ = (
        Index('idx_performance_metric_name_time', 'metric_name', 'measurement_time'),
        Index('idx_performance_metric_category', 'metric_category'),
    )

    def __repr__(self):
        return f'<PerformanceMetric {self.metric_name}: {self.value}>'

# =============================================================================
# DATABASE CONFIGURATION AND SETUP
# =============================================================================

class DatabaseConfig:
    """
    Database configuration and connection management.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database configuration.

        Args:
            database_url (Optional[str]): Database connection URL
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.Session = None

    def _get_database_url(self) -> str:
        """
        Get database URL from environment or use default SQLite.

        Returns:
            str: Database connection URL
        """
        # Check for environment variable first
        if os.environ.get('DATABASE_URL'):
            return os.environ.get('DATABASE_URL')

        # Production PostgreSQL configuration
        if os.environ.get('FLASK_ENV') == 'production':
            host = os.environ.get('DB_HOST', 'localhost')
            port = os.environ.get('DB_PORT', '5432')
            name = os.environ.get('DB_NAME', 'securecart_fraud_detection')
            user = os.environ.get('DB_USER', 'postgres')
            password = os.environ.get('DB_PASSWORD', 'password')

            return f'postgresql://{user}:{password}@{host}:{port}/{name}'

        # Development SQLite configuration
        return 'sqlite:///securecart_fraud_detection.db'

    def create_engine(self, **kwargs):
        """
        Create database engine with configuration.

        Args:
            **kwargs: Additional engine parameters
        """
        default_kwargs = {
            'echo': os.environ.get('SQL_DEBUG', 'False').lower() == 'true',
            'pool_pre_ping': True,  # Verify connections before use
            'pool_recycle': 3600,   # Recycle connections every hour
        }

        # Add PostgreSQL-specific configurations
        if self.database_url.startswith('postgresql'):
            default_kwargs.update({
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
            })

        default_kwargs.update(kwargs)

        self.engine = create_engine(self.database_url, **default_kwargs)
        self.Session = sessionmaker(bind=self.engine)

        return self.engine

    def create_tables(self):
        """Create all database tables."""
        if not self.engine:
            self.create_engine()

        Base.metadata.create_all(self.engine)
        print("Database tables created successfully!")

    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        if not self.engine:
            self.create_engine()

        Base.metadata.drop_all(self.engine)
        print("Database tables dropped!")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session
        """
        if not self.Session:
            self.create_engine()

        return self.Session()

# =============================================================================
# DATABASE UTILITIES AND HELPERS
# =============================================================================

def create_sample_data(db_session: Session):
    """
    Create sample data for development and testing.

    Args:
        db_session: Database session
    """
    try:
        # Create sample users
        admin_user = User(
            username='admin',
            email='admin@securecart.com',
            first_name='System',
            last_name='Administrator',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin_user.set_password('admin123')

        analyst_user = User(
            username='analyst',
            email='analyst@securecart.com',
            first_name='Fraud',
            last_name='Analyst',
            role='analyst',
            is_active=True,
            is_verified=True
        )
        analyst_user.set_password('analyst123')

        regular_user = User(
            username='testuser',
            email='user@example.com',
            first_name='Test',
            last_name='User',
            role='user',
            is_active=True,
            is_verified=True
        )
        regular_user.set_password('user123')

        # Add users to session
        db_session.add_all([admin_user, analyst_user, regular_user])
        db_session.commit()

        # Create sample transactions
        sample_transactions = [
            Transaction(
                id='txn_001',
                user_id=regular_user.id,
                amount=250.75,
                merchant_name='Amazon',
                merchant_category='E-commerce',
                payment_method='card',
                card_type='visa',
                location_country='US',
                location_city='New York',
                transaction_time=datetime.utcnow(),
                status='approved',
                risk_score=15.5
            ),
            Transaction(
                id='txn_002',
                user_id=regular_user.id,
                amount=1500.00,
                merchant_name='Suspicious Store',
                merchant_category='Unknown',
                payment_method='card',
                card_type='mastercard',
                location_country='XX',
                location_city='Unknown',
                transaction_time=datetime.utcnow(),
                status='flagged',
                risk_score=85.2
            )
        ]

        # Add transactions
        db_session.add_all(sample_transactions)
        db_session.commit()

        # Create sample fraud reports
        fraud_report = FraudReport(
            transaction_id='txn_002',
            reported_by_id=analyst_user.id,
            is_fraud=True,
            fraud_probability=0.85,
            risk_score=85.2,
            model_name='ensemble_fraud_detector',
            model_version='1.0.0',
            fraud_indicators=['unusual_location', 'high_amount', 'new_merchant'],
            investigation_status='investigating'
        )

        db_session.add(fraud_report)
        db_session.commit()

        print("Sample data created successfully!")

    except Exception as e:
        db_session.rollback()
        print(f"Error creating sample data: {e}")

# =============================================================================
# MAIN EXECUTION FOR DATABASE SETUP
# =============================================================================

if __name__ == '__main__':
    """
    Main execution block for database setup and testing.
    """
    # Initialize database configuration
    db_config = DatabaseConfig()

    # Create database engine and tables
    engine = db_config.create_engine()
    db_config.create_tables()

    # Create a session and add sample data
    session = db_config.get_session()

    try:
        # Create sample data
        create_sample_data(session)

        # Test queries
        print("\n=== Testing Database Queries ===")

        # Query users
        users = session.query(User).all()
        print(f"Users in database: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.role})")

        # Query transactions
        transactions = session.query(Transaction).all()
        print(f"\nTransactions in database: {len(transactions)}")
        for txn in transactions:
            print(f"  - {txn.id}: ${txn.amount} at {txn.merchant_name} (Risk: {txn.risk_score}%)")

        # Query fraud reports
        fraud_reports = session.query(FraudReport).all()
        print(f"\nFraud reports in database: {len(fraud_reports)}")
        for report in fraud_reports:
            print(f"  - {report.transaction_id}: Risk {report.risk_score}% (Status: {report.investigation_status})")

        print("\nDatabase setup and testing completed successfully!")

    except Exception as e:
        print(f"Error during database testing: {e}")
        session.rollback()
    finally:
        session.close()
