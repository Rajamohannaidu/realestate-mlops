# src/predictive_models.py

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib

class RealEstatePredictiveModels:
    """Collection of ML and DL models for real estate price prediction"""
    
    def __init__(self):
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        
    def build_neural_network(self, input_dim):
        """Build a deep learning model for price prediction"""
        model = keras.Sequential([
            layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(1)
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_all_models(self, X_train, y_train, X_test, y_test):
        """Train multiple models and compare performance"""
        results = {}
        
        # 1. Linear Regression
        print("Training Linear Regression...")
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        self.models['linear_regression'] = lr
        results['linear_regression'] = self.evaluate_model(lr, X_test, y_test)
        
        # 2. Ridge Regression
        print("Training Ridge Regression...")
        ridge = Ridge(alpha=1.0)
        ridge.fit(X_train, y_train)
        self.models['ridge'] = ridge
        results['ridge'] = self.evaluate_model(ridge, X_test, y_test)
        
        # 3. Random Forest
        print("Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        self.models['random_forest'] = rf
        results['random_forest'] = self.evaluate_model(rf, X_test, y_test)
        
        # 4. Gradient Boosting
        print("Training Gradient Boosting...")
        gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
        gb.fit(X_train, y_train)
        self.models['gradient_boosting'] = gb
        results['gradient_boosting'] = self.evaluate_model(gb, X_test, y_test)
        
        # 5. XGBoost
        print("Training XGBoost...")
        xgb = XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        xgb.fit(X_train, y_train)
        self.models['xgboost'] = xgb
        results['xgboost'] = self.evaluate_model(xgb, X_test, y_test)
        
        # 6. LightGBM
        print("Training LightGBM...")
        lgbm = LGBMRegressor(n_estimators=100, random_state=42, n_jobs=-1, 
                            verbose=-1, min_child_samples=5)
        lgbm.fit(X_train, y_train)
        self.models['lightgbm'] = lgbm
        results['lightgbm'] = self.evaluate_model(lgbm, X_test, y_test)
        
        # 7. Deep Learning Model
        print("Training Neural Network...")
        nn = self.build_neural_network(X_train.shape[1])
        
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=10, restore_best_weights=True
        )
        
        history = nn.fit(
            X_train, y_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=0
        )
        
        self.models['neural_network'] = nn
        results['neural_network'] = self.evaluate_model(nn, X_test, y_test)
        
        # Find best model
        best_r2 = max(results.items(), key=lambda x: x[1]['r2_score'])
        self.best_model_name = best_r2[0]
        self.best_model = self.models[best_r2[0]]
        
        print(f"\nBest Model: {self.best_model_name} (R² = {best_r2[1]['r2_score']:.4f})")
        
        return results
    
    def evaluate_model(self, model, X_test, y_test):
        """Evaluate model performance"""
        y_pred = model.predict(X_test)
        
        # Flatten predictions if needed (for neural networks)
        if len(y_pred.shape) > 1:
            y_pred = y_pred.flatten()
        
        # Convert to numpy array if pandas Series
        if hasattr(y_test, 'values'):
            y_test_array = y_test.values
        else:
            y_test_array = y_test
        
        mse = mean_squared_error(y_test_array, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test_array, y_pred)
        r2 = r2_score(y_test_array, y_pred)
        
        # Safe MAPE calculation with zero handling
        epsilon = 1e-10
        mape = np.mean(np.abs((y_test_array - y_pred) / (y_test_array + epsilon))) * 100
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2_score': r2,
            'mape': mape
        }
    
    def predict(self, X, model_name=None):
        """Make predictions using specified or best model"""
        if model_name is None:
            model = self.best_model
        else:
            model = self.models.get(model_name, self.best_model)
        
        predictions = model.predict(X)
        
        # Flatten if neural network returns 2D array
        if len(predictions.shape) > 1:
            predictions = predictions.flatten()
        
        return predictions
    
    def predict_future_prices(self, X, years=5):
        """Predict future property prices with appreciation"""
        current_predictions = self.predict(X)
        
        # Assume average annual appreciation rate of 3-5%
        appreciation_rate = 0.04
        
        future_predictions = {}
        for year in range(1, years + 1):
            future_price = current_predictions * (1 + appreciation_rate) ** year
            future_predictions[f'year_{year}'] = future_price
        
        return future_predictions
    
    def save_models(self, directory='models/saved_models/'):
        """Save all trained models"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        for name, model in self.models.items():
            if name == 'neural_network':
                model.save(f'{directory}{name}.h5')
            else:
                joblib.dump(model, f'{directory}{name}.pkl')
        
        print(f"Models saved to {directory}")
    
    def load_models(self, directory='models/saved_models/'):
        """Load pre-trained models"""
        import os
        
        for filename in os.listdir(directory):
            if filename.endswith('.pkl'):
                name = filename.replace('.pkl', '')
                self.models[name] = joblib.load(f'{directory}{filename}')
            elif filename.endswith('.h5'):
                name = filename.replace('.h5', '')
                self.models[name] = keras.models.load_model(f'{directory}{filename}')
        
        print(f"Loaded {len(self.models)} models")

# Example usage
if __name__ == "__main__":
    from data_preprocessing import RealEstateDataPreprocessor
    
    # Load and preprocess data
    preprocessor = RealEstateDataPreprocessor()
    df = preprocessor.load_data('data/sample_data.csv')
    df = preprocessor.clean_data(df)
    df = preprocessor.feature_engineering(df)
    
    categorical_cols = ['location', 'property_type']
    df_encoded = preprocessor.encode_categorical(df, categorical_cols)
    
    X_train, X_test, y_train, y_test = preprocessor.prepare_features(df_encoded)
    
    # Train models
    models = RealEstatePredictiveModels()
    results = models.train_all_models(X_train, y_train, X_test, y_test)
    
    # Print results
    print("\nModel Performance Comparison:")
    for model_name, metrics in results.items():
        print(f"\n{model_name.upper()}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
    
    # Save models
    models.save_models()