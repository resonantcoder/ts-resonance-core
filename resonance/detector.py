import numpy as np
import joblib
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Resonance - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpectralDetector:
    """
    The primary engine for detecting spectral anomalies in time-series data.
    Supports two modes:
    1. 'statistical': Uses Isolation Forests for efficient outlier detection.
    2. 'neural': Uses LSTM Autoencoders for temporal sequence reconstruction.
    """
    
    def __init__(self, mode='statistical', window_size=50, contamination='auto'):
        self.mode = mode
        self.window_size = window_size
        self.contamination = contamination
        self.model = None
        self.scaler = None
        self._is_fitted = False
        
        logger.info(f"Initializing SpectralDetector in mode: '{self.mode}'")

    def fit(self, data):
        """
        Learns the 'normal' vibrational state of the system from the provided data.
        
        Args:
            data (np.array): Training data. Shape (n_samples, n_features).
        """
        logger.info(f"Fitting model on {len(data)} samples...")
        
        # Data validation
        data = np.array(data)
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)

        if self.mode == 'statistical':
            self._fit_statistical(data)
        elif self.mode == 'neural':
            self._fit_neural(data)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
            
        self._is_fitted = True
        logger.info("Model fitting complete.")

    def score(self, data):
        """
        Scores the input data based on deviation from the learned normal state.
        
        Args:
            data (np.array): Input data to analyze.
            
        Returns:
            np.array: Anomaly scores. 
                      For 'statistical': -1 for anomaly, 1 for normal.
                      For 'neural': Reconstruction error (0.0 to 1.0+).
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before scoring.")
            
        data = np.array(data)
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)

        if self.mode == 'statistical':
            return self._score_statistical(data)
        elif self.mode == 'neural':
            return self._score_neural(data)

    def save(self, filepath):
        """Saves the current model state to disk."""
        if self.mode == 'neural':
            # For neural, we save weights separately or use Keras format
            # This is a simplified implementation for the PoC
            logger.warning("Saving neural models requires specific Keras handling. Saving scaler/config only.")
            
        joblib.dump({
            'mode': self.mode,
            'model': self.model if self.mode == 'statistical' else None, # Keras models don't pickle well
            'config': {
                'window_size': self.window_size,
                'contamination': self.contamination
            }
        }, filepath)
        logger.info(f"Model state saved to {filepath}")

    def load(self, filepath):
        """Loads a model state from disk."""
        state = joblib.load(filepath)
        self.mode = state['mode']
        if self.mode == 'statistical':
            self.model = state['model']
        self._is_fitted = True
        logger.info(f"Model loaded from {filepath}")

    # --- Internal Statistical Engine ---
    def _fit_statistical(self, data):
        from sklearn.ensemble import IsolationForest
        self.model = IsolationForest(contamination=self.contamination, random_state=42)
        self.model.fit(data)

    def _score_statistical(self, data):
        # Returns -1 for outliers, 1 for inliers
        return self.model.predict(data)

    # --- Internal Neural Engine (The "TSPulse" Proxy) ---
    def _fit_neural(self, data):
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
        except ImportError:
            raise ImportError("TensorFlow is required for 'neural' mode. Install with `pip install tensorflow`.")

        # Create sequences
        X = self._create_sequences(data, self.window_size)
        n_features = data.shape[1]
        
        # LSTM Autoencoder Architecture
        self.model = Sequential([
            LSTM(64, activation='relu', input_shape=(self.window_size, n_features), return_sequences=True),
            LSTM(32, activation='relu', return_sequences=False),
            RepeatVector(self.window_size),
            LSTM(32, activation='relu', return_sequences=True),
            LSTM(64, activation='relu', return_sequences=True),
            TimeDistributed(Dense(n_features))
        ])
        
        self.model.compile(optimizer='adam', loss='mse')
        self.model.fit(X, X, epochs=10, batch_size=32, verbose=0)

    def _score_neural(self, data):
        # Calculate Reconstruction Error (MSE)
        X = self._create_sequences(data, self.window_size)
        X_pred = self.model.predict(X, verbose=0)
        mse = np.mean(np.power(X - X_pred, 2), axis=1)
        # Average the features to get a single score per window
        return np.mean(mse, axis=1)

    def _create_sequences(self, data, window_size):
        sequences = []
        for i in range(len(data) - window_size + 1):
            sequences.append(data[i : i + window_size])
        return np.array(sequences)
