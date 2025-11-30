# ============================================================================
# GCP TRAINING WRAPPER - Wraps Your Existing Training Pipeline
# ============================================================================
# PURPOSE: Adds GCP integration to your existing model_training.py
# FEATURES: 
#   - Uses your existing RealEstateDataPreprocessor
#   - Uses your existing RealEstatePredictiveModels (all 7 models)
#   - Uploads trained models to Google Cloud Storage
#   - Saves metadata for production deployment
# ============================================================================

import pandas as pd
import numpy as np
import joblib
import json
import os
import sys
from datetime import datetime
from google.cloud import storage
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules (no changes needed to them!)
from data_preprocessing import RealEstateDataPreprocessor
from predictive_models import RealEstatePredictiveModels

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GCPModelTrainer:
    """
    Wrapper that adds GCP functionality to your existing training pipeline
    """
    
    def __init__(self, data_path='data/Housing.csv'):
        """
        Initialize trainer with your existing components
        
        Args:
            data_path: Path to your Housing.csv or other training data
        """
        self.data_path = data_path
        self.preprocessor = RealEstateDataPreprocessor()
        self.models = RealEstatePredictiveModels()
        self.results = {}
        
        logger.info("GCP Model Trainer initialized")
        logger.info(f"Data path: {data_path}")
    
    def train_all_models(self):
        """
        Execute complete training pipeline using YOUR existing code
        This calls your original training logic - no changes needed!
        """
        logger.info("="*70)
        logger.info("REAL ESTATE MODEL TRAINING - GCP VERSION")
        logger.info("="*70)
        
        # Step 1: Load Data
        logger.info("\n Step 1: Loading data...")
        if not os.path.exists(self.data_path):
            logger.warning("Data file not found. Creating sample dataset...")
            df = self.preprocessor.create_sample_dataset(n_samples=1000)
            os.makedirs('data', exist_ok=True)
            df.to_csv(self.data_path, index=False)
            logger.info(f"✓ Sample dataset created: {self.data_path}")
        else:
            df = self.preprocessor.load_data(self.data_path)
            logger.info(f"✓ Data loaded: {len(df)} records")
        
        # Step 2: Preprocess using YOUR existing pipeline
        logger.info("\n Step 2: Preprocessing data...")
        df_clean = self.preprocessor.clean_data(df)
        logger.info(f"✓ Data cleaned: {len(df_clean)} records")
        
        # Step 3: Process Housing.csv specific format
        logger.info("\n Step 3: Processing Housing.csv format...")
        df_processed = self.preprocessor.process_housing_data(df_clean)
        logger.info(f"✓ Housing data processed: {df_processed.shape}")
        
        # Step 4: Prepare features using YOUR existing method
        logger.info("\n Step 4: Preparing features...")
        X_train, X_test, y_train, y_test = self.preprocessor.prepare_features(
            df_processed, 
            target='price'
        )
        logger.info(f"✓ Training set: {X_train.shape}")
        logger.info(f"✓ Test set: {X_test.shape}")
        
        # Step 5: Train ALL 7 models using YOUR existing method
        logger.info("\n" + "="*70)
        logger.info(" Step 5: Training all models...")
        logger.info("="*70)
        
        # This calls YOUR train_all_models method - trains all 7 models!
        self.results = self.models.train_all_models(
            X_train, y_train, 
            X_test, y_test
        )
        
        # Display results
        self._log_results()
        
        return self.results
    
    def _log_results(self):
        """Log training results in a nice format"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING RESULTS SUMMARY")
        logger.info("="*70)
        
        # Sort models by R² score
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
        logger.info(f"{'='*70}")
    
    def save_models_locally(self, path='models/saved_models'):
        """
        Save all trained models locally
        
        Args:
            path: Directory to save models
        """
        os.makedirs(path, exist_ok=True)
        
        logger.info(f"\nSaving models to: {path}")
        
        # Save all 7 models using YOUR existing method
        self.models.save_models(path)
        
        # Save preprocessor (needed for inference)
        joblib.dump(
            self.preprocessor, 
            os.path.join(path, 'preprocessor.pkl')
        )
        logger.info("✓ Preprocessor saved")
        
        # Save metadata with all model metrics
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
            'feature_names': list(self.preprocessor.feature_names) 
                if hasattr(self.preprocessor, 'feature_names') 
                else [],
            'model_count': len(self.results),
            'models_included': list(self.results.keys())
        }
        
        with open(os.path.join(path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("✓ Metadata saved")
        logger.info(f"✓ All {len(self.results)} models saved successfully!")
        
        return metadata
    
    def upload_to_gcs(self, bucket_name, local_path, gcs_path):
        """
        Upload trained models to Google Cloud Storage
        
        Args:
            bucket_name: GCS bucket name (e.g., 'your-project-ml-models')
            local_path: Local directory with models
            gcs_path: GCS path prefix (e.g., 'models/latest')
        """
        logger.info(f"\nUploading models to GCS...")
        logger.info(f"Bucket: gs://{bucket_name}/{gcs_path}/")
        
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            # Upload all files in the directory
            for filename in os.listdir(local_path):
                local_file = os.path.join(local_path, filename)
                
                if os.path.isfile(local_file):
                    blob = bucket.blob(f"{gcs_path}/{filename}")
                    blob.upload_from_filename(local_file)
                    logger.info(f"  ✓ Uploaded: {filename}")
            
            logger.info(f"\n✓ Upload complete!")
            logger.info(f"Models available at: gs://{bucket_name}/{gcs_path}/")
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            raise

def main():
    """
    Main training execution with GCP integration
    """
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
        help='GCS bucket name for model storage (e.g., your-project-ml-models)'
    )
    parser.add_argument(
        '--gcs-path', 
        type=str, 
        default='models/latest',
        help='GCS path for models (default: models/latest)'
    )
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = GCPModelTrainer(data_path=args.data)
    
    # Train all models
    logger.info("Starting training pipeline...")
    results = trainer.train_all_models()
    
    # Save models locally
    local_path = 'models/saved_models'
    metadata = trainer.save_models_locally(local_path)
    
    # Upload to GCS if bucket specified
    if args.gcs_bucket:
        trainer.upload_to_gcs(args.gcs_bucket, local_path, args.gcs_path)
    else:
        logger.warning("\nNo GCS bucket specified. Models saved locally only.")
        logger.warning("To upload to GCS, use: --gcs-bucket YOUR_BUCKET_NAME")
    
    logger.info("\n" + "="*70)
    logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("="*70)
    logger.info(f"\nModels trained: {len(results)}")
    logger.info(f"Best model: {metadata['best_model']}")
    logger.info(f"Best R² score: {results[metadata['best_model']]['r2_score']:.4f}")
    
    return results

if __name__ == '__main__':
    main()