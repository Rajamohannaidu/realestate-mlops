#!/bin/bash

# ============================================================================
# DEPLOY BACKEND ONLY - ML API Deployment Script
# ============================================================================
# PURPOSE: Deploy or update just the backend without touching frontend
# USAGE: ./scripts/deploy_backend.sh
# USE WHEN: You changed ML models, API, or analytics code
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_SERVICE="realestate-backend"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/${BACKEND_SERVICE}"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Backend Deployment (ML API)           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check project ID
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo -e "${YELLOW}Error: Set GCP_PROJECT_ID environment variable${NC}"
    exit 1
fi

echo -e "${BLUE}▶ Step 1:${NC} Building Backend Docker Image"
cd backend
docker build -f Dockerfile.backend -t $BACKEND_IMAGE:latest .
echo -e "${GREEN}✓ Backend image built${NC}"

echo -e "\n${BLUE}▶ Step 2:${NC} Pushing to Container Registry"
docker push $BACKEND_IMAGE:latest
echo -e "${GREEN}✓ Image pushed to GCR${NC}"

echo -e "\n${BLUE}▶ Step 3:${NC} Deploying to Cloud Run"
gcloud run deploy $BACKEND_SERVICE \
    --image=$BACKEND_IMAGE:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=20 \
    --min-instances=2 \
    --set-env-vars="GCS_BUCKET_NAME=${PROJECT_ID}-ml-models,GCS_MODEL_PATH=models/latest" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --project=$PROJECT_ID

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

echo -e "\n${BLUE}▶ Step 4:${NC} Updating Frontend with New Backend URL"
gcloud run services update realestate-frontend \
    --region=$REGION \
    --update-env-vars="BACKEND_API_URL=${BACKEND_URL}" \
    --project=$PROJECT_ID \
    --quiet 2>/dev/null || echo -e "${YELLOW}⚠ Frontend not deployed yet${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Backend Deployment Complete!      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backend URL:${NC} $BACKEND_URL"
echo -e "${BLUE}API Docs:${NC} $BACKEND_URL/docs"
echo ""
echo -e "Test it: ${BLUE}curl $BACKEND_URL/health${NC}"