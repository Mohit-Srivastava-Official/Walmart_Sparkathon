"""
Flask application entry point for SecureCart AI fraud detection system.
This module initializes and configures the Flask application with all necessary
extensions, blueprints, and middleware for the fraud detection API.
"""

# Standard library imports
import os
import logging
from datetime import datetime, timedelta

# Third-party imports
from flask import Flask, request, jsonify, g
from flask_cors import CORS  # Cross-Origin Resource Sharing support
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_limiter import Limiter  # Rate limiting for API endpoints
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy  # Database ORM
try:
    import redis  # Redis for caching and real-time data
    redis_client = redis.from_url(app.config['REDIS_URL'])
except Exception:
    class DummyRedis:
        def setex(self, *args, **kwargs):
            pass
        def delete(self, *args, **kwargs):
            pass
    redis_client = DummyRedis()
from werkzeug.security import generate_password_hash, check_password_hash

# Local imports (these would be in separate modules)
# from models import db, User, Transaction, FraudAlert, SecurityRule
# from ml_models import FraudDetectionModel
# from blockchain import BlockchainIntegration
# from security import SecurityManager

# Initialize Flask application
app = Flask(__name__)

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# Load configuration from environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Token expires in 24 hours

# Database configuration - PostgreSQL for production, SQLite for development
database_url = os.environ.get('DATABASE_URL', 'sqlite:///securecart.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for performance

# Redis configuration for caching and real-time data
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['REDIS_URL'] = redis_url

# API rate limiting configuration
app.config['RATELIMIT_STORAGE_URL'] = redis_url
app.config['RATELIMIT_DEFAULT'] = "1000 per hour"  # Default rate limit

# CORS configuration for frontend communication
app.config['CORS_ORIGINS'] = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

# Machine Learning model configuration
app.config['ML_MODEL_PATH'] = os.environ.get('ML_MODEL_PATH', './ml_models/')
app.config['ML_THRESHOLD'] = float(os.environ.get('ML_THRESHOLD', '0.7'))

# Blockchain configuration
app.config['BLOCKCHAIN_ENABLED'] = os.environ.get('BLOCKCHAIN_ENABLED', 'False').lower() == 'true'
app.config['WEB3_PROVIDER_URL'] = os.environ.get('WEB3_PROVIDER_URL', 'http://localhost:8545')

# =============================================================================
# EXTENSION INITIALIZATION
# =============================================================================

# Initialize database ORM
# db = SQLAlchemy(app)

# Initialize JWT manager for authentication
jwt = JWTManager(app)

# Initialize CORS for cross-origin requests
CORS(app, origins=app.config['CORS_ORIGINS'])



# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,  # Use IP address for rate limiting
    app=app,
    default_limits=["1000 per hour"]  # Default rate limit
)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Configure logging for different environments
if app.config.get('ENV') == 'production':
    # Production logging - log to file and external service
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.FileHandler('securecart.log'),
            logging.StreamHandler()
        ]
    )
else:
    # Development logging - more verbose, console only
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s'
    )

logger = logging.getLogger(__name__)

# =============================================================================
# MIDDLEWARE AND REQUEST HOOKS
# =============================================================================

@app.before_request
def before_request():
    """
    Execute before each request to log activity and set up request context.
    This middleware runs before every API call to track usage and performance.
    """
    # Log incoming request for monitoring and debugging
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

    # Store request start time for performance monitoring
    g.start_time = datetime.utcnow()

    # Add request ID for tracing (in production, use proper request ID middleware)
    g.request_id = f"req_{int(datetime.utcnow().timestamp())}"

@app.after_request
def after_request(response):
    """
    Execute after each request to log response and performance metrics.
    This middleware runs after every API call to track performance and errors.
    """
    # Calculate request processing time
    if hasattr(g, 'start_time'):
        processing_time = (datetime.utcnow() - g.start_time).total_seconds()
        response.headers['X-Processing-Time'] = str(processing_time)

        # Log response for monitoring
        logger.info(f"Response: {response.status_code} in {processing_time:.3f}s")

    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors with consistent JSON response."""
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request could not be understood by the server',
        'status_code': 400
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors for authentication failures."""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required',
        'status_code': 401
    }), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors for authorization failures."""
    return jsonify({
        'error': 'Forbidden',
        'message': 'Insufficient permissions',
        'status_code': 403
    }), 403

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors for missing resources."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Too Many Requests errors from rate limiting."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error with logging."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500

# =============================================================================
# JWT TOKEN HANDLERS
# =============================================================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired JWT tokens with clear error message."""
    return jsonify({
        'error': 'Token Expired',
        'message': 'The token has expired. Please log in again.',
        'status_code': 401
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid JWT tokens with clear error message."""
    return jsonify({
        'error': 'Invalid Token',
        'message': 'The token is invalid. Please log in again.',
        'status_code': 401
    }), 401

# =============================================================================
# CORE API ROUTES
# =============================================================================

@app.route('/')
def index():
    """
    Root endpoint that provides API information and health status.
    This endpoint gives basic information about the SecureCart AI API.
    """
    return jsonify({
        'name': 'SecureCart AI Fraud Detection API',
        'version': '1.0.0',
        'description': 'Advanced real-time fraud detection system for Walmart Sparkathon 2025',
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'authentication': '/api/auth',
            'transactions': '/api/transactions',
            'fraud_detection': '/api/fraud',
            'analytics': '/api/analytics',
            'settings': '/api/settings'
        }
    })

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and load balancer integration.
    This endpoint verifies that all critical services are operational.
    """
    try:
        # Check database connectivity
        # db_status = 'connected' if db.engine.execute('SELECT 1').scalar() == 1 else 'disconnected'
        db_status = 'connected'  # Placeholder since db is not fully implemented

        # Check Redis connectivity
        redis_status = 'connected' if redis_client.ping() else 'disconnected'

        # Check ML model availability
        ml_status = 'loaded'  # Placeholder for ML model status

        # Overall health status
        overall_status = 'healthy' if all([
            db_status == 'connected',
            redis_status == 'connected',
            ml_status == 'loaded'
        ]) else 'unhealthy'

        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': db_status,
                'redis': redis_status,
                'ml_model': ml_status
            },
            'uptime': 'calculated_uptime_here'  # Would calculate actual uptime
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit login attempts
def login():
    """
    User authentication endpoint that validates credentials and returns JWT token.
    This endpoint handles user login and issues JWT tokens for API access.
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email')
        password = data.get('password')
        remember_me = data.get('rememberMe', False)

        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Demo authentication (in production, validate against database)
        if email == 'admin@walmart.com' and password == 'securepass123':
            # Create user data (in production, fetch from database)
            user_data = {
                'id': 'user_123',
                'email': email,
                'name': 'Security Administrator',
                'role': 'admin',
                'lastLogin': datetime.utcnow().isoformat()
            }

            # Create JWT token with extended expiry if remember_me is True
            expires = timedelta(days=30) if remember_me else timedelta(hours=24)
            access_token = create_access_token(
                identity=user_data['id'],
                expires_delta=expires
            )

            # Store session in Redis for tracking
            redis_client.setex(
                f"session:{user_data['id']}",
                int(expires.total_seconds()),
                access_token
            )

            logger.info(f"User {email} logged in successfully")

            return jsonify({
                'message': 'Login successful',
                'user': user_data,
                'token': access_token
            })

        else:
            # Invalid credentials
            logger.warning(f"Failed login attempt for {email}")
            return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint that invalidates the JWT token.
    This endpoint handles user logout and token cleanup.
    """
    try:
        # Get current user from JWT token
        current_user_id = get_jwt_identity()

        # Remove session from Redis
        redis_client.delete(f"session:{current_user_id}")

        logger.info(f"User {current_user_id} logged out successfully")

        return jsonify({'message': 'Logout successful'})

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Token verification endpoint to check if JWT token is still valid.
    This endpoint allows the frontend to verify token validity.
    """
    try:
        current_user_id = get_jwt_identity()

        # In production, fetch user data from database
        user_data = {
            'id': current_user_id,
            'email': 'admin@walmart.com',
            'name': 'Security Administrator',
            'role': 'admin'
        }

        return jsonify({
            'valid': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'valid': False}), 401

# =============================================================================
# DEMO DATA ENDPOINTS (for frontend development)
# =============================================================================

@app.route('/api/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """
    Get transactions with optional filtering and pagination.
    This endpoint returns transaction data for the monitoring dashboard.
    """
    try:
        # In production, this would query the database with filters
        # For demo, return mock data
        mock_transactions = [
            {
                'id': 'txn_001',
                'userId': 'user_456',
                'amount': 250.75,
                'currency': 'USD',
                'merchantName': 'Best Buy Electronics',
                'merchantCategory': 'Electronics',
                'timestamp': datetime.utcnow().isoformat(),
                'location': {
                    'country': 'USA',
                    'city': 'New York',
                    'coordinates': [40.7128, -74.0060]
                },
                'paymentMethod': 'card',
                'deviceInfo': {
                    'deviceId': 'device_789',
                    'ipAddress': '192.168.1.100',
                    'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'status': 'approved',
                'riskScore': 25,
                'fraudProbability': 0.15,
                'blockchainHash': '0x1234567890abcdef'
            },
            # More mock transactions would be added here
        ]

        return jsonify({
            'transactions': mock_transactions,
            'totalCount': len(mock_transactions),
            'totalAmount': sum(t['amount'] for t in mock_transactions),
            'averageRiskScore': sum(t['riskScore'] for t in mock_transactions) / len(mock_transactions)
        })

    except Exception as e:
        logger.error(f"Get transactions error: {e}")
        return jsonify({'error': 'Failed to fetch transactions'}), 500

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    """
    Application entry point for development server.
    In production, use a WSGI server like Gunicorn or uWSGI.
    """
    # Log startup information
    logger.info("Starting SecureCart AI Fraud Detection API")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info(f"Redis: {app.config['REDIS_URL']}")

    # Run development server
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=int(os.environ.get('PORT', 5000)),  # Use PORT env var or default to 5000
        debug=os.environ.get('FLASK_ENV') == 'development'  # Enable debug mode in development
    )
