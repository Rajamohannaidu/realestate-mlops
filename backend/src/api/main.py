# backend/src/api/main.py
"""
Complete FastAPI Backend for Real Estate Investment Advisor
Handles all ML predictions, analytics, and explainability
WITH GRACEFUL MODEL LOADING FOR CLOUD RUN
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import joblib
import numpy as np
import pandas as pd
import json
import os
import sys
from typing import List, Optional, Dict, Any
from google.cloud import storage
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'training'))

# Import your existing modules
from data_preprocessing import RealEstateDataPreprocessor
from predictive_models import RealEstatePredictiveModels
from investment_analytics import InvestmentAnalytics
from explainability import ModelExplainability
from chatbot import RealEstateInvestmentChatbot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real Estate Investment Advisor API",
    description="ML-powered API for real estate predictions and investment analysis",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models (Using v1 syntax for compatibility)
# ============================================================================

class PropertyInput(BaseModel):
    """Input for price prediction"""
    area: float = Field(..., gt=0, description="Area in square feet")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: int = Field(..., ge=0, description="Number of bathrooms")
    stories: int = Field(..., ge=1, description="Number of stories")
    mainroad: str = Field(..., description="On main road? (yes/no)")
    guestroom: str = Field(..., description="Has guest room? (yes/no)")
    basement: str = Field(..., description="Has basement? (yes/no)")
    hotwaterheating: str = Field(..., description="Has hot water heating? (yes/no)")
    airconditioning: str = Field(..., description="Has AC? (yes/no)")
    parking: int = Field(..., ge=0, description="Number of parking spaces")
    prefarea: str = Field(..., description="In preferred area? (yes/no)")
    furnishingstatus: str = Field(..., description="Furnishing status (furnished/semi-furnished/unfurnished)")
    
    @validator('mainroad', 'guestroom', 'basement', 'hotwaterheating', 
               'airconditioning', 'prefarea')
    def validate_yes_no(cls, v):
        if v.lower() not in ['yes', 'no']:
            raise ValueError('Must be "yes" or "no"')
        return v.lower()
    
    @validator('furnishingstatus')
    def validate_furnishing(cls, v):
        valid = ['furnished', 'semi-furnished', 'unfurnished']
        if v.lower() not in valid:
            raise ValueError(f'Must be one of {valid}')
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "area": 7420,
                "bedrooms": 4,
                "bathrooms": 2,
                "stories": 3,
                "mainroad": "yes",
                "guestroom": "no",
                "basement": "no",
                "hotwaterheating": "no",
                "airconditioning": "yes",
                "parking": 2,
                "prefarea": "yes",
                "furnishingstatus": "furnished"
            }
        }

class InvestmentInput(BaseModel):
    """Input for investment analysis"""
    purchase_price: float = Field(..., gt=0)
    down_payment_percent: float = Field(20, ge=0, le=100)
    loan_interest_rate: float = Field(7.5, ge=0, le=30)
    loan_term_years: int = Field(30, ge=1, le=40)
    monthly_rental_income: float = Field(..., ge=0)
    annual_property_tax: float = Field(..., ge=0)
    annual_insurance: float = Field(..., ge=0)
    annual_maintenance: float = Field(..., ge=0)
    vacancy_rate: float = Field(5, ge=0, le=100)
    annual_appreciation_rate: float = Field(3, ge=-10, le=20)
    holding_period_years: int = Field(10, ge=1, le=50)
    
    class Config:
        schema_extra = {
            "example": {
                "purchase_price": 5000000,
                "down_payment_percent": 20,
                "loan_interest_rate": 7.5,
                "loan_term_years": 30,
                "monthly_rental_income": 35000,
                "annual_property_tax": 50000,
                "annual_insurance": 25000,
                "annual_maintenance": 30000,
                "vacancy_rate": 5,
                "annual_appreciation_rate": 5,
                "holding_period_years": 10
            }
        }

class PredictionResponse(BaseModel):
    predicted_price: float
    price_per_sqft: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    model_used: str
    prediction_date: str
    
class InvestmentAnalysisResponse(BaseModel):
    roi: float
    rental_yield: float
    cap_rate: float
    cash_flow_monthly: float
    cash_flow_annual: float
    total_return: float
    appreciation_value: float
    total_rental_income: float
    total_expenses: float
    net_profit: float
    investment_grade: str
    recommendation: str
    
class ExplainabilityResponse(BaseModel):
    shap_values: Dict[str, float]
    feature_importance: Dict[str, float]
    explanation_text: str
    top_features: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    
class ChatResponse(BaseModel):
    response: str
    context_used: bool

class ModelStatus(BaseModel):
    models_loaded: bool
    preprocessor_loaded: bool
    analytics_available: bool
    explainability_available: bool
    chatbot_available: bool
    model_info: Optional[Dict[str, Any]] = None
    last_loaded: Optional[str] = None
    error_message: Optional[str] = None

# ============================================================================
# Model Manager with Graceful Loading
# ============================================================================

class ModelManager:
    """Manages all ML models and components with graceful degradation"""
    
    def __init__(self):
        self.preprocessor = None
        self.models = None
        self.analytics = None
        self.explainability = None
        self.chatbot = None
        self.metadata = None
        self.models_loaded = False
        self.last_loaded = None
        self.load_error = None
        
        # Configuration
        self.allow_startup_without_models = os.getenv(
            'ALLOW_STARTUP_WITHOUT_MODELS', 
            'true'
        ).lower() == 'true'
        
        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.gcs_model_path = os.getenv('GCS_MODEL_PATH', 'models/latest')
        self.local_model_path = os.getenv('LOCAL_MODEL_PATH', 'models/saved_models')
    
    def download_from_gcs(self) -> bool:
        """Download models from GCS"""
        try:
            if not self.bucket_name:
                logger.warning("GCS_BUCKET_NAME not set, skipping GCS download")
                return False
            
            logger.info(f"Downloading models from gs://{self.bucket_name}/{self.gcs_model_path}")
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.bucket_name)
            
            os.makedirs(self.local_model_path, exist_ok=True)
            
            blobs = list(bucket.list_blobs(prefix=self.gcs_model_path))
            
            if not blobs:
                logger.warning(f"No files found in gs://{self.bucket_name}/{self.gcs_model_path}")
                return False
            
            downloaded_count = 0
            for blob in blobs:
                if not blob.name.endswith('/'):
                    filename = os.path.basename(blob.name)
                    local_file = os.path.join(self.local_model_path, filename)
                    blob.download_to_filename(local_file)
                    logger.info(f"✓ Downloaded {filename}")
                    downloaded_count += 1
            
            logger.info(f"Successfully downloaded {downloaded_count} files from GCS")
            return downloaded_count > 0
            
        except Exception as e:
            logger.error(f"Error downloading from GCS: {e}", exc_info=True)
            return False
    
    def load_all_models(self) -> bool:
        """Load all models and components"""
        try:
            logger.info("=" * 60)
            logger.info("Starting model loading process...")
            logger.info("=" * 60)
            
            # Try to download from GCS if configured
            if self.bucket_name:
                gcs_success = self.download_from_gcs()
                if not gcs_success:
                    logger.warning("GCS download failed or returned no files")
            
            # Check if local models exist
            if not os.path.exists(self.local_model_path):
                raise FileNotFoundError(f"Model path not found: {self.local_model_path}")
            
            # Check for required files
            required_files = ['preprocessor.pkl', 'metadata.json']
            missing_files = [
                f for f in required_files 
                if not os.path.exists(os.path.join(self.local_model_path, f))
            ]
            
            if missing_files:
                raise FileNotFoundError(f"Missing required files: {missing_files}")
            
            # Load preprocessor
            logger.info("Loading preprocessor...")
            self.preprocessor = joblib.load(
                os.path.join(self.local_model_path, 'preprocessor.pkl')
            )
            logger.info("✓ Preprocessor loaded")
            
            # Load predictive models
            logger.info("Loading ML models...")
            self.models = RealEstatePredictiveModels()
            self.models.load_models(self.local_model_path)
            logger.info("✓ ML models loaded")
            
            # Initialize analytics
            logger.info("Initializing analytics...")
            self.analytics = InvestmentAnalytics()
            logger.info("✓ Analytics initialized")
            
            # Load metadata
            with open(os.path.join(self.local_model_path, 'metadata.json'), 'r') as f:
                self.metadata = json.load(f)
            logger.info("✓ Metadata loaded")
            
            # Initialize explainability
            logger.info("Initializing explainability...")
            self.explainability = ModelExplainability(
                model=self.models.models[self.models.best_model_name],
                preprocessor=self.preprocessor
            )
            logger.info("✓ Explainability initialized")
            
            # Initialize chatbot
            logger.info("Initializing chatbot...")
            groq_api_key = os.getenv('GROQ_API_KEY')
            if groq_api_key:
                self.chatbot = RealEstateInvestmentChatbot(api_key=groq_api_key)
                logger.info("✓ Chatbot initialized")
            else:
                logger.warning("⚠ Groq API key not found, chatbot disabled")
            
            # Mark as successfully loaded
            self.models_loaded = True
            self.last_loaded = datetime.utcnow().isoformat()
            self.load_error = None
            
            logger.info("=" * 60)
            logger.info("✅ All models loaded successfully!")
            logger.info(f"Best model: {self.metadata['best_model']}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.load_error = str(e)
            logger.error("=" * 60)
            logger.error(f"❌ Error loading models: {e}")
            logger.error("=" * 60)
            
            if self.allow_startup_without_models:
                logger.warning("⚠ Continuing without models (ALLOW_STARTUP_WITHOUT_MODELS=true)")
                logger.warning("⚠ API will be available but predictions will fail")
                logger.warning("⚠ Upload models and call POST /admin/reload to activate")
                return False
            else:
                logger.error("❌ ALLOW_STARTUP_WITHOUT_MODELS=false, startup will fail")
                raise
    
    def reload_models(self) -> bool:
        """Reload models from GCS"""
        logger.info("Reloading models...")
        
        # Reset state
        self.preprocessor = None
        self.models = None
        self.analytics = None
        self.explainability = None
        self.models_loaded = False
        
        # Attempt reload
        return self.load_all_models()
    
    def is_ready(self) -> bool:
        """Check if models are loaded and ready"""
        return self.models_loaded and self.models is not None
    
    def get_status(self) -> ModelStatus:
        """Get current status of model loader"""
        return ModelStatus(
            models_loaded=self.models_loaded,
            preprocessor_loaded=self.preprocessor is not None,
            analytics_available=self.analytics is not None,
            explainability_available=self.explainability is not None,
            chatbot_available=self.chatbot is not None,
            model_info={
                "best_model": self.metadata.get('best_model') if self.metadata else None,
                "trained_at": self.metadata.get('trained_at') if self.metadata else None,
            } if self.metadata else None,
            last_loaded=self.last_loaded,
            error_message=self.load_error
        )

# Initialize model manager
logger.info("Initializing Model Manager...")
model_manager = ModelManager()

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    status = model_manager.get_status()
    return {
        "message": "Real Estate Investment Advisor API",
        "version": "1.0.0",
        "status": "running",
        "models_ready": status.models_loaded,
        "endpoints": {
            "prediction": "/predict",
            "investment": "/analyze",
            "explanation": "/explain",
            "chat": "/chat",
            "model_info": "/models/info",
            "model_status": "/models/status",
            "health": "/health",
            "ready": "/ready",
            "reload": "/admin/reload"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint - always returns healthy if API is running"""
    status = model_manager.get_status()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models_status": status.dict()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check - only ready when models are loaded"""
    if not model_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "message": "Models not loaded yet. Check /models/status for details.",
                "error": model_manager.load_error
            }
        )
    return {
        "status": "ready",
        "models_loaded": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/models/status", response_model=ModelStatus)
async def model_status():
    """Get detailed model status"""
    return model_manager.get_status()

@app.get("/models/info")
async def model_info():
    """Get model information and metrics"""
    if not model_manager.metadata:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Upload models and call POST /admin/reload"
        )
    
    return {
        "best_model": model_manager.metadata['best_model'],
        "trained_at": model_manager.metadata['trained_at'],
        "all_models": list(model_manager.metadata['results'].keys()),
        "model_metrics": model_manager.metadata['results'],
        "feature_names": model_manager.metadata.get('feature_names', [])
    }

@app.post("/admin/reload")
async def reload_models():
    """Reload models from GCS (admin endpoint)"""
    logger.info("Reload request received")
    
    try:
        success = model_manager.reload_models()
        
        if success:
            return {
                "status": "success",
                "message": "Models reloaded successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "model_info": {
                    "best_model": model_manager.metadata.get('best_model'),
                    "trained_at": model_manager.metadata.get('trained_at')
                }
            }
        else:
            return {
                "status": "partial_success",
                "message": "Reload attempted but models not available",
                "error": model_manager.load_error,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload models: {str(e)}"
        )

@app.post("/predict", response_model=PredictionResponse)
async def predict_price(property_input: PropertyInput):
    """Predict property price"""
    if not model_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Models not available. Please wait or contact administrator."
        )
    
    try:
        # Convert input to DataFrame
        input_data = property_input.dict()
        df = pd.DataFrame([input_data])
        
        # Preprocess
        df_processed = model_manager.preprocessor.process_housing_data(df)
        
        # Remove target if present
        if 'price' in df_processed.columns:
            df_processed = df_processed.drop(columns=['price'])
        
        # Scale features
        X = model_manager.preprocessor.scaler.transform(df_processed)
        
        # Predict
        prediction = model_manager.models.predict(X)[0]
        price_per_sqft = prediction / property_input.area
        
        # Calculate confidence interval (simple approach)
        std_dev = prediction * 0.1
        
        return PredictionResponse(
            predicted_price=float(prediction),
            price_per_sqft=float(price_per_sqft),
            confidence_interval_lower=float(prediction - 1.96 * std_dev),
            confidence_interval_upper=float(prediction + 1.96 * std_dev),
            model_used=model_manager.metadata['best_model'],
            prediction_date=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=InvestmentAnalysisResponse)
async def analyze_investment(investment_input: InvestmentInput):
    """Perform comprehensive investment analysis"""
    if not model_manager.analytics:
        raise HTTPException(
            status_code=503,
            detail="Analytics not available. Models may not be loaded."
        )
    
    try:
        # Prepare data
        analysis_data = investment_input.dict()
        
        # Perform analysis
        result = model_manager.analytics.comprehensive_analysis(analysis_data)
        recommendation = model_manager.analytics.investment_recommendation(result)
        
        return InvestmentAnalysisResponse(
            roi=result['roi'],
            rental_yield=result['rental_yield'],
            cap_rate=result['cap_rate'],
            cash_flow_monthly=result['monthly_cash_flow'],
            cash_flow_annual=result['annual_cash_flow'],
            total_return=result['total_return'],
            appreciation_value=result['appreciation_value'],
            total_rental_income=result['total_rental_income'],
            total_expenses=result['total_expenses'],
            net_profit=result['net_profit'],
            investment_grade=recommendation['grade'],
            recommendation=recommendation['recommendation']
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain", response_model=ExplainabilityResponse)
async def explain_prediction(property_input: PropertyInput):
    """Explain prediction using SHAP/LIME"""
    if not model_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Explainability not available. Models may not be loaded."
        )
    
    try:
        # Convert input to DataFrame and preprocess
        input_data = property_input.dict()
        df = pd.DataFrame([input_data])
        df_processed = model_manager.preprocessor.process_housing_data(df)
        
        if 'price' in df_processed.columns:
            df_processed = df_processed.drop(columns=['price'])
        
        X = model_manager.preprocessor.scaler.transform(df_processed)
        
        # Get SHAP explanation
        shap_explanation = model_manager.explainability.explain_prediction_shap(X[0])
        
        # Get feature importance
        importance = model_manager.explainability.get_global_feature_importance(X)
        
        # Generate explanation text
        explanation_text = model_manager.explainability.generate_explanation_text(
            shap_explanation, 
            df_processed.columns.tolist()
        )
        
        # Get top features
        top_features = [
            {"feature": feat, "importance": float(imp)}
            for feat, imp in list(importance.items())[:5]
        ]
        
        return ExplainabilityResponse(
            shap_values=shap_explanation,
            feature_importance=importance,
            explanation_text=explanation_text,
            top_features=top_features
        )
        
    except Exception as e:
        logger.error(f"Explanation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Chat with AI assistant"""
    if not model_manager.chatbot:
        raise HTTPException(
            status_code=503, 
            detail="Chatbot service not available. Groq API key not configured."
        )
    
    try:
        # Set context if provided
        if chat_request.context:
            model_manager.chatbot.set_property_context(
                chat_request.context.get('property', {}),
                chat_request.context.get('analysis', {})
            )
        
        # Get response
        response = model_manager.chatbot.chat(chat_request.message)
        
        return ChatResponse(
            response=response,
            context_used=chat_request.context is not None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/reset")
async def reset_chat():
    """Reset chat conversation"""
    try:
        if model_manager.chatbot:
            model_manager.chatbot.reset_conversation()
        return {"status": "success", "message": "Conversation reset"}
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Startup & Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("=" * 60)
    logger.info("🚀 Real Estate Investment Advisor API Starting...")
    logger.info("=" * 60)
    
    # Attempt to load models
    success = model_manager.load_all_models()
    
    if success:
        logger.info("✅ API started successfully with models loaded")
        logger.info(f"Best model: {model_manager.metadata['best_model']}")
    else:
        logger.warning("⚠️ API started but models are not available")
        logger.warning("Upload models to GCS and call POST /admin/reload")
    
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks"""
    logger.info("API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)