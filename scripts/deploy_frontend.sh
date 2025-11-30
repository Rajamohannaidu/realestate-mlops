#!/bin/bash

# ============================================================================
# DEPLOY FRONTEND ONLY - Streamlit UI Deployment Script
# ============================================================================
# PURPOSE: Deploy or update just the frontend without touching backend
# USAGE: ./scripts/deploy_frontend.sh
# USE WHEN: You changed only UI code (streamlit_app.py)
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
FRONTEND_SERVICE="realestate-frontend"
FRONTEND_IMAGE="gcr.io/${PROJECT_ID}/${FRONTEND_SERVICE}"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Frontend Deployment (Streamlit UI)   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check project ID
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo -e "${YELLOW}Error: Set GCP_PROJECT_ID environment variable${NC}"
    exit 1
fi

echo -e "${BLUE}▶ Step 1:${NC} Building Frontend Docker Image"
cd frontend
docker build -f Dockerfile.frontend -t $FRONTEND_IMAGE:latest .
echo -e "${GREEN}✓ Frontend image built${NC}"

echo -e "\n${BLUE}▶ Step 2:${NC} Pushing to Container Registry"
docker push $FRONTEND_IMAGE:latest
echo -e "${GREEN}✓ Image pushed to GCR${NC}"

echo -e "\n${BLUE}▶ Step 3:${NC} Getting Backend URL"
BACKEND_URL=$(gcloud run services describe realestate-backend \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo -e "${YELLOW}⚠ Backend not found. Using localhost${NC}"
    BACKEND_URL="http://localhost:8080"
fi
echo -e "${GREEN}✓ Backend URL: $BACKEND_URL${NC}"

echo -e "\n${BLUE}▶ Step 4:${NC} Deploying to Cloud Run"
gcloud run deploy $FRONTEND_SERVICE \
    --image=$FRONTEND_IMAGE:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --max-instances=10 \
    --min-instances=1 \
    --set-env-vars="BACKEND_API_URL=${BACKEND_URL}" \
    --project=$PROJECT_ID

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Frontend Deployment Complete!     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Frontend URL:${NC} $FRONTEND_URL"
echo ""
echo -e "Test it: ${BLUE}curl $FRONTEND_URL${NC}"