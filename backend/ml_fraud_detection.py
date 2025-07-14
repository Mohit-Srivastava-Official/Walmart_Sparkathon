"""
Advanced Machine Learning Fraud Detection System for SecureCart AI.
This module implements a sophisticated fraud detection pipeline using multiple
ML algorithms and real-time feature engineering for transaction analysis.
"""

# Standard library imports
import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

# Third-party imports
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib

# Configure logging
logger = logging.getLogger(__name__)

class FraudDetectionModel:
    """
    Advanced fraud detection system using ensemble learning and deep neural networks.

    This class implements a multi-layered approach to fraud detection:
    1. Feature engineering from transaction data
    2. Ensemble of traditional ML models (Random Forest, Gradient Boosting, etc.)
    3. Deep neural network for complex pattern recognition
    4. Real-time scoring and threshold-based classification
    """

    def __init__(self, model_path: str = './ml_models/'):
        """
        Initialize the fraud detection model with configuration.

        Args:
            model_path (str): Directory path to store and load trained models
        """
        self.model_path = model_path
        self.models = {}  # Dictionary to store different ML models
        self.scalers = {}  # Dictionary to store feature scalers
        self.encoders = {}  # Dictionary to store categorical encoders
        self.feature_names = []  # List of feature names for consistency
        self.threshold = 0.7  # Default fraud probability threshold
        self.is_trained = False  # Flag to track if models are trained

        # Create model directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)

        # Initialize model components
        self._initialize_models()

        # Load pre-trained models if available
        self._load_models()

    def _initialize_models(self):
        """
        Initialize all machine learning models with optimized parameters.
        Each model is tuned for different aspects of fraud detection.
        """
        # Random Forest - Good for feature importance and interpretability
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=100,           # Number of trees in the forest
            max_depth=10,               # Maximum depth of trees
            min_samples_split=5,        # Minimum samples to split a node
            min_samples_leaf=2,         # Minimum samples in leaf node
            random_state=42,            # For reproducible results
            n_jobs=-1                   # Use all available processors
        )

        # Gradient Boosting - Excellent for sequential learning
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=100,           # Number of boosting stages
            learning_rate=0.1,          # Learning rate for boosting
            max_depth=6,                # Maximum depth of trees
            random_state=42
        )

        # Logistic Regression - Fast and interpretable baseline
        self.models['logistic_regression'] = LogisticRegression(
            C=1.0,                      # Regularization strength
            penalty='l2',               # L2 regularization
            random_state=42,
            max_iter=1000               # Maximum iterations for convergence
        )

        # Multi-layer Perceptron - Neural network for complex patterns
        self.models['neural_network'] = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25),  # Three hidden layers
            activation='relu',          # ReLU activation function
            solver='adam',              # Adam optimizer
            alpha=0.001,               # L2 regularization parameter
            learning_rate='adaptive',   # Adaptive learning rate
            max_iter=500,              # Maximum iterations
            random_state=42
        )

        # Isolation Forest - Unsupervised anomaly detection
        self.models['isolation_forest'] = IsolationForest(
            contamination=0.1,          # Expected proportion of outliers
            random_state=42,
            n_jobs=-1
        )

        # Standard scaler for feature normalization
        self.scalers['standard'] = StandardScaler()

        # Label encoders for categorical variables
        self.encoders = {
            'merchant_category': LabelEncoder(),
            'payment_method': LabelEncoder(),
            'country': LabelEncoder(),
            'device_type': LabelEncoder()
        }

        logger.info("Initialized all ML models and preprocessors")

    def _extract_features(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract and engineer features from raw transaction data.

        This method converts raw transaction data into a feature vector
        suitable for machine learning models.

        Args:
            transaction_data (Dict): Raw transaction data

        Returns:
            np.ndarray: Engineered feature vector
        """
        features = []

        # Basic transaction features
        features.append(float(transaction_data.get('amount', 0)))
        features.append(float(transaction_data.get('userId', '0').replace('user_', '')))

        # Time-based features
        timestamp = datetime.fromisoformat(transaction_data.get('timestamp', datetime.utcnow().isoformat()))
        features.extend([
            timestamp.hour,                    # Hour of day (0-23)
            timestamp.weekday(),              # Day of week (0-6)
            timestamp.day,                    # Day of month (1-31)
            timestamp.month,                  # Month (1-12)
            int(timestamp.timestamp())        # Unix timestamp
        ])

        # Location-based features
        location = transaction_data.get('location', {})
        coordinates = location.get('coordinates', [0, 0])
        features.extend([
            float(coordinates[0]),            # Latitude
            float(coordinates[1]),            # Longitude
            len(location.get('city', '')),    # City name length
        ])

        # Categorical features (encoded as integers)
        merchant_category = transaction_data.get('merchantCategory', 'unknown')
        payment_method = transaction_data.get('paymentMethod', 'unknown')
        country = location.get('country', 'unknown')

        # Use label encoders to convert categorical to numerical
        try:
            features.append(self.encoders['merchant_category'].transform([merchant_category])[0])
        except (ValueError, AttributeError):
            features.append(0)  # Default for unknown categories

        try:
            features.append(self.encoders['payment_method'].transform([payment_method])[0])
        except (ValueError, AttributeError):
            features.append(0)

        try:
            features.append(self.encoders['country'].transform([country])[0])
        except (ValueError, AttributeError):
            features.append(0)

        # Device and network features
        device_info = transaction_data.get('deviceInfo', {})
        features.extend([
            len(device_info.get('deviceId', '')),      # Device ID length
            len(device_info.get('userAgent', '')),     # User agent length
            self._ip_to_numeric(device_info.get('ipAddress', '0.0.0.0'))  # IP as numeric
        ])

        # Merchant features
        features.extend([
            len(transaction_data.get('merchantName', '')),  # Merchant name length
            hash(transaction_data.get('merchantName', '')) % 1000  # Merchant hash (simple)
        ])

        # Advanced engineered features
        features.extend([
            # Amount-based features
            np.log1p(float(transaction_data.get('amount', 0))),  # Log-transformed amount
            float(transaction_data.get('amount', 0)) / 100,      # Amount in hundreds

            # Velocity features (would be calculated from historical data)
            0,  # Transactions in last hour (placeholder)
            0,  # Amount spent in last 24 hours (placeholder)
            0,  # Number of different merchants in last week (placeholder)

            # Anomaly indicators
            1 if timestamp.hour < 6 or timestamp.hour > 22 else 0,  # Unusual time
            1 if float(transaction_data.get('amount', 0)) > 1000 else 0,  # High amount
        ])

        return np.array(features)

    def _ip_to_numeric(self, ip_address: str) -> float:
        """
        Convert IP address to numeric representation for ML models.

        Args:
            ip_address (str): IP address in dotted decimal notation

        Returns:
            float: Numeric representation of IP address
        """
        try:
            parts = ip_address.split('.')
            return float(parts[0]) * 256**3 + float(parts[1]) * 256**2 + float(parts[2]) * 256 + float(parts[3])
        except (ValueError, IndexError):
            return 0.0  # Default for invalid IP addresses

    def _create_deep_learning_model(self, input_dim: int) -> keras.Model:
        """
        Create a deep neural network for fraud detection.

        Args:
            input_dim (int): Number of input features

        Returns:
            keras.Model: Compiled deep learning model
        """
        model = keras.Sequential([
            # Input layer with dropout for regularization
            layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            layers.Dropout(0.3),

            # Hidden layers with batch normalization
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            layers.Dense(32, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),

            layers.Dense(16, activation='relu'),
            layers.Dropout(0.2),

            # Output layer for binary classification
            layers.Dense(1, activation='sigmoid')
        ])

        # Compile model with appropriate optimizer and loss function
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )

        return model

    def train(self, training_data: List[Dict[str, Any]], labels: List[int]):
        """
        Train all fraud detection models on provided data.

        Args:
            training_data (List[Dict]): List of transaction dictionaries
            labels (List[int]): List of fraud labels (0=legitimate, 1=fraudulent)
        """
        logger.info(f"Starting training on {len(training_data)} transactions")

        # Extract features from all training transactions
        X = np.array([self._extract_features(transaction) for transaction in training_data])
        y = np.array(labels)

        # Store feature names for consistency
        self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]

        # Fit categorical encoders on training data
        categories = {
            'merchant_category': [t.get('merchantCategory', 'unknown') for t in training_data],
            'payment_method': [t.get('paymentMethod', 'unknown') for t in training_data],
            'country': [t.get('location', {}).get('country', 'unknown') for t in training_data],
        }

        for key, values in categories.items():
            self.encoders[key].fit(values)

        # Scale features for models that require normalization
        X_scaled = self.scalers['standard'].fit_transform(X)

        # Split data for training and validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train traditional ML models
        for name, model in self.models.items():
            if name == 'isolation_forest':
                # Isolation Forest is unsupervised (only uses normal transactions)
                normal_transactions = X_train[y_train == 0]
                model.fit(normal_transactions)
                logger.info(f"Trained {name} on {len(normal_transactions)} normal transactions")
            else:
                # Supervised models use both normal and fraudulent transactions
                model.fit(X_train, y_train)

                # Evaluate model performance
                val_predictions = model.predict(X_val)
                val_accuracy = np.mean(val_predictions == y_val)
                logger.info(f"Trained {name} - Validation accuracy: {val_accuracy:.3f}")

        # Train deep learning model
        dl_model = self._create_deep_learning_model(X_train.shape[1])

        # Train with early stopping and learning rate reduction
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]

        history = dl_model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )

        self.models['deep_learning'] = dl_model

        # Calculate final performance metrics
        self._evaluate_models(X_val, y_val)

        self.is_trained = True
        self._save_models()

        logger.info("Training completed successfully")

    def _evaluate_models(self, X_val: np.ndarray, y_val: np.ndarray):
        """
        Evaluate all trained models on validation data.

        Args:
            X_val (np.ndarray): Validation features
            y_val (np.ndarray): Validation labels
        """
        logger.info("Evaluating model performance:")

        for name, model in self.models.items():
            try:
                if name == 'isolation_forest':
                    # Isolation Forest returns -1 for outliers, 1 for inliers
                    predictions = model.predict(X_val)
                    predictions = np.where(predictions == -1, 1, 0)  # Convert to fraud labels
                elif name == 'deep_learning':
                    # Deep learning model returns probabilities
                    predictions = (model.predict(X_val) > self.threshold).astype(int).flatten()
                else:
                    # Traditional ML models
                    predictions = model.predict(X_val)

                accuracy = np.mean(predictions == y_val)
                logger.info(f"{name}: Accuracy = {accuracy:.3f}")

            except Exception as e:
                logger.error(f"Error evaluating {name}: {e}")

    def predict_fraud_probability(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict fraud probability for a single transaction.

        Args:
            transaction_data (Dict): Transaction data dictionary

        Returns:
            Dict: Prediction results with probability and classification
        """
        if not self.is_trained:
            logger.warning("Models not trained yet, using random prediction")
            return {
                'fraud_probability': np.random.random(),
                'is_fraud': np.random.choice([True, False]),
                'risk_score': np.random.randint(0, 100),
                'model_predictions': {},
                'confidence': 0.5
            }

        # Extract features from transaction
        features = self._extract_features(transaction_data)
        features_scaled = self.scalers['standard'].transform([features])

        # Get predictions from all models
        model_predictions = {}
        probabilities = []

        for name, model in self.models.items():
            try:
                if name == 'isolation_forest':
                    # Isolation Forest anomaly score
                    anomaly_score = model.decision_function([features_scaled[0]])[0]
                    # Convert to probability (more negative = more anomalous)
                    probability = max(0, min(1, (0.5 - anomaly_score) / 0.5))
                elif name == 'deep_learning':
                    # Deep learning model probability
                    probability = float(model.predict([features_scaled[0]])[0][0])
                else:
                    # Traditional ML models with probability prediction
                    if hasattr(model, 'predict_proba'):
                        probability = model.predict_proba([features_scaled[0]])[0][1]
                    else:
                        # For models without probability, use decision function
                        decision = model.decision_function([features_scaled[0]])[0]
                        probability = 1 / (1 + np.exp(-decision))  # Sigmoid transformation

                model_predictions[name] = float(probability)
                probabilities.append(probability)

            except Exception as e:
                logger.error(f"Error in {name} prediction: {e}")
                model_predictions[name] = 0.5  # Default probability
                probabilities.append(0.5)

        # Ensemble prediction (weighted average)
        weights = {
            'random_forest': 0.25,
            'gradient_boosting': 0.25,
            'deep_learning': 0.3,
            'neural_network': 0.15,
            'isolation_forest': 0.05
        }

        ensemble_probability = sum(
            model_predictions.get(name, 0.5) * weight
            for name, weight in weights.items()
        )

        # Calculate confidence based on model agreement
        confidence = 1.0 - np.std(probabilities) if probabilities else 0.5

        # Determine if transaction is fraudulent
        is_fraud = ensemble_probability > self.threshold
        risk_score = int(ensemble_probability * 100)

        return {
            'fraud_probability': float(ensemble_probability),
            'is_fraud': bool(is_fraud),
            'risk_score': risk_score,
            'model_predictions': model_predictions,
            'confidence': float(confidence),
            'threshold': self.threshold
        }

    def update_threshold(self, new_threshold: float):
        """
        Update the fraud detection threshold.

        Args:
            new_threshold (float): New threshold value (0.0 to 1.0)
        """
        if 0.0 <= new_threshold <= 1.0:
            self.threshold = new_threshold
            logger.info(f"Updated fraud threshold to {new_threshold}")
        else:
            raise ValueError("Threshold must be between 0.0 and 1.0")

    def _save_models(self):
        """Save all trained models and preprocessors to disk."""
        try:
            # Save traditional ML models and preprocessors
            for name, model in self.models.items():
                if name != 'deep_learning':
                    joblib.dump(model, os.path.join(self.model_path, f'{name}.pkl'))

            # Save deep learning model
            if 'deep_learning' in self.models:
                self.models['deep_learning'].save(os.path.join(self.model_path, 'deep_learning.h5'))

            # Save scalers and encoders
            joblib.dump(self.scalers, os.path.join(self.model_path, 'scalers.pkl'))
            joblib.dump(self.encoders, os.path.join(self.model_path, 'encoders.pkl'))

            # Save configuration
            config = {
                'feature_names': self.feature_names,
                'threshold': self.threshold,
                'is_trained': self.is_trained
            }
            with open(os.path.join(self.model_path, 'config.json'), 'w') as f:
                json.dump(config, f)

            logger.info("Models saved successfully")

        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def _load_models(self):
        """Load pre-trained models and preprocessors from disk."""
        try:
            config_path = os.path.join(self.model_path, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)

                self.feature_names = config.get('feature_names', [])
                self.threshold = config.get('threshold', 0.7)
                self.is_trained = config.get('is_trained', False)

            # Load traditional ML models
            for name in ['random_forest', 'gradient_boosting', 'logistic_regression',
                        'neural_network', 'isolation_forest']:
                model_path = os.path.join(self.model_path, f'{name}.pkl')
                if os.path.exists(model_path):
                    self.models[name] = joblib.load(model_path)

            # Load deep learning model
            dl_path = os.path.join(self.model_path, 'deep_learning.h5')
            if os.path.exists(dl_path):
                self.models['deep_learning'] = keras.models.load_model(dl_path)

            # Load scalers and encoders
            scalers_path = os.path.join(self.model_path, 'scalers.pkl')
            if os.path.exists(scalers_path):
                self.scalers = joblib.load(scalers_path)

            encoders_path = os.path.join(self.model_path, 'encoders.pkl')
            if os.path.exists(encoders_path):
                self.encoders = joblib.load(encoders_path)

            if self.is_trained:
                logger.info("Pre-trained models loaded successfully")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.is_trained = False

# =============================================================================
# MODEL TRAINING AND DEMO DATA GENERATION
# =============================================================================

def generate_demo_training_data(num_samples: int = 10000) -> Tuple[List[Dict], List[int]]:
    """
    Generate synthetic training data for demonstration purposes.
    In production, this would be replaced with real transaction data.

    Args:
        num_samples (int): Number of training samples to generate

    Returns:
        Tuple: (training_data, labels)
    """
    np.random.seed(42)  # For reproducible results

    training_data = []
    labels = []

    # Generate legitimate transactions (80% of data)
    for i in range(int(num_samples * 0.8)):
        transaction = {
            'id': f'txn_{i}',
            'userId': f'user_{np.random.randint(1, 1000)}',
            'amount': np.random.lognormal(4, 1),  # Log-normal distribution for amounts
            'currency': 'USD',
            'merchantName': np.random.choice(['Walmart', 'Target', 'Amazon', 'Best Buy', 'Costco']),
            'merchantCategory': np.random.choice(['grocery', 'electronics', 'clothing', 'gas_station']),
            'timestamp': (datetime.utcnow() - timedelta(days=np.random.randint(0, 30))).isoformat(),
            'location': {
                'country': np.random.choice(['USA', 'Canada', 'Mexico']),
                'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston']),
                'coordinates': [
                    np.random.uniform(25, 45),  # Latitude
                    np.random.uniform(-125, -70)  # Longitude
                ]
            },
            'paymentMethod': np.random.choice(['card', 'wallet', 'bank_transfer']),
            'deviceInfo': {
                'deviceId': f'device_{np.random.randint(1, 500)}',
                'ipAddress': f'{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}',
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        training_data.append(transaction)
        labels.append(0)  # Legitimate transaction

    # Generate fraudulent transactions (20% of data)
    for i in range(int(num_samples * 0.2)):
        transaction = {
            'id': f'fraud_txn_{i}',
            'userId': f'user_{np.random.randint(1, 1000)}',
            'amount': np.random.uniform(500, 5000),  # Higher amounts for fraud
            'currency': 'USD',
            'merchantName': np.random.choice(['Unknown Merchant', 'Suspicious Store', 'Quick Cash']),
            'merchantCategory': np.random.choice(['other', 'cash_advance', 'unknown']),
            'timestamp': (datetime.utcnow() - timedelta(hours=np.random.randint(0, 6))).isoformat(),  # Recent
            'location': {
                'country': np.random.choice(['Unknown', 'Russia', 'Nigeria', 'Romania']),
                'city': 'Unknown',
                'coordinates': [
                    np.random.uniform(-90, 90),  # Random worldwide coordinates
                    np.random.uniform(-180, 180)
                ]
            },
            'paymentMethod': 'card',
            'deviceInfo': {
                'deviceId': f'suspicious_device_{np.random.randint(1, 100)}',
                'ipAddress': f'{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}',
                'userAgent': 'Unknown'
            }
        }
        training_data.append(transaction)
        labels.append(1)  # Fraudulent transaction

    # Shuffle the data
    combined = list(zip(training_data, labels))
    np.random.shuffle(combined)
    training_data, labels = zip(*combined)

    return list(training_data), list(labels)

# =============================================================================
# MAIN EXECUTION FOR TESTING
# =============================================================================

if __name__ == '__main__':
    """
    Main execution block for testing and training the fraud detection model.
    This can be run standalone to train and test the model.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize fraud detection model
    fraud_detector = FraudDetectionModel()

    # Generate demo training data
    print("Generating training data...")
    training_data, labels = generate_demo_training_data(5000)

    # Train the model
    print("Training fraud detection models...")
    fraud_detector.train(training_data, labels)

    # Test with a sample transaction
    test_transaction = {
        'id': 'test_txn',
        'userId': 'user_123',
        'amount': 1500.0,
        'currency': 'USD',
        'merchantName': 'Unknown Merchant',
        'merchantCategory': 'other',
        'timestamp': datetime.utcnow().isoformat(),
        'location': {
            'country': 'Nigeria',
            'city': 'Lagos',
            'coordinates': [6.5244, 3.3792]
        },
        'paymentMethod': 'card',
        'deviceInfo': {
            'deviceId': 'suspicious_device_001',
            'ipAddress': '192.168.1.100',
            'userAgent': 'Mozilla/5.0'
        }
    }

    # Make prediction
    print("\nTesting fraud detection...")
    result = fraud_detector.predict_fraud_probability(test_transaction)

    print(f"Fraud Probability: {result['fraud_probability']:.3f}")
    print(f"Is Fraud: {result['is_fraud']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print("Model Predictions:")
    for model, prob in result['model_predictions'].items():
        print(f"  {model}: {prob:.3f}")

    print("\nFraud detection system ready for production use!")
