#!/bin/bash

# ============================================================================
# Real Estate Investment Advisor - Complete GCP Deployment
# ============================================================================
# Deploys both frontend (Streamlit) and backend (FastAPI) to Cloud Run
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Service Names
FRONTEND_SERVICE="realestate-frontend"
BACKEND_SERVICE="realestate-backend"

# Image Names
FRONTEND_IMAGE="gcr.io/${PROJECT_ID}/${FRONTEND_SERVICE}"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/${BACKEND_SERVICE}"

echo -e "${PURPLE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Real Estate Investment Advisor - GCP Deployment    ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Project ID:${NC} $PROJECT_ID"
echo -e "${BLUE}Region:${NC} $REGION"
echo -e "${BLUE}Environment:${NC} $ENVIRONMENT"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# ============================================================================
# Step 1: Prerequisites Check
# ============================================================================

print_step "Step 1: Checking Prerequisites"

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Please install it first."
    exit 1
fi
print_success "gcloud CLI found"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install it first."
    exit 1
fi
print_success "Docker found"

# Check project ID
if [ "$PROJECT_ID" = "your-project-id" ]; then
    print_error "Please set GCP_PROJECT_ID environment variable"
    exit 1
fi
print_success "Project ID configured"

# Set project
gcloud config set project $PROJECT_ID
print_success "Project set to $PROJECT_ID"

# ============================================================================
# Step 2: Enable Required APIs
# ============================================================================

print_step "Step 2: Enabling Required GCP APIs"

APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "storage.googleapis.com"
    "aiplatform.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
    "secretmanager.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

print_success "All APIs enabled"

# ============================================================================
# Step 3: Create GCS Buckets
# ============================================================================

print_step "Step 3: Creating GCS Buckets"

BUCKETS=(
    "${PROJECT_ID}-ml-models:ML Models"
    "${PROJECT_ID}-training-data:Training Data"
    "${PROJECT_ID}-reports:User Reports"
    "${PROJECT_ID}-explainability:SHAP/LIME Artifacts"
)

for bucket_info in "${BUCKETS[@]}"; do
    IFS=':' read -r bucket_name bucket_desc <<< "$bucket_info"
    
    if gsutil ls -b gs://$bucket_name 2>/dev/null; then
        print_warning "Bucket $bucket_name already exists"
    else
        gsutil mb -l $REGION gs://$bucket_name
        print_success "Created $bucket_name ($bucket_desc)"
    fi
done

# Enable versioning for models bucket
gsutil versioning set on gs://${PROJECT_ID}-ml-models
print_success "Versioning enabled for models bucket"

# ============================================================================
# Step 4: Setup Secret Manager
# ============================================================================

print_step "Step 4: Setting Up Secret Manager"

# Check if Groq API key is set
if [ -z "$GROQ_API_KEY" ]; then
    print_warning "GROQ_API_KEY not set. Chatbot will be disabled."
    print_warning "Set it with: export GROQ_API_KEY='your-key-here'"
else
    # Create or update secret
    if gcloud secrets describe groq-api-key --project=$PROJECT_ID &>/dev/null; then
        echo $GROQ_API_KEY | gcloud secrets versions add groq-api-key \
            --data-file=- \
            --project=$PROJECT_ID
        print_success "Groq API key secret updated"
    else
        echo $GROQ_API_KEY | gcloud secrets create groq-api-key \
            --data-file=- \
            --replication-policy="automatic" \
            --project=$PROJECT_ID
        print_success "Groq API key secret created"
    fi
fi

# ============================================================================
# Step 5: Create Service Accounts
# ============================================================================

print_step "Step 5: Creating Service Accounts"

# Frontend service account
FRONTEND_SA="realestate-frontend@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $FRONTEND_SA --project=$PROJECT_ID &>/dev/null; then
    print_warning "Frontend service account already exists"
else
    gcloud iam service-accounts create realestate-frontend \
        --display-name="Real Estate Frontend Service" \
        --project=$PROJECT_ID
    print_success "Frontend service account created"
fi

# Backend service account
BACKEND_SA="realestate-backend@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $BACKEND_SA --project=$PROJECT_ID &>/dev/null; then
    print_warning "Backend service account already exists"
else
    gcloud iam service-accounts create realestate-backend \
        --display-name="Real Estate Backend Service" \
        --project=$PROJECT_ID
    print_success "Backend service account created"
fi

# ============================================================================
# Step 6: Grant IAM Permissions
# ============================================================================

print_step "Step 6: Granting IAM Permissions"

# Backend needs access to models, secrets, and logging
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$BACKEND_SA" \
    --role="roles/storage.objectViewer" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$BACKEND_SA" \
    --role="roles/logging.logWriter" \
    --condition=None

if [ ! -z "$GROQ_API_KEY" ]; then
    gcloud secrets add-iam-policy-binding groq-api-key \
        --member="serviceAccount:$BACKEND_SA" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID
fi

print_success "IAM permissions granted"

# ============================================================================
# Step 7: Build Backend Docker Image
# ============================================================================

print_step "Step 7: Building Backend Docker Image"

cd backend
docker build -f Dockerfile.backend -t $BACKEND_IMAGE:latest .
docker tag $BACKEND_IMAGE:latest $BACKEND_IMAGE:$GITHUB_SHA

# Push to GCR
docker push $BACKEND_IMAGE:latest

print_success "Backend image built and pushed"
cd ..

# ============================================================================
# Step 8: Build Frontend Docker Image
# ============================================================================

print_step "Step 8: Building Frontend Docker Image"

cd frontend
docker build -f Dockerfile.frontend -t $FRONTEND_IMAGE:latest .
docker tag $FRONTEND_IMAGE:latest $FRONTEND_IMAGE:$GITHUB_SHA

# Push to GCR
docker push $FRONTEND_IMAGE:latest

print_success "Frontend image built and pushed"
cd ..

# ============================================================================
# Step 9: Deploy Backend to Cloud Run
# ============================================================================

print_step "Step 9: Deploying Backend to Cloud Run"

gcloud run deploy $BACKEND_SERVICE \
    --image=$BACKEND_IMAGE:latest \
    --platform=managed \
    --region=$REGION \
    --service-account=$BACKEND_SA \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=20 \
    --min-instances=2 \
    --set-env-vars="GCS_BUCKET_NAME=${PROJECT_ID}-ml-models,GCS_MODEL_PATH=models/latest,ENVIRONMENT=${ENVIRONMENT}" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --project=$PROJECT_ID

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

print_success "Backend deployed: $BACKEND_URL"

# ============================================================================
# Step 10: Deploy Frontend to Cloud Run
# ============================================================================

print_step "Step 10: Deploying Frontend to Cloud Run"

gcloud run deploy $FRONTEND_SERVICE \
    --image=$FRONTEND_IMAGE:latest \
    --platform=managed \
    --region=$REGION \
    --service-account=$FRONTEND_SA \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=1 \
    --set-env-vars="BACKEND_API_URL=${BACKEND_URL},ENVIRONMENT=${ENVIRONMENT}" \
    --project=$PROJECT_ID

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

print_success "Frontend deployed: $FRONTEND_URL"

# ============================================================================
# Step 11: Upload Models to GCS (if exist locally)
# ============================================================================

print_step "Step 11: Uploading Models to GCS"

if [ -d "models/saved_models" ]; then
    gsutil -m cp -r models/saved_models/* \
        gs://${PROJECT_ID}-ml-models/models/latest/
    print_success "Models uploaded to GCS"
else
    print_warning "No local models found. Run training pipeline first."
fi

# ============================================================================
# Step 12: Setup Monitoring
# ============================================================================

print_step "Step 12: Setting Up Monitoring"

# Create log-based metrics
gcloud logging metrics create prediction_requests \
    --description="Number of prediction requests" \
    --log-filter='resource.type="cloud_run_revision"
        resource.labels.service_name="'$BACKEND_SERVICE'"
        jsonPayload.endpoint="/predict"' \
    --project=$PROJECT_ID 2>/dev/null || print_warning "Metric already exists"

gcloud logging metrics create prediction_errors \
    --description="Number of prediction errors" \
    --log-filter='resource.type="cloud_run_revision"
        resource.labels.service_name="'$BACKEND_SERVICE'"
        severity="ERROR"' \
    --project=$PROJECT_ID 2>/dev/null || print_warning "Metric already exists"

print_success "Monitoring setup complete"

# ============================================================================
# Step 13: Run Smoke Tests
# ============================================================================

print_step "Step 13: Running Smoke Tests"

echo "Testing backend health..."
sleep 10  # Wait for service to be ready

if curl -f $BACKEND_URL/health > /dev/null 2>&1; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed"
fi

echo "Testing frontend..."
if curl -f $FRONTEND_URL > /dev/null 2>&1; then
    print_success "Frontend health check passed"
else
    print_error "Frontend health check failed"
fi

# ============================================================================
# Deployment Complete
# ============================================================================

echo ""
echo -e "${PURPLE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║          🎉 Deployment Complete! 🎉                 ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service URLs:${NC}"
echo -e "  ${BLUE}Frontend (Streamlit):${NC} $FRONTEND_URL"
echo -e "  ${BLUE}Backend (FastAPI):${NC} $BACKEND_URL"
echo ""
echo -e "${GREEN}GCS Buckets:${NC}"
echo -e "  ${BLUE}Models:${NC} gs://${PROJECT_ID}-ml-models"
echo -e "  ${BLUE}Data:${NC} gs://${PROJECT_ID}-training-data"
echo -e "  ${BLUE}Reports:${NC} gs://${PROJECT_ID}-reports"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Visit $FRONTEND_URL to use the application"
echo -e "  2. Check logs: ${BLUE}gcloud run services logs read $FRONTEND_SERVICE --region=$REGION${NC}"
echo -e "  3. Monitor: ${BLUE}https://console.cloud.google.com/run${NC}"
echo -e "  4. Train models: ${BLUE}./scripts/train_models.sh${NC}"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo -e "  - Set GROQ_API_KEY for chatbot functionality"
echo -e "  - Upload trained models to GCS before using predictions"
echo -e "  - Configure monitoring alerts in Cloud Console"
echo ""