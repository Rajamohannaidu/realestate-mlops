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
# Pydantic Models (Pydantic v1 syntax)
# ============================================================================

class PropertyInput(BaseModel):
    """Input for price prediction"""
    area: float = Field(..., gt=0, description="Area in square feet")
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    stories: int = Field(..., ge=1)
    mainroad: str
    guestroom: str
    basement: str
    hotwaterheating: str
    airconditioning: str
    parking: int = Field(..., ge=0)
    prefarea: str
    furnishingstatus: str

    @validator(
        "mainroad", "guestroom", "basement",
        "hotwaterheating", "airconditioning", "prefarea"
    )
    def validate_yes_no(cls, v):
        if v.lower() not in ["yes", "no"]:
            raise ValueError('Must be "yes" or "no"')
        return v.lower()

    @validator("furnishingstatus")
    def validate_furnishing(cls, v):
        valid = ["furnished", "semi-furnished", "unfurnished"]
        if v.lower() not in valid:
            raise ValueError(f"Must be one of {valid}")
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

        self.allow_startup_without_models = os.getenv(
            'ALLOW_STARTUP_WITHOUT_MODELS', 
            'false'
        ).lower() == 'true'

        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.gcs_model_path = os.getenv('GCS_MODEL_PATH', 'models/latest')
        self.local_model_path = os.getenv('LOCAL_MODEL_PATH', '/app/models/saved_models')

    def download_from_gcs(self) -> bool:
        """Download models from GCS bucket"""
        try:
            if not self.bucket_name:
                logger.warning("GCS_BUCKET_NAME not set, skipping GCS download")
                return False

            logger.info(f"📥 Downloading models from gs://{self.bucket_name}/{self.gcs_model_path}")
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.bucket_name)

            os.makedirs(self.local_model_path, exist_ok=True)

            blobs = list(bucket.list_blobs(prefix=self.gcs_model_path))

            if not blobs:
                logger.warning(f"❌ No model files found in gs://{self.bucket_name}/{self.gcs_model_path}")
                return False

            downloaded_count = 0
            for blob in blobs:
                if not blob.name.endswith('/'):
                    local_file = os.path.join(self.local_model_path, os.path.basename(blob.name))
                    blob.download_to_filename(local_file)
                    logger.info(f"✅ Downloaded: {blob.name} → {local_file}")
                    downloaded_count += 1

            logger.info(f"📦 Downloaded {downloaded_count} files from GCS")
            return downloaded_count > 0

        except Exception as e:
            logger.error(f"❌ Error downloading from GCS: {e}", exc_info=True)
            return False

    def load_all_models(self) -> bool:
        """Load all models and components"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 STARTING MODEL LOADING SEQUENCE")
            logger.info("=" * 60)

            # Step 1: Try to download from GCS if bucket is configured
            if self.bucket_name:
                logger.info(f"Step 1: Attempting GCS download from bucket '{self.bucket_name}'")
                self.download_from_gcs()
            else:
                logger.warning("Step 1: Skipped (GCS_BUCKET_NAME not configured)")

            # Step 2: Check if local models exist
            logger.info(f"Step 2: Checking local model path: {self.local_model_path}")
            if not os.path.exists(self.local_model_path):
                logger.error(f"❌ Model path does not exist: {self.local_model_path}")
                if not self.allow_startup_without_models:
                    raise FileNotFoundError(f"Model path not found: {self.local_model_path}")
                return False

            # Step 3: List available files
            available_files = os.listdir(self.local_model_path)
            logger.info(f"📂 Available files in {self.local_model_path}: {available_files}")

            # Step 4: Check for required files
            logger.info("Step 3: Checking for required files")
            required_files = ["preprocessor.pkl", "metadata.json"]
            missing_files = []
            for f in required_files:
                path = os.path.join(self.local_model_path, f)
                if not os.path.exists(path):
                    missing_files.append(f)
                    logger.warning(f"⚠️  Missing: {f}")
                else:
                    logger.info(f"✅ Found: {f}")

            if missing_files:
                logger.error(f"❌ Missing required files: {missing_files}")
                if not self.allow_startup_without_models:
                    raise FileNotFoundError(f"Missing required files: {missing_files}")
                return False

            # Step 5: Load preprocessor
            logger.info("Step 4: Loading preprocessor...")
            preprocessor_path = os.path.join(self.local_model_path, "preprocessor.pkl")
            self.preprocessor = joblib.load(preprocessor_path)
            logger.info(f"✅ Preprocessor loaded: {preprocessor_path}")

            # Step 6: Load predictive models
            logger.info("Step 5: Loading predictive models...")
            self.models = RealEstatePredictiveModels()
            self.models.load_models(self.local_model_path)
            logger.info(f"✅ Models loaded: {self.models.best_model_name}")

            # Step 7: Load metadata
            logger.info("Step 6: Loading metadata...")
            metadata_path = os.path.join(self.local_model_path, "metadata.json")
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
            logger.info(f"✅ Metadata loaded: {self.metadata.get('best_model', 'unknown')}")

            # Step 8: Initialize analytics
            logger.info("Step 7: Initializing analytics...")
            self.analytics = InvestmentAnalytics()
            logger.info("✅ Analytics initialized")

            # Step 9: Initialize explainability
            logger.info("Step 8: Initializing explainability...")
            self.explainability = ModelExplainability(
                model=self.models.models[self.models.best_model_name],
                preprocessor=self.preprocessor
            )
            logger.info("✅ Explainability initialized")

            # Step 10: Initialize chatbot (optional)
            logger.info("Step 9: Initializing chatbot...")
            groq_api_key = os.getenv("GROQ_API_KEY")
            if groq_api_key:
                self.chatbot = RealEstateInvestmentChatbot(api_key=groq_api_key)
                logger.info("✅ Chatbot initialized")
            else:
                logger.warning("⚠️  GROQ_API_KEY not set, chatbot will be unavailable")

            # Mark as ready
            self.models_loaded = True
            self.last_loaded = datetime.utcnow().isoformat()
            self.load_error = None

            logger.info("=" * 60)
            logger.info("✅ ALL MODELS LOADED SUCCESSFULLY!")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ ERROR DURING MODEL LOADING: {e}", exc_info=True)
            logger.error("=" * 60)
            self.load_error = str(e)
            self.models_loaded = False

            if self.allow_startup_without_models:
                logger.warning("⚠️  ALLOW_STARTUP_WITHOUT_MODELS=true, continuing without models")
                return False
            else:
                logger.error("🚨 ALLOW_STARTUP_WITHOUT_MODELS=false, aborting startup")
                raise

    def reload_models(self):
        """Reload all models"""
        logger.info("🔄 Reloading models...")
        self.preprocessor = None
        self.models = None
        self.metadata = None
        self.explainability = None
        self.chatbot = None
        self.analytics = None
        self.models_loaded = False
        return self.load_all_models()

    def is_ready(self):
        """Check if models are ready"""
        return self.models_loaded

    def get_status(self):
        """Get current model status"""
        return ModelStatus(
            models_loaded=self.models_loaded,
            preprocessor_loaded=self.preprocessor is not None,
            analytics_available=self.analytics is not None,
            explainability_available=self.explainability is not None,
            chatbot_available=self.chatbot is not None,
            model_info=self.metadata,
            last_loaded=self.last_loaded,
            error_message=self.load_error
        )


logger.info("🔧 Initializing Model Manager...")
model_manager = ModelManager()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    status = model_manager.get_status()
    return {
        "message": "Real Estate Investment Advisor API",
        "version": "1.0.0",
        "models_ready": status.models_loaded
    }


@app.get("/health")
async def health_check():
    """Liveness probe - app is running"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/ready")
async def readiness_check():
    """Readiness probe - models are loaded and ready"""
    if not model_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail=f"Models not loaded: {model_manager.load_error}"
        )
    return {"status": "ready"}


@app.get("/models/status", response_model=ModelStatus)
async def model_status():
    """Get detailed model loading status"""
    return model_manager.get_status()


@app.post("/admin/reload")
async def reload():
    """Manually reload all models"""
    ok = model_manager.reload_models()
    return {"success": ok, "error": model_manager.load_error}


@app.post("/predict", response_model=PredictionResponse)
async def predict_price(property_input: PropertyInput):
    if not model_manager.is_ready():
        raise HTTPException(status_code=503, detail="Models not loaded")

    try:
        df = pd.DataFrame([property_input.dict()])
        df_processed = model_manager.preprocessor.process_housing_data(df)

        if "price" in df_processed.columns:
            df_processed = df_processed.drop(columns=["price"])

        X = model_manager.preprocessor.scaler.transform(df_processed)
        prediction = model_manager.models.predict(X)[0]

        price_per_sqft = prediction / property_input.area
        std_dev = prediction * 0.1

        return PredictionResponse(
            predicted_price=float(prediction),
            price_per_sqft=float(price_per_sqft),
            confidence_interval_lower=float(prediction - 1.96 * std_dev),
            confidence_interval_upper=float(prediction + 1.96 * std_dev),
            model_used=model_manager.metadata["best_model"],
            prediction_date=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=InvestmentAnalysisResponse)
async def analyze_investment(data: InvestmentInput):
    if not model_manager.analytics:
        raise HTTPException(status_code=503, detail="Analytics unavailable")

    try:
        result = model_manager.analytics.comprehensive_analysis(data.dict())
        recommendation = model_manager.analytics.investment_recommendation(result)

        return InvestmentAnalysisResponse(
            roi=result["roi"],
            rental_yield=result["rental_yield"],
            cap_rate=result["cap_rate"],
            cash_flow_monthly=result["monthly_cash_flow"],
            cash_flow_annual=result["annual_cash_flow"],
            total_return=result["total_return"],
            appreciation_value=result["appreciation_value"],
            total_rental_income=result["total_rental_income"],
            total_expenses=result["total_expenses"],
            net_profit=result["net_profit"],
            investment_grade=recommendation["grade"],
            recommendation=recommendation["recommendation"]
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain", response_model=ExplainabilityResponse)
async def explain_prediction(property_input: PropertyInput):
    if not model_manager.is_ready():
        raise HTTPException(status_code=503, detail="Models not loaded")

    try:
        df = pd.DataFrame([property_input.dict()])
        df_processed = model_manager.preprocessor.process_housing_data(df)

        if "price" in df_processed.columns:
            df_processed = df_processed.drop(columns=["price"])

        X = model_manager.preprocessor.scaler.transform(df_processed)

        shap_vals = model_manager.explainability.explain_prediction_shap(X[0])
        importance = model_manager.explainability.get_global_feature_importance(X)
        explanation_text = model_manager.explainability.generate_explanation_text(
            shap_vals, df_processed.columns.tolist()
        )

        top_features = [
            {"feature": feat, "importance": float(imp)}
            for feat, imp in list(importance.items())[:5]
        ]

        return ExplainabilityResponse(
            shap_values=shap_vals,
            feature_importance=importance,
            explanation_text=explanation_text,
            top_features=top_features
        )
    except Exception as e:
        logger.error(f"Explain error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not model_manager.chatbot:
        raise HTTPException(status_code=503, detail="Chatbot unavailable")

    try:
        if req.context:
            model_manager.chatbot.set_property_context(
                req.context.get("property", {}),
                req.context.get("analysis", {})
            )
        response = model_manager.chatbot.chat(req.message)
        return ChatResponse(response=response, context_used=req.context is not None)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/reset")
async def reset_chat():
    if model_manager.chatbot:
        model_manager.chatbot.reset_conversation()
    return {"status": "success"}


# ============================================================================
# Application Lifecycle
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Real Estate Investment Advisor API...")
    try:
        ok = model_manager.load_all_models()
        if ok:
            logger.info("✅ API ready with models loaded")
        else:
            logger.warning("⚠️  API started without models")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)