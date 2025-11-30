# src/data_preprocessing.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

class RealEstateDataPreprocessor:
    """Handles data loading, cleaning, and preprocessing for real estate data"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        
    def load_data(self, file_path):
        """Load real estate data from CSV"""
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} records")
        return df
    
    def clean_data(self, df):
        """Clean and handle missing values"""
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # Handle categorical missing values
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna(df[col].mode()[0])
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        return df
    
    def feature_engineering(self, df):
        """Create additional features for better predictions"""
        if 'price' in df.columns and 'area' in df.columns:
            df['price_per_sqft'] = df['price'] / df['area']
        
        if 'bedrooms' in df.columns and 'bathrooms' in df.columns:
            df['bed_bath_ratio'] = df['bedrooms'] / (df['bathrooms'] + 1)
        
        if 'year_built' in df.columns:
            df['property_age'] = 2025 - df['year_built']
        
        return df
    
    def encode_categorical(self, df, categorical_cols):
        """Encode categorical variables"""
        df_encoded = df.copy()
        
        for col in categorical_cols:
            if col in df_encoded.columns:
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
                self.label_encoders[col] = le
        
        return df_encoded
    
    def prepare_features(self, df, target_col='price', test_size=0.2):
        """Prepare features and target for modeling"""
        # Separate features and target
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        
        return X_train, X_test, y_train, y_test
    
    def process_housing_data(self, df):
        """Process the Housing.csv dataset with specific transformations"""
        
        # Convert yes/no columns to binary
        binary_columns = ['mainroad', 'guestroom', 'basement', 'hotwaterheating', 
                         'airconditioning', 'prefarea']
        
        for col in binary_columns:
            df[col] = df[col].map({'yes': 1, 'no': 0})
        
        # Map furnishing status to numeric
        df['furnishingstatus'] = df['furnishingstatus'].map({
            'furnished': 2,
            'semi-furnished': 1,
            'unfurnished': 0
        })
        
        return df
    
    def create_sample_dataset(self, n_samples=1000):
        """Generate sample real estate dataset for testing"""
        np.random.seed(42)
        
        data = {
            'area': np.random.randint(500, 5000, n_samples),
            'bedrooms': np.random.randint(1, 6, n_samples),
            'bathrooms': np.random.randint(1, 4, n_samples),
            'year_built': np.random.randint(1980, 2024, n_samples),
            'location': np.random.choice(['Urban', 'Suburban', 'Rural'], n_samples),
            'property_type': np.random.choice(['Apartment', 'House', 'Condo', 'Villa'], n_samples),
            'parking_spaces': np.random.randint(0, 4, n_samples),
            'amenities_score': np.random.randint(1, 11, n_samples),
        }
        
        df = pd.DataFrame(data)
        
        # Generate price based on features
        base_price = (
            df['area'] * 150 + 
            df['bedrooms'] * 50000 + 
            df['bathrooms'] * 30000 + 
            (2025 - df['year_built']) * -2000 +
            df['parking_spaces'] * 20000 +
            df['amenities_score'] * 10000
        )
        
        # Add location multiplier
        location_multiplier = df['location'].map({
            'Urban': 1.5, 'Suburban': 1.2, 'Rural': 0.8
        })
        
        df['price'] = base_price * location_multiplier + np.random.normal(0, 50000, n_samples)
        df['price'] = df['price'].clip(lower=100000)
        
        return df

# Example usage
if __name__ == "__main__":
    preprocessor = RealEstateDataPreprocessor()
    
    # Load the actual Housing.csv file
    try:
        df = preprocessor.load_data('Housing.csv')
        print(f"Loaded Housing.csv: {len(df)} records")
        
        # Process housing-specific columns
        df = preprocessor.process_housing_data(df)
        print("✓ Processed housing data")
        
        # Clean data
        df = preprocessor.clean_data(df)
        print(f"✓ Cleaned data: {len(df)} records")
        
        # Feature engineering
        df = preprocessor.feature_engineering(df)
        print(f"✓ Feature engineering complete: {df.shape[1]} features")
        
        # Encode categorical if any remain
        categorical_cols = [col for col in df.columns if df[col].dtype == 'object' and col != 'price']
        if categorical_cols:
            df = preprocessor.encode_categorical(df, categorical_cols)
            print(f"✓ Encoded categorical columns: {categorical_cols}")
        
        # Prepare for modeling
        X_train, X_test, y_train, y_test = preprocessor.prepare_features(df)
        
        print(f"\n✓ Training set: {X_train.shape}")
        print(f"✓ Test set: {X_test.shape}")
        print(f"✓ Features: {list(preprocessor.feature_names)}")
        
        # Save processed data
        df.to_csv('data/processed/housing_processed.csv', index=False)
        print("\n✓ Saved processed data to data/processed/housing_processed.csv")
        
    except FileNotFoundError:
        print("Housing.csv not found. Creating sample dataset...")
        df = preprocessor.create_sample_dataset(1000)
        df.to_csv('data/sample_data.csv', index=False)
        print("✓ Sample dataset created at data/sample_data.csv")