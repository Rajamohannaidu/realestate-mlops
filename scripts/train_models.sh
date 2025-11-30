#!/bin/bash

# ============================================================================
# TRAIN MODELS SCRIPT - Train All 7 ML Models & Upload to GCS
# ============================================================================
# PURPOSE: Train all models locally and upload to Google Cloud Storage
# USAGE: ./scripts/train_models.sh
# TRAINS: Linear, Ridge, Random Forest, Gradient Boosting, XGBoost, 
#         LightGBM, Neural Network (7 models total)
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
BUCKET_NAME="${PROJECT_ID}-ml-models"
DATA_PATH="${TRAINING_DATA:-data/Housing.csv}"

echo -e "${PURPLE}╔════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Real Estate Model Training Pipeline  ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if data exists
if [ ! -f "$DATA_PATH" ]; then
    echo -e "${YELLOW}⚠ Training data not found: $DATA_PATH${NC}"
    echo -e "${YELLOW}  Will create sample dataset${NC}"
fi

echo -e "${BLUE}▶ Step 1:${NC} Training All Models"
echo -e "  Models to train: ${GREEN}7${NC} (Linear, Ridge, RF, GB, XGB, LightGBM, NN)"
echo ""

# Run training script
python backend/src/training/train_gcp.py \
    --data "$DATA_PATH" \
    --gcs-bucket "$BUCKET_NAME" \
    --gcs-path "models/latest"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Training Pipeline Complete!      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Models Location:${NC}"
echo -e "  Local:  ${GREEN}models/saved_models/${NC}"
echo -e "  GCS:    ${GREEN}gs://${BUCKET_NAME}/models/latest/${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Deploy backend: ${YELLOW}./scripts/deploy_backend.sh${NC}"
echo -e "  2. Or deploy all:  ${YELLOW}./scripts/deploy_all.sh${NC}"