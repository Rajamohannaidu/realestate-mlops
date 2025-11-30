# ============================================================================
# TERRAFORM TFVARS EXAMPLE - Configuration Values
# ============================================================================
# PURPOSE: Example configuration file with actual values
# USAGE: 
#   1. Copy this file: cp terraform.tfvars.example terraform.tfvars
#   2. Update with your actual values
#   3. Never commit terraform.tfvars to git!
# ============================================================================

# === REQUIRED: GCP Project Configuration ===
project_id = "academic-atlas-475811-c5"  # CHANGE THIS!
region     = "us-central1"
environment = "production"

# === Frontend Configuration (Streamlit) ===
frontend_min_instances = 1    # 0 for dev (cost saving), 1+ for production
frontend_max_instances = 10   # Maximum concurrent users / 80
frontend_memory        = "2Gi"
frontend_cpu          = "2000m"

# === Backend Configuration (FastAPI + ML) ===
backend_min_instances = 2     # Keep 2+ for production (warm instances)
backend_max_instances = 20    # Scale based on expected load
backend_memory        = "4Gi" # ML models need memory
backend_cpu          = "2000m"
backend_timeout      = 300    # 5 minutes for ML inference

# === Storage Lifecycle ===
models_bucket_lifecycle_days       = 90  # Keep 3 months of model versions
training_data_lifecycle_days      = 90  # Keep 3 months of training data
reports_lifecycle_days            = 30  # Keep 1 month of user reports

# === Monitoring ===
enable_monitoring    = true
enable_logging      = true
log_retention_days  = 30

# === Security ===
enable_public_access = true   # Set false for private deployment
enable_iap          = false   # Set true to enable Identity-Aware Proxy

# === Training ===
enable_scheduled_training = true
training_schedule        = "0 2 * * 0"  # Sunday 2 AM
training_timezone        = "America/New_York"

# === Cost Optimization ===
enable_cpu_throttling    = false  # Keep false for ML workloads
enable_startup_cpu_boost = true   # Faster cold starts

# === Labels ===
common_labels = {
  project     = "realestate-mlops"
  managed_by  = "terraform"
  team        = "ml-engineering"
  cost_center = "engineering"
}

# ============================================================================
# ENVIRONMENT-SPECIFIC EXAMPLES
# ============================================================================

# --- Development Environment ---
# project_id             = "realestate-dev"
# environment           = "dev"
# frontend_min_instances = 0    # Cost saving: scale to zero
# backend_min_instances  = 0    # Cost saving: scale to zero
# frontend_max_instances = 3
# backend_max_instances  = 5
# enable_scheduled_training = false

# --- Staging Environment ---
# project_id             = "realestate-staging"
# environment           = "staging"
# frontend_min_instances = 1
# backend_min_instances  = 1
# frontend_max_instances = 5
# backend_max_instances  = 10

# --- Production Environment ---
# project_id             = "realestate-prod"
# environment           = "production"
# frontend_min_instances = 2
# backend_min_instances  = 3
# frontend_max_instances = 20
# backend_max_instances  = 50
# enable_iap            = true  # Enable for security