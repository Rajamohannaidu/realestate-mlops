# config.py

"""
Configuration settings for Real Estate Investment Advisor
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
SAVED_MODELS_DIR = MODELS_DIR / "saved_models"
EXPLAINABILITY_DIR = MODELS_DIR / "explainability"

# Create directories if they don't exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
                  MODELS_DIR, SAVED_MODELS_DIR, EXPLAINABILITY_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Model configuration
MODEL_CONFIG = {
    'random_forest': {
        'n_estimators': 100,
        'max_depth': None,
        'min_samples_split': 2,
        'random_state': 42
    },
    'xgboost': {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 6,
        'random_state': 42
    },
    'lightgbm': {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'num_leaves': 31,
        'random_state': 42
    },
    'neural_network': {
        'layers': [128, 64, 32],
        'dropout': [0.3, 0.2, 0.0],
        'activation': 'relu',
        'learning_rate': 0.001,
        'batch_size': 32,
        'epochs': 100
    }
}

# Data preprocessing configuration
PREPROCESSING_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'categorical_columns': ['location', 'property_type'],
    'numeric_columns': ['area', 'bedrooms', 'bathrooms', 'year_built', 
                       'parking_spaces', 'amenities_score']
}

# Investment analytics configuration
ANALYTICS_CONFIG = {
    'default_appreciation_rate': 0.04,  # 4% annual
    'default_vacancy_rate': 0.05,       # 5%
    'default_maintenance_rate': 0.01,   # 1% of property value
    'holding_periods': [1, 3, 5, 10],   # years
}

# Explainability configuration
EXPLAINABILITY_CONFIG = {
    'shap': {
        'max_samples': 100,
        'check_additivity': False
    },
    'lime': {
        'num_features': 10,
        'num_samples': 1000
    }
}

# Chatbot configuration
CHATBOT_CONFIG = {
    'model_name': 'llama-3.3-70b-versatile',  # or 'llama2-70b-4096'
    'temperature': 0.7,
    'max_tokens': 1024,
    'top_p': 0.9
}

# Streamlit configuration
STREAMLIT_CONFIG = {
    'page_title': 'Real Estate Investment Advisor',
    'page_icon': '🏘️',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# API configuration
API_CONFIG = {
    'groq_api_key': os.getenv('GROQ_API_KEY'),
    'rate_limit': 60,  # requests per minute
    'timeout': 30  # seconds
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': PROJECT_ROOT / 'logs' / 'app.log'
}

# Feature engineering configuration
FEATURE_ENGINEERING = {
    'derived_features': [
        'price_per_sqft',
        'bed_bath_ratio',
        'property_age'
    ],
    'interaction_features': [
        'area_bedrooms',
        'location_property_type'
    ]
}

# Visualization configuration
VISUALIZATION_CONFIG = {
    'color_schemes': {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e',
        'success': '#2ca02c',
        'warning': '#d62728',
        'info': '#9467bd'
    },
    'chart_height': 400,
    'dpi': 300
}

# Sample data generation configuration
SAMPLE_DATA_CONFIG = {
    'n_samples': 1000,
    'area_range': (500, 5000),
    'bedrooms_range': (1, 6),
    'bathrooms_range': (1, 4),
    'year_built_range': (1980, 2024),
    'locations': ['Urban', 'Suburban', 'Rural'],
    'property_types': ['Apartment', 'House', 'Condo', 'Villa'],
    'parking_range': (0, 4),
    'amenities_range': (1, 11)
}

# Export all configurations
__all__ = [
    'PROJECT_ROOT',
    'DATA_DIR',
    'MODELS_DIR',
    'MODEL_CONFIG',
    'PREPROCESSING_CONFIG',
    'ANALYTICS_CONFIG',
    'EXPLAINABILITY_CONFIG',
    'CHATBOT_CONFIG',
    'STREAMLIT_CONFIG',
    'API_CONFIG',
    'LOGGING_CONFIG',
    'FEATURE_ENGINEERING',
    'VISUALIZATION_CONFIG',
    'SAMPLE_DATA_CONFIG'
]