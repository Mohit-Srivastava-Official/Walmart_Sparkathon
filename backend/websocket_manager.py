"""
WebSocket Module for Real-time Fraud Detection Updates.
This module provides real-time communication between the backend fraud detection
system and frontend dashboard for instant fraud alerts and transaction monitoring.
"""

# Standard library imports
import json
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
import uuid

# Third-party imports
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import redis
from threading import Thread
import queue

# Configure logging
logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    WebSocket manager for real-time fraud detection updates.

    This class handles:
    1. Real-time fraud alerts to connected clients
    2. Live transaction monitoring dashboard updates
    3. User-specific notification channels
    4. System status and health monitoring
    5. Fraud statistics broadcasting
    """

    def __init__(self, app=None, redis_client=None):
        """
        Initialize WebSocket manager with Flask-SocketIO.

        Args:
            app: Flask application instance
            redis_client: Redis client for pub/sub functionality
        """
        self.app = app
        self.socketio = None
        self.redis_client = redis_client
        self.connected_clients = {}  # client_id -> client_info
        self.user_sessions = {}      # user_id -> set of session_ids
        self.fraud_queue = queue.Queue()  # Queue for fraud alerts
        self.is_running = False

        # Initialize SocketIO if app is provided
        if app:
            self.initialize_socketio(app)

    def initialize_socketio(self, app):
        """
        Initialize Flask-SocketIO with the Flask application.

        Args:
            app: Flask application instance
        """
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",  # Configure based on your security needs
            async_mode='threading',    # Use threading for compatibility
            logger=True,
            engineio_logger=True
        )

        # Register event handlers
        self._register_event_handlers()

        # Start background tasks
        self._start_background_tasks()

        logger.info("WebSocket server initialized successfully")

    def _register_event_handlers(self):
        """Register all WebSocket event handlers."""

        @self.socketio.on('connect')
        def handle_connect(auth):
            """
            Handle client connection to WebSocket.

            Args:
                auth: Authentication data from client
            """
            try:
                # Get client session ID
                session_id = request.sid

                # Extract user information from auth token
                user_info = self._authenticate_websocket_user(auth)

                if not user_info:
                    logger.warning(f"Unauthenticated WebSocket connection attempt: {session_id}")
                    disconnect()
                    return False

                # Store client information
                self.connected_clients[session_id] = {
                    'user_id': user_info['user_id'],
                    'username': user_info['username'],
                    'role': user_info.get('role', 'user'),
                    'connected_at': datetime.utcnow().isoformat(),
                    'last_activity': datetime.utcnow().isoformat()
                }

                # Add to user sessions mapping
                user_id = user_info['user_id']
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(session_id)

                # Join user-specific room for targeted messages
                join_room(f"user_{user_id}")

                # Join role-based room (admin, analyst, user)
                join_room(f"role_{user_info.get('role', 'user')}")

                # Send welcome message with current system status
                emit('connection_established', {
                    'session_id': session_id,
                    'user_id': user_id,
                    'username': user_info['username'],
                    'connected_at': self.connected_clients[session_id]['connected_at'],
                    'system_status': self._get_system_status()
                })

                logger.info(f"WebSocket client connected: {user_info['username']} ({session_id})")

                # Notify other admins about new connection
                if user_info.get('role') == 'admin':
                    self.socketio.emit('admin_connected', {
                        'admin_username': user_info['username'],
                        'session_id': session_id,
                        'connected_at': self.connected_clients[session_id]['connected_at']
                    }, room='role_admin')

                return True

            except Exception as e:
                logger.error(f"Error handling WebSocket connection: {e}")
                disconnect()
                return False

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection from WebSocket."""
            try:
                session_id = request.sid

                if session_id in self.connected_clients:
                    client_info = self.connected_clients[session_id]
                    user_id = client_info['user_id']
                    username = client_info['username']

                    # Remove from user sessions
                    if user_id in self.user_sessions:
                        self.user_sessions[user_id].discard(session_id)
                        if not self.user_sessions[user_id]:
                            del self.user_sessions[user_id]

                    # Remove client info
                    del self.connected_clients[session_id]

                    # Leave rooms
                    leave_room(f"user_{user_id}")
                    leave_room(f"role_{client_info.get('role', 'user')}")

                    logger.info(f"WebSocket client disconnected: {username} ({session_id})")

                    # Notify other admins about disconnection
                    if client_info.get('role') == 'admin':
                        self.socketio.emit('admin_disconnected', {
                            'admin_username': username,
                            'session_id': session_id,
                            'disconnected_at': datetime.utcnow().isoformat()
                        }, room='role_admin')

            except Exception as e:
                logger.error(f"Error handling WebSocket disconnection: {e}")

        @self.socketio.on('subscribe_to_fraud_alerts')
        def handle_fraud_alert_subscription(data):
            """
            Handle subscription to fraud alerts.

            Args:
                data: Subscription preferences
            """
            try:
                session_id = request.sid

                if session_id not in self.connected_clients:
                    emit('error', {'message': 'Not authenticated'})
                    return

                client_info = self.connected_clients[session_id]

                # Join fraud alerts room
                join_room('fraud_alerts')

                # Update client preferences
                client_info['subscriptions'] = client_info.get('subscriptions', {})
                client_info['subscriptions']['fraud_alerts'] = {
                    'enabled': data.get('enabled', True),
                    'min_risk_score': data.get('min_risk_score', 70),
                    'include_false_positives': data.get('include_false_positives', False),
                    'subscribed_at': datetime.utcnow().isoformat()
                }

                emit('subscription_confirmed', {
                    'type': 'fraud_alerts',
                    'preferences': client_info['subscriptions']['fraud_alerts']
                })

                logger.info(f"Client subscribed to fraud alerts: {client_info['username']}")

            except Exception as e:
                logger.error(f"Error handling fraud alert subscription: {e}")
                emit('error', {'message': 'Subscription failed'})

        @self.socketio.on('request_live_stats')
        def handle_live_stats_request():
            """Handle request for live fraud detection statistics."""
            try:
                session_id = request.sid

                if session_id not in self.connected_clients:
                    emit('error', {'message': 'Not authenticated'})
                    return

                # Get current fraud statistics
                stats = self._get_live_fraud_statistics()

                emit('live_stats_update', stats)

                # Join live stats room for automatic updates
                join_room('live_stats')

            except Exception as e:
                logger.error(f"Error handling live stats request: {e}")
                emit('error', {'message': 'Failed to get live stats'})

        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping from client to maintain connection."""
            session_id = request.sid

            if session_id in self.connected_clients:
                self.connected_clients[session_id]['last_activity'] = datetime.utcnow().isoformat()
                emit('pong', {'timestamp': datetime.utcnow().isoformat()})

    def _authenticate_websocket_user(self, auth) -> Optional[Dict[str, Any]]:
        """
        Authenticate WebSocket user using JWT token.

        Args:
            auth: Authentication data from client

        Returns:
            Optional[Dict]: User information if authenticated, None otherwise
        """
        try:
            # Extract token from auth data
            token = auth.get('token') if auth else None

            if not token:
                return None

            # In a real application, verify JWT token here
            # For demo, create mock user data
            if token.startswith('admin_'):
                return {
                    'user_id': 'admin_001',
                    'username': 'admin_user',
                    'role': 'admin'
                }
            elif token.startswith('analyst_'):
                return {
                    'user_id': 'analyst_001',
                    'username': 'fraud_analyst',
                    'role': 'analyst'
                }
            else:
                return {
                    'user_id': 'user_001',
                    'username': 'regular_user',
                    'role': 'user'
                }

        except Exception as e:
            logger.error(f"Error authenticating WebSocket user: {e}")
            return None

    def _get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status for client updates.

        Returns:
            Dict: System status information
        """
        return {
            'status': 'operational',
            'connected_clients': len(self.connected_clients),
            'fraud_detection_active': True,
            'ml_model_status': 'trained',
            'blockchain_status': 'connected',
            'last_updated': datetime.utcnow().isoformat(),
            'uptime_hours': 24.5,  # Mock uptime
            'processed_transactions_today': 12450
        }

    def _get_live_fraud_statistics(self) -> Dict[str, Any]:
        """
        Get live fraud detection statistics.

        Returns:
            Dict: Current fraud statistics
        """
        return {
            'transactions_per_minute': 85,
            'fraud_detections_today': 23,
            'fraud_rate_today': 1.8,
            'average_risk_score': 22.5,
            'high_risk_transactions': 156,
            'blocked_transactions': 12,
            'false_positive_rate': 0.3,
            'model_accuracy': 94.7,
            'last_fraud_detection': datetime.utcnow().isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _start_background_tasks(self):
        """Start background tasks for WebSocket updates."""
        self.is_running = True

        # Start fraud alert processor
        fraud_alert_thread = Thread(target=self._process_fraud_alerts, daemon=True)
        fraud_alert_thread.start()

        # Start periodic stats updater
        stats_update_thread = Thread(target=self._periodic_stats_update, daemon=True)
        stats_update_thread.start()

        # Start connection health checker
        health_check_thread = Thread(target=self._connection_health_check, daemon=True)
        health_check_thread.start()

        logger.info("WebSocket background tasks started")

    def _process_fraud_alerts(self):
        """Background task to process and send fraud alerts."""
        while self.is_running:
            try:
                # Check for new fraud alerts in queue
                if not self.fraud_queue.empty():
                    fraud_alert = self.fraud_queue.get(timeout=1)
                    self._send_fraud_alert(fraud_alert)
                else:
                    time.sleep(0.1)  # Short sleep to prevent busy waiting

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing fraud alerts: {e}")
                time.sleep(1)

    def _periodic_stats_update(self):
        """Background task to send periodic statistics updates."""
        while self.is_running:
            try:
                # Send stats update every 30 seconds
                time.sleep(30)

                if self.socketio and 'live_stats' in self.socketio.server.manager.rooms.get('/', {}):
                    stats = self._get_live_fraud_statistics()
                    self.socketio.emit('live_stats_update', stats, room='live_stats')

            except Exception as e:
                logger.error(f"Error sending periodic stats update: {e}")
                time.sleep(5)

    def _connection_health_check(self):
        """Background task to check connection health and cleanup stale connections."""
        while self.is_running:
            try:
                time.sleep(60)  # Check every minute

                current_time = datetime.utcnow()
                stale_sessions = []

                # Find stale connections (no activity for 10 minutes)
                for session_id, client_info in self.connected_clients.items():
                    last_activity = datetime.fromisoformat(client_info['last_activity'].replace('Z', ''))
                    if (current_time - last_activity).total_seconds() > 600:  # 10 minutes
                        stale_sessions.append(session_id)

                # Disconnect stale sessions
                for session_id in stale_sessions:
                    logger.info(f"Disconnecting stale session: {session_id}")
                    self.socketio.disconnect(session_id)

            except Exception as e:
                logger.error(f"Error in connection health check: {e}")
                time.sleep(5)

    def send_fraud_alert(self, fraud_data: Dict[str, Any]) -> bool:
        """
        Queue a fraud alert to be sent to connected clients.

        Args:
            fraud_data: Fraud detection data

        Returns:
            bool: True if queued successfully
        """
        try:
            # Add fraud alert to queue for processing
            fraud_alert = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'transaction_id': fraud_data.get('transaction_id'),
                'user_id': fraud_data.get('user_id'),
                'amount': fraud_data.get('amount'),
                'merchant': fraud_data.get('merchant_name'),
                'risk_score': fraud_data.get('risk_score'),
                'fraud_probability': fraud_data.get('fraud_probability'),
                'alert_level': self._get_alert_level(fraud_data.get('risk_score', 0)),
                'location': fraud_data.get('location'),
                'payment_method': fraud_data.get('payment_method'),
                'fraud_reasons': fraud_data.get('fraud_reasons', [])
            }

            self.fraud_queue.put(fraud_alert)
            return True

        except Exception as e:
            logger.error(f"Error queuing fraud alert: {e}")
            return False

    def _send_fraud_alert(self, fraud_alert: Dict[str, Any]):
        """
        Send fraud alert to appropriate clients.

        Args:
            fraud_alert: Fraud alert data
        """
        try:
            if not self.socketio:
                return

            # Send to fraud alerts room (subscribed clients)
            self.socketio.emit('fraud_alert', fraud_alert, room='fraud_alerts')

            # Send to specific user if available
            user_id = fraud_alert.get('user_id')
            if user_id:
                self.socketio.emit('user_fraud_alert', fraud_alert, room=f'user_{user_id}')

            # Send high-priority alerts to all admins
            if fraud_alert.get('alert_level') == 'critical':
                self.socketio.emit('critical_fraud_alert', fraud_alert, room='role_admin')

            logger.info(f"Fraud alert sent: {fraud_alert['id']} (Risk: {fraud_alert['risk_score']})")

        except Exception as e:
            logger.error(f"Error sending fraud alert: {e}")

    def _get_alert_level(self, risk_score: float) -> str:
        """
        Determine alert level based on risk score.

        Args:
            risk_score: Risk score (0-100)

        Returns:
            str: Alert level
        """
        if risk_score >= 90:
            return 'critical'
        elif risk_score >= 70:
            return 'high'
        elif risk_score >= 50:
            return 'medium'
        else:
            return 'low'

    def send_transaction_update(self, transaction_data: Dict[str, Any]):
        """
        Send real-time transaction update to dashboard.

        Args:
            transaction_data: Transaction data
        """
        try:
            if not self.socketio:
                return

            update = {
                'type': 'transaction_processed',
                'timestamp': datetime.utcnow().isoformat(),
                'transaction_id': transaction_data.get('id'),
                'amount': transaction_data.get('amount'),
                'merchant': transaction_data.get('merchantName'),
                'status': transaction_data.get('status', 'processed'),
                'risk_score': transaction_data.get('risk_score'),
                'processing_time_ms': transaction_data.get('processing_time_ms', 0)
            }

            # Send to live stats room
            self.socketio.emit('transaction_update', update, room='live_stats')

        except Exception as e:
            logger.error(f"Error sending transaction update: {e}")

    def send_system_notification(self,
                                notification_type: str,
                                message: str,
                                target_roles: List[str] = None):
        """
        Send system notification to specific roles.

        Args:
            notification_type: Type of notification
            message: Notification message
            target_roles: List of roles to notify (default: all)
        """
        try:
            if not self.socketio:
                return

            notification = {
                'id': str(uuid.uuid4()),
                'type': notification_type,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'info'
            }

            if target_roles:
                for role in target_roles:
                    self.socketio.emit('system_notification', notification, room=f'role_{role}')
            else:
                # Send to all connected clients
                self.socketio.emit('system_notification', notification)

            logger.info(f"System notification sent: {notification_type}")

        except Exception as e:
            logger.error(f"Error sending system notification: {e}")

    def get_connected_clients_info(self) -> Dict[str, Any]:
        """
        Get information about currently connected clients.

        Returns:
            Dict: Connected clients information
        """
        return {
            'total_connections': len(self.connected_clients),
            'clients_by_role': self._get_clients_by_role(),
            'active_sessions': len(self.user_sessions),
            'last_updated': datetime.utcnow().isoformat()
        }

    def _get_clients_by_role(self) -> Dict[str, int]:
        """Get count of clients by role."""
        role_counts = {'admin': 0, 'analyst': 0, 'user': 0}

        for client_info in self.connected_clients.values():
            role = client_info.get('role', 'user')
            if role in role_counts:
                role_counts[role] += 1

        return role_counts

    def stop(self):
        """Stop WebSocket manager and background tasks."""
        self.is_running = False
        logger.info("WebSocket manager stopped")

# =============================================================================
# WEBSOCKET EVENT HANDLERS FOR FLASK-SOCKETIO INTEGRATION
# =============================================================================

def create_websocket_handlers(socketio, websocket_manager):
    """
    Create additional WebSocket event handlers for Flask-SocketIO.

    Args:
        socketio: Flask-SocketIO instance
        websocket_manager: WebSocketManager instance
    """

    @socketio.on('get_fraud_history')
    def handle_fraud_history_request(data):
        """Handle request for fraud detection history."""
        try:
            # Get fraud history based on filters
            filters = data.get('filters', {})
            limit = data.get('limit', 50)

            # Mock fraud history data
            fraud_history = [
                {
                    'id': f'fraud_{i}',
                    'timestamp': datetime.utcnow().isoformat(),
                    'transaction_id': f'txn_{i}',
                    'risk_score': 85.5 + (i * 2),
                    'fraud_probability': 0.87,
                    'amount': 250.00 + (i * 10),
                    'merchant': f'Merchant_{i}',
                    'status': 'blocked' if i % 3 == 0 else 'flagged'
                }
                for i in range(limit)
            ]

            emit('fraud_history_response', {
                'history': fraud_history,
                'total_count': 1250,
                'filters_applied': filters
            })

        except Exception as e:
            logger.error(f"Error handling fraud history request: {e}")
            emit('error', {'message': 'Failed to get fraud history'})

    @socketio.on('update_fraud_threshold')
    def handle_fraud_threshold_update(data):
        """Handle fraud threshold update from admin."""
        try:
            session_id = request.sid

            if session_id not in websocket_manager.connected_clients:
                emit('error', {'message': 'Not authenticated'})
                return

            client_info = websocket_manager.connected_clients[session_id]

            # Check if user has admin privileges
            if client_info.get('role') != 'admin':
                emit('error', {'message': 'Insufficient privileges'})
                return

            new_threshold = data.get('threshold')
            threshold_type = data.get('type', 'risk_score')

            if not isinstance(new_threshold, (int, float)) or new_threshold < 0 or new_threshold > 100:
                emit('error', {'message': 'Invalid threshold value'})
                return

            # Update threshold (in real app, update database/config)
            update_notification = {
                'type': 'threshold_updated',
                'threshold_type': threshold_type,
                'old_value': 70,  # Mock old value
                'new_value': new_threshold,
                'updated_by': client_info['username'],
                'timestamp': datetime.utcnow().isoformat()
            }

            # Notify all admins and analysts
            socketio.emit('threshold_updated', update_notification, room='role_admin')
            socketio.emit('threshold_updated', update_notification, room='role_analyst')

            emit('threshold_update_success', {
                'threshold_type': threshold_type,
                'new_value': new_threshold
            })

            logger.info(f"Fraud threshold updated by {client_info['username']}: {threshold_type} = {new_threshold}")

        except Exception as e:
            logger.error(f"Error handling fraud threshold update: {e}")
            emit('error', {'message': 'Failed to update threshold'})

# =============================================================================
# REDIS INTEGRATION FOR SCALABLE WEBSOCKET MESSAGING
# =============================================================================

class RedisWebSocketIntegration:
    """
    Redis integration for scalable WebSocket messaging across multiple server instances.
    """

    def __init__(self, redis_client, websocket_manager):
        """
        Initialize Redis WebSocket integration.

        Args:
            redis_client: Redis client instance
            websocket_manager: WebSocketManager instance
        """
        self.redis_client = redis_client
        self.websocket_manager = websocket_manager
        self.pubsub = None
        self.is_listening = False

        if redis_client:
            self._setup_redis_pubsub()

    def _setup_redis_pubsub(self):
        """Setup Redis pub/sub for cross-server WebSocket messaging."""
        try:
            self.pubsub = self.redis_client.pubsub()

            # Subscribe to relevant channels
            channels = [
                'fraud_alerts',
                'system_notifications',
                'transaction_updates',
                'threshold_updates'
            ]

            for channel in channels:
                self.pubsub.subscribe(channel)

            # Start listening thread
            listen_thread = Thread(target=self._listen_to_redis, daemon=True)
            listen_thread.start()

            logger.info("Redis pub/sub setup completed")

        except Exception as e:
            logger.error(f"Error setting up Redis pub/sub: {e}")

    def _listen_to_redis(self):
        """Listen to Redis pub/sub messages and forward to WebSocket clients."""
        self.is_listening = True

        try:
            for message in self.pubsub.listen():
                if not self.is_listening:
                    break

                if message['type'] == 'message':
                    self._handle_redis_message(message)

        except Exception as e:
            logger.error(f"Error listening to Redis messages: {e}")

    def _handle_redis_message(self, message):
        """
        Handle incoming Redis pub/sub message.

        Args:
            message: Redis message
        """
        try:
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'].decode('utf-8'))

            # Route message based on channel
            if channel == 'fraud_alerts':
                self.websocket_manager.send_fraud_alert(data)
            elif channel == 'system_notifications':
                self.websocket_manager.send_system_notification(
                    data['type'],
                    data['message'],
                    data.get('target_roles')
                )
            elif channel == 'transaction_updates':
                self.websocket_manager.send_transaction_update(data)

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

    def publish_fraud_alert(self, fraud_data: Dict[str, Any]):
        """
        Publish fraud alert to Redis for cross-server distribution.

        Args:
            fraud_data: Fraud alert data
        """
        try:
            if self.redis_client:
                self.redis_client.publish('fraud_alerts', json.dumps(fraud_data))

        except Exception as e:
            logger.error(f"Error publishing fraud alert to Redis: {e}")

    def stop(self):
        """Stop Redis integration."""
        self.is_listening = False
        if self.pubsub:
            self.pubsub.close()

# =============================================================================
# MAIN EXECUTION FOR TESTING
# =============================================================================

if __name__ == '__main__':
    """
    Main execution block for testing WebSocket functionality.
    """
    from flask import Flask

    # Create test Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'

    # Initialize WebSocket manager
    websocket_manager = WebSocketManager(app)

    # Test fraud alert
    test_fraud_data = {
        'transaction_id': 'test_txn_001',
        'user_id': 'user_123',
        'amount': 500.00,
        'merchant_name': 'Suspicious Merchant',
        'risk_score': 95.5,
        'fraud_probability': 0.95,
        'location': {'country': 'Unknown'},
        'payment_method': 'card',
        'fraud_reasons': ['Unusual location', 'High amount', 'Velocity check failed']
    }

    # Queue fraud alert
    websocket_manager.send_fraud_alert(test_fraud_data)

    print("WebSocket manager initialized for testing")
    print("Connect to WebSocket at: http://localhost:5000")
    print("Use client with authentication token for testing")

    # Run Flask app with SocketIO
    if websocket_manager.socketio:
        websocket_manager.socketio.run(app, debug=True, port=5000)
