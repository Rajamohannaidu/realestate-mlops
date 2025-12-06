# src/data_preprocessing.py - FIXED VERSION

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
        df = df.copy()
        
        # Ensure target column exists
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found. Available: {list(df.columns)}")
        
        # Encode categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if target_col in categorical_cols:
            categorical_cols.remove(target_col)
        
        print(f"Encoding categorical columns: {categorical_cols}")
        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
                print(f"  ✓ Encoded {col}")
        
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
        """
        Process the Housing.csv dataset with specific transformations
        Handles case-insensitive column names
        """
        df = df.copy()
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Convert yes/no columns to binary (case-insensitive)
        binary_columns = ['mainroad', 'guestroom', 'basement', 'hotwaterheating', 
                         'airconditioning', 'prefarea']
        
        for col in binary_columns:
            if col in df.columns:
                # Convert to lowercase and map
                df[col] = df[col].str.lower().map({'yes': 1, 'no': 0})
                print(f"✓ Converted {col} to binary")
            else:
                print(f"⚠️  Column '{col}' not found. Skipping...")
        
        # Map furnishing status to numeric (case-insensitive)
        if 'furnishingstatus' in df.columns:
            df['furnishingstatus'] = df['furnishingstatus'].str.lower().map({
                'furnished': 2,
                'semi-furnished': 1,
                'unfurnished': 0
            })
            print(f"✓ Converted furnishingstatus to numeric")
        else:
            print(f"⚠️  Column 'furnishingstatus' not found. Skipping...")
        
        return df
    
    def create_sample_dataset(self, n_samples=1000):
        """Generate sample real estate dataset for testing"""
        np.random.seed(42)
        
        data = {
            'price': np.random.uniform(1000000, 15000000, n_samples),
            'area': np.random.uniform(1500, 12000, n_samples),
            'bedrooms': np.random.randint(1, 6, n_samples),
            'bathrooms': np.random.randint(1, 4, n_samples),
            'stories': np.random.randint(1, 4, n_samples),
            'mainroad': np.random.choice(['yes', 'no'], n_samples),
            'guestroom': np.random.choice(['yes', 'no'], n_samples),
            'basement': np.random.choice(['yes', 'no'], n_samples),
            'hotwaterheating': np.random.choice(['yes', 'no'], n_samples),
            'airconditioning': np.random.choice(['yes', 'no'], n_samples),
            'parking': np.random.randint(0, 4, n_samples),
            'prefarea': np.random.choice(['yes', 'no'], n_samples),
            'furnishingstatus': np.random.choice(['furnished', 'semi-furnished', 'unfurnished'], n_samples)
        }
        
        return pd.DataFrame(data)


# Example usage
if __name__ == "__main__":
    preprocessor = RealEstateDataPreprocessor()
    
    # Load the actual Housing.csv file
    try:
        df = preprocessor.load_data('Housing.csv')
        print(f"✓ Loaded Housing.csv: {len(df)} records")
        print(f"  Columns: {list(df.columns)}")
        
        # Process housing-specific columns
        df = preprocessor.process_housing_data(df)
        print("✓ Processed housing data")
        
        # Clean data
        df = preprocessor.clean_data(df)
        print(f"✓ Cleaned data: {len(df)} records")
        
        # Feature engineering
        df = preprocessor.feature_engineering(df)
        print(f"✓ Feature engineering complete: {df.shape[1]} features")
        
        # Prepare for modeling
        X_train, X_test, y_train, y_test = preprocessor.prepare_features(df)
        
        print(f"\n✓ Training set: {X_train.shape}")
        print(f"✓ Test set: {X_test.shape}")
        print(f"✓ Features: {list(preprocessor.feature_names)}")
        
    except FileNotFoundError:
        print("❌ Housing.csv not found.")
        print("Please place Housing.csv in the same directory as this script")