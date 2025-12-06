"""
GCP TRAINING WRAPPER - Fixed Version
Wraps your existing training pipeline with proper data handling
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
import sys
from datetime import datetime
from google.cloud import storage
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_preprocessing import RealEstateDataPreprocessor
from predictive_models import RealEstatePredictiveModels

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GCPModelTrainer:
    """Wrapper that adds GCP functionality to your existing training pipeline"""
    
    def __init__(self, data_path='data/Housing.csv'):
        self.data_path = data_path
        self.preprocessor = RealEstateDataPreprocessor()
        self.models = RealEstatePredictiveModels()
        self.results = {}
        
        logger.info("GCP Model Trainer initialized")
        logger.info(f"Data path: {data_path}")
    
    def train_all_models(self):
        """Execute complete training pipeline"""
        
        logger.info("="*70)
        logger.info("REAL ESTATE MODEL TRAINING - GCP VERSION")
        logger.info("="*70)
        
        # Step 1: Load Data
        logger.info("\nStep 1: Loading data...")
        if not os.path.exists(self.data_path):
            logger.error(f"❌ Data file not found: {self.data_path}")
            logger.error("Please provide the Housing.csv file")
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        else:
            df = pd.read_csv(self.data_path)
            logger.info(f"✓ Data loaded: {len(df)} records")
        
        logger.info(f"✓ Columns: {list(df.columns)}")
        logger.info(f"✓ Shape: {df.shape}")
        
        # Step 2: Process Housing.csv format
        logger.info("\nStep 2: Processing Housing.csv format...")
        df_processed = self.preprocessor.process_housing_data(df)
        logger.info(f"✓ Housing data processed: {df_processed.shape}")
        
        # Step 3: Prepare features
        logger.info("\nStep 3: Preparing features...")
        X_train, X_test, y_train, y_test = self.preprocessor.prepare_features(df_processed)
        logger.info(f"✓ Training set: {X_train.shape}")
        logger.info(f"✓ Test set: {X_test.shape}")
        
        # Step 4: Train ALL models
        logger.info("\n" + "="*70)
        logger.info("Step 4: Training all models...")
        logger.info("="*70)
        
        self.results = self.models.train_all_models(
            X_train, y_train, 
            X_test, y_test
        )
        
        self._log_results()
        return self.results
    
    def _create_housing_sample_dataset(self, n_samples=545):
        """
        Create a sample Housing dataset with correct column names
        Matches the actual Housing.csv format your models expect
        """
        logger.info(f"Generating {n_samples} sample properties...")
        
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
        
        df = pd.DataFrame(data)
        logger.info(f"✓ Sample dataset created with columns: {list(df.columns)}")
        return df
    
    def _log_results(self):
        """Log training results"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING RESULTS SUMMARY")
        logger.info("="*70)
        
        sorted_results = sorted(
            self.results.items(), 
            key=lambda x: x[1]['r2_score'], 
            reverse=True
        )
        
        for model_name, metrics in sorted_results:
            logger.info(f"\n{model_name}:")
            logger.info(f"  RMSE: ₹{metrics['rmse']:,.2f}")
            logger.info(f"  MAE:  ₹{metrics['mae']:,.2f}")
            logger.info(f"  R² Score: {metrics['r2_score']:.4f}")
            logger.info(f"  MAPE: {metrics['mape']:.2f}%")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"BEST MODEL: {self.models.best_model_name.upper()}")
        logger.info(f"R² Score: {self.results[self.models.best_model_name]['r2_score']:.4f}")
        logger.info(f"RMSE: ₹{self.results[self.models.best_model_name]['rmse']:,.2f}")
        logger.info(f"{'='*70}")
    
    def save_models_locally(self, path='models/saved_models'):
        """Save all trained models locally"""
        
        os.makedirs(path, exist_ok=True)
        logger.info(f"\nSaving models to: {path}")
        
        # Save all models
        self.models.save_models(path)
        logger.info("✓ All models saved")
        
        # Save preprocessor
        joblib.dump(
            self.preprocessor, 
            os.path.join(path, 'preprocessor.pkl')
        )
        logger.info("✓ Preprocessor saved")
        
        # Save metadata
        metadata = {
            'best_model': self.models.best_model_name,
            'trained_at': datetime.now().isoformat(),
            'results': {
                model_name: {
                    'rmse': float(metrics['rmse']),
                    'mae': float(metrics['mae']),
                    'r2_score': float(metrics['r2_score']),
                    'mape': float(metrics['mape'])
                }
                for model_name, metrics in self.results.items()
            },
            'features': [
                'area', 'bedrooms', 'bathrooms', 'stories',
                'mainroad', 'guestroom', 'basement', 'hotwaterheating',
                'airconditioning', 'parking', 'prefarea', 'furnishingstatus'
            ],
            'model_count': len(self.results),
            'models_included': list(self.results.keys()),
            'version': '1.0.0'
        }
        
        with open(os.path.join(path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("✓ Metadata saved")
        logger.info(f"✓ All {len(self.results)} models saved successfully!")
        
        return metadata
    
    def upload_to_gcs(self, bucket_name, local_path='models/saved_models', gcs_path='models/latest'):
        """Upload trained models to Google Cloud Storage"""
        
        logger.info(f"\nUploading models to GCS...")
        logger.info(f"Bucket: gs://{bucket_name}/{gcs_path}/")
        
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            if not os.path.exists(local_path):
                logger.error(f"Local path does not exist: {local_path}")
                return False
            
            # Upload all files
            for filename in os.listdir(local_path):
                local_file = os.path.join(local_path, filename)
                
                if os.path.isfile(local_file):
                    blob = bucket.blob(f"{gcs_path}/{filename}")
                    blob.upload_from_filename(local_file)
                    logger.info(f"  ✓ Uploaded: {filename}")
            
            logger.info(f"\n✓ Upload complete!")
            logger.info(f"Models available at: gs://{bucket_name}/{gcs_path}/")
            return True
        
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            raise

def main():
    """Main training execution"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Train real estate models with GCP integration'
    )
    parser.add_argument(
        '--data', 
        type=str, 
        default='data/Housing.csv',
        help='Path to training data CSV'
    )
    parser.add_argument(
        '--gcs-bucket', 
        type=str, 
        default=None,
        help='GCS bucket name for model storage'
    )
    parser.add_argument(
        '--gcs-path', 
        type=str, 
        default='models/latest',
        help='GCS path for models'
    )
    
    args = parser.parse_args()
    
    # Initialize and train
    trainer = GCPModelTrainer(data_path=args.data)
    logger.info("Starting training pipeline...")
    results = trainer.train_all_models()
    
    # Save locally
    local_path = 'models/saved_models'
    metadata = trainer.save_models_locally(local_path)
    
    # Upload to GCS
    if args.gcs_bucket:
        trainer.upload_to_gcs(args.gcs_bucket, local_path, args.gcs_path)
    else:
        logger.warning("\nNo GCS bucket specified. Models saved locally only.")
        logger.warning("To upload: --gcs-bucket YOUR_BUCKET_NAME")
    
    logger.info("\n" + "="*70)
    logger.info("✅ TRAINING COMPLETED!")
    logger.info("="*70)
    logger.info(f"Models: {len(results)} trained")
    logger.info(f"Best: {metadata['best_model']}")
    logger.info(f"R² Score: {results[metadata['best_model']]['r2_score']:.4f}")

if __name__ == '__main__':
    main()