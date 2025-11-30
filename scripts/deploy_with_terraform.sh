#!/bin/bash

# ============================================================================
# TERRAFORM DEPLOYMENT SCRIPT - Deploy with Infrastructure as Code
# ============================================================================
# PURPOSE: Deploy complete infrastructure using Terraform
# USAGE: ./scripts/deploy_with_terraform.sh
# INCLUDES: Complete infrastructure + services deployment
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
TERRAFORM_DIR="infrastructure/terraform"

echo -e "${PURPLE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Real Estate MLOps - Terraform Deployment             ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Project ID:${NC} $PROJECT_ID"
echo -e "${BLUE}Region:${NC} $REGION"
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

# Check Terraform
if ! command -v terraform &> /dev/null; then
    print_error "Terraform not found. Install it first:"
    echo "  macOS: brew install terraform"
    echo "  Linux: sudo apt install terraform"
    exit 1
fi
print_success "Terraform found: $(terraform version | head -1)"

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Please install it first."
    exit 1
fi
print_success "gcloud CLI found"

# Check project ID
if [ "$PROJECT_ID" = "your-project-id" ]; then
    print_error "Please set GCP_PROJECT_ID environment variable"
    echo "  export GCP_PROJECT_ID='your-actual-project-id'"
    exit 1
fi
print_success "Project ID configured"

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_warning "Not authenticated to GCP"
    echo "Authenticating..."
    gcloud auth login
    gcloud auth application-default login
fi
print_success "Authenticated to GCP"

# Set project
gcloud config set project $PROJECT_ID
print_success "Project set to $PROJECT_ID"

# ============================================================================
# Step 2: Setup Terraform State Bucket
# ============================================================================

print_step "Step 2: Setting Up Terraform State Bucket"

STATE_BUCKET="${PROJECT_ID}-terraform-state"

if gsutil ls -b gs://$STATE_BUCKET 2>/dev/null; then
    print_warning "State bucket already exists: $STATE_BUCKET"
else
    gsutil mb -l $REGION gs://$STATE_BUCKET
    gsutil versioning set on gs://$STATE_BUCKET
    print_success "Created state bucket: $STATE_BUCKET"
fi

# ============================================================================
# Step 3: Configure Terraform
# ============================================================================

print_step "Step 3: Configuring Terraform"

cd $TERRAFORM_DIR

# Check if terraform.tfvars exists
if [ ! -f terraform.tfvars ]; then
    print_warning "terraform.tfvars not found. Creating from example..."
    
    if [ -f terraform.tfvars.example ]; then
        cp terraform.tfvars.example terraform.tfvars
        
        # Update project_id in terraform.tfvars
        sed -i.bak "s/your-actual-gcp-project-id/${PROJECT_ID}/g" terraform.tfvars
        sed -i.bak "s/us-central1/${REGION}/g" terraform.tfvars
        rm -f terraform.tfvars.bak
        
        print_success "Created terraform.tfvars"
        print_warning "Please review terraform.tfvars and update if needed"
        
        # Pause for user review
        read -p "Press Enter to continue after reviewing terraform.tfvars..."
    else
        print_error "terraform.tfvars.example not found"
        exit 1
    fi
else
    print_success "terraform.tfvars found"
fi

# Update backend configuration in main.tf
print_step "Updating backend configuration..."
sed -i.bak "s/REPLACE_WITH_YOUR_PROJECT_ID/${PROJECT_ID}/g" main.tf
rm -f main.tf.bak
print_success "Backend configuration updated"

# ============================================================================
# Step 4: Initialize Terraform
# ============================================================================

print_step "Step 4: Initializing Terraform"

terraform init

print_success "Terraform initialized"

# ============================================================================
# Step 5: Validate Configuration
# ============================================================================

print_step "Step 5: Validating Configuration"

terraform validate

print_success "Configuration is valid"

# ============================================================================
# Step 6: Plan Infrastructure
# ============================================================================

print_step "Step 6: Planning Infrastructure Changes"

echo ""
echo -e "${YELLOW}This will show you what will be created...${NC}"
echo ""

terraform plan -out=tfplan

print_success "Plan created"

# ============================================================================
# Step 7: Confirm Deployment
# ============================================================================

print_step "Step 7: Confirm Deployment"

echo ""
echo -e "${YELLOW}Review the plan above carefully.${NC}"
echo -e "${YELLOW}This will create:${NC}"
echo "  - 2 Cloud Run services (frontend + backend)"
echo "  - 4 GCS buckets"
echo "  - 3 Service accounts"
echo "  - IAM policies"
echo "  - Secrets"
echo "  - Monitoring"
echo ""

read -p "Do you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_warning "Deployment cancelled"
    rm -f tfplan
    exit 0
fi

# ============================================================================
# Step 8: Apply Infrastructure
# ============================================================================

print_step "Step 8: Applying Infrastructure"

terraform apply tfplan

rm -f tfplan

print_success "Infrastructure deployed!"

# ============================================================================
# Step 9: Build and Push Docker Images
# ============================================================================

print_step "Step 9: Building and Pushing Docker Images"

cd ../../  # Back to project root

# Configure Docker for GCR
gcloud auth configure-docker

# Build Backend
print_step "Building backend image..."
cd backend
docker build -f Dockerfile.backend -t gcr.io/${PROJECT_ID}/realestate-backend:latest .
docker push gcr.io/${PROJECT_ID}/realestate-backend:latest
print_success "Backend image pushed"
cd ..

# Build Frontend
print_step "Building frontend image..."
cd frontend
docker build -f Dockerfile.frontend -t gcr.io/${PROJECT_ID}/realestate-frontend:latest .
docker push gcr.io/${PROJECT_ID}/realestate-frontend:latest
print_success "Frontend image pushed"
cd ..

# ============================================================================
# Step 10: Update Services with New Images
# ============================================================================

print_step "Step 10: Updating Services with New Images"

# Update backend
gcloud run services update realestate-backend \
    --image=gcr.io/${PROJECT_ID}/realestate-backend:latest \
    --region=$REGION \
    --quiet

print_success "Backend service updated"

# Update frontend  
gcloud run services update realestate-frontend \
    --image=gcr.io/${PROJECT_ID}/realestate-frontend:latest \
    --region=$REGION \
    --quiet

print_success "Frontend service updated"

# ============================================================================
# Step 11: Upload Models (if exist)
# ============================================================================

print_step "Step 11: Uploading Models to GCS"

if [ -d "backend/models/saved_models" ]; then
    gsutil -m cp -r backend/models/saved_models/* \
        gs://${PROJECT_ID}-ml-models/models/latest/
    print_success "Models uploaded"
else
    print_warning "No models found. Run training first:"
    echo "  python backend/src/training/train_gcp.py"
fi

# ============================================================================
# Step 12: Add Secrets
# ============================================================================

print_step "Step 12: Configuring Secrets"

if [ ! -z "$GROQ_API_KEY" ]; then
    echo $GROQ_API_KEY | gcloud secrets versions add groq-api-key \
        --data-file=- \
        --project=$PROJECT_ID
    print_success "Groq API key added to Secret Manager"
else
    print_warning "GROQ_API_KEY not set. Chatbot will be disabled."
    echo "  Set it: export GROQ_API_KEY='your-key'"
fi

# ============================================================================
# Step 13: Get Deployment Info
# ============================================================================

print_step "Step 13: Getting Deployment Information"

cd $TERRAFORM_DIR

FRONTEND_URL=$(terraform output -raw frontend_url)
BACKEND_URL=$(terraform output -raw backend_url)
MODELS_BUCKET=$(terraform output -raw models_bucket)

# ============================================================================
# Deployment Complete
# ============================================================================

echo ""
echo -e "${PURPLE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║          🎉 Deployment Complete! 🎉                   ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service URLs:${NC}"
echo -e "  ${BLUE}Frontend:${NC} $FRONTEND_URL"
echo -e "  ${BLUE}Backend:${NC} $BACKEND_URL"
echo -e "  ${BLUE}API Docs:${NC} ${BACKEND_URL}/docs"
echo ""
echo -e "${GREEN}Storage:${NC}"
echo -e "  ${BLUE}Models:${NC} gs://${MODELS_BUCKET}"
echo ""
echo -e "${GREEN}Terraform Commands:${NC}"
echo -e "  ${BLUE}View outputs:${NC} cd ${TERRAFORM_DIR} && terraform output"
echo -e "  ${BLUE}Show state:${NC} cd ${TERRAFORM_DIR} && terraform show"
echo -e "  ${BLUE}Update:${NC} cd ${TERRAFORM_DIR} && terraform apply"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Visit ${BLUE}${FRONTEND_URL}${NC}"
echo -e "  2. Train models: ${BLUE}./scripts/train_models.sh${NC}"
echo -e "  3. Monitor: ${BLUE}gcloud run services logs read realestate-backend --region=${REGION}${NC}"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo -e "  - Set GROQ_API_KEY for chatbot: ${BLUE}export GROQ_API_KEY='your-key'${NC}"
echo -e "  - Upload models: ${BLUE}gsutil cp -r models/* gs://${MODELS_BUCKET}/models/latest/${NC}"
echo ""