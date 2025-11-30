# 🏗️ Terraform Infrastructure Guide

Complete Infrastructure-as-Code for Real Estate MLOps deployment on GCP.

---

## 📋 What This Creates

### Services
- ✅ **Frontend Service** - Streamlit UI on Cloud Run (1-10 instances)
- ✅ **Backend Service** - FastAPI ML API on Cloud Run (2-20 instances)

### Storage
- ✅ **ML Models Bucket** - Stores all 7 trained models
- ✅ **Training Data Bucket** - Houses Housing.csv and datasets
- ✅ **Reports Bucket** - User-generated reports
- ✅ **Explainability Bucket** - SHAP/LIME artifacts

### Security
- ✅ **Service Accounts** - 3 accounts (frontend, backend, training)
- ✅ **IAM Policies** - Least-privilege access
- ✅ **Secret Manager** - Groq & LangChain API keys

### Monitoring
- ✅ **Cloud Logging** - Automatic log aggregation
- ✅ **Cloud Monitoring** - Metrics and dashboards
- ✅ **Health Checks** - Startup and liveness probes

### Automation
- ✅ **Cloud Scheduler** - Weekly model retraining

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# or sudo apt install terraform  # Linux

# Authenticate to GCP
gcloud auth login
gcloud auth application-default login

# Set project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID
```

### 2. Configure

```bash
cd infrastructure/terraform

# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**Required changes in `terraform.tfvars`:**
```hcl
project_id = "your-actual-project-id"  # CHANGE THIS!
region     = "us-central1"
environment = "production"
```

### 3. Deploy

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply
```

Type `yes` when prompted.

**Deployment time:** 5-10 minutes

### 4. Verify

```bash
# View outputs
terraform output

# Access services
terraform output frontend_url
terraform output backend_url
```

---

## 📁 File Structure

```
infrastructure/terraform/
├── main.tf                      # Main infrastructure (700+ lines)
├── variables.tf                 # Variable definitions
├── outputs.tf                   # Output values
├── terraform.tfvars.example     # Example configuration
├── terraform.tfvars             # Your config (don't commit!)
└── README.md                    # This file
```

---

## ⚙️ Configuration

### Environment Variables

**Option 1: terraform.tfvars (Recommended)**
```hcl
project_id = "realestate-prod"
region     = "us-central1"
environment = "production"

frontend_min_instances = 1
frontend_max_instances = 10
backend_min_instances = 2
backend_max_instances = 20
```

**Option 2: Command Line**
```bash
terraform apply \
  -var="project_id=realestate-prod" \
  -var="region=us-central1" \
  -var="frontend_min_instances=1"
```

**Option 3: Environment Variables**
```bash
export TF_VAR_project_id="realestate-prod"
export TF_VAR_region="us-central1"
terraform apply
```

### Environment-Specific Configs

**Development:**
```hcl
environment            = "dev"
frontend_min_instances = 0  # Scale to zero
backend_min_instances  = 0  # Scale to zero
frontend_max_instances = 3
backend_max_instances  = 5
enable_scheduled_training = false
```

**Staging:**
```hcl
environment            = "staging"
frontend_min_instances = 1
backend_min_instances  = 1
frontend_max_instances = 5
backend_max_instances  = 10
```

**Production:**
```hcl
environment            = "production"
frontend_min_instances = 2
backend_min_instances  = 3
frontend_max_instances = 20
backend_max_instances  = 50
enable_iap            = true
```

---

## 📊 Key Configuration Options

### Frontend (Streamlit)

```hcl
frontend_min_instances = 1        # Keep 1+ for production
frontend_max_instances = 10       # Scale based on users
frontend_memory        = "2Gi"    # Memory per instance
frontend_cpu          = "2000m"   # 2 CPUs per instance
```

**Calculation:**
- Each instance handles ~80 concurrent users
- 10 instances = 800 concurrent users max

### Backend (FastAPI + ML)

```hcl
backend_min_instances = 2         # Keep warm for fast response
backend_max_instances = 20        # Scale for ML inference
backend_memory        = "4Gi"     # ML models need memory
backend_cpu          = "2000m"    # 2 CPUs per instance
backend_timeout      = 300        # 5 min for predictions
```

**Calculation:**
- Each instance handles ~50 requests/min
- 20 instances = 1000 requests/min max

### Storage Lifecycle

```hcl
models_bucket_lifecycle_days     = 90  # Keep 3 months
training_data_lifecycle_days    = 90  # Keep 3 months
reports_lifecycle_days          = 30  # Keep 1 month
```

---

## 🔧 Common Operations

### View Current State

```bash
# List all resources
terraform state list

# Show specific resource
terraform state show google_cloud_run_service.backend

# View outputs
terraform output
terraform output -json
```

### Update Configuration

```bash
# 1. Edit terraform.tfvars
nano terraform.tfvars

# 2. Preview changes
terraform plan

# 3. Apply changes
terraform apply
```

### Update Specific Resource

```bash
# Update backend instances
terraform apply \
  -var="backend_min_instances=5" \
  -target=google_cloud_run_service.backend
```

### Destroy Infrastructure

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy everything
terraform destroy

# Destroy specific resource
terraform destroy -target=google_cloud_run_service.frontend
```

---

## 🎯 Common Scenarios

### Scenario 1: Increase Scaling Limits

**Problem:** Getting 503 errors under load

**Solution:**
```hcl
# terraform.tfvars
backend_max_instances = 30  # Increase from 20
```

```bash
terraform apply
```

### Scenario 2: Reduce Costs

**Problem:** Monthly bill is too high

**Solution:**
```hcl
# terraform.tfvars
frontend_min_instances = 0  # Scale to zero
backend_min_instances  = 0  # Scale to zero
```

```bash
terraform apply
```

### Scenario 3: Update Service

**Problem:** Need to deploy new code

**Solution:**
```bash
# Terraform manages infrastructure, not code
# Use these instead:
./scripts/deploy_backend.sh
./scripts/deploy_frontend.sh
```

### Scenario 4: Change Region

**Problem:** Want to deploy in different region

**Solution:**
```hcl
# terraform.tfvars
region = "europe-west1"  # Change region
```

```bash
terraform apply
```

### Scenario 5: Enable Private Access

**Problem:** Don't want public access

**Solution:**
```hcl
# terraform.tfvars
enable_public_access = false
enable_iap          = true
```

```bash
terraform apply
```

---

## 📊 Outputs Reference

After deployment, Terraform provides useful outputs:

```bash
# Service URLs
terraform output frontend_url
terraform output backend_url
terraform output backend_api_docs

# Storage buckets
terraform output models_bucket
terraform output training_data_bucket

# Quick commands
terraform output upload_models_command
terraform output view_backend_logs_command

# Complete summary
terraform output deployment_summary
terraform output -json > deployment.json
```

---

## 🔒 State Management

### Remote State (Recommended)

**Initial setup:**
```bash
# Create state bucket
gsutil mb -l us-central1 gs://${GCP_PROJECT_ID}-terraform-state

# Enable versioning
gsutil versioning set on gs://${GCP_PROJECT_ID}-terraform-state
```

**Update main.tf:**
```hcl
terraform {
  backend "gcs" {
    bucket = "your-project-id-terraform-state"
    prefix = "terraform/state"
  }
}
```

**Initialize:**
```bash
terraform init
```

### State Commands

```bash
# Show state
terraform show

# List resources
terraform state list

# Pull state
terraform state pull

# Backup state
terraform state pull > backup.tfstate
```

---

## 💰 Cost Estimation

### Development (~$20-50/month)
```hcl
frontend_min_instances = 0
backend_min_instances  = 0
frontend_max_instances = 3
backend_max_instances  = 5
```

**Breakdown:**
- Cloud Run: $10-30 (pay per use)
- Storage: $1-5
- Logging: $0-5 (free tier)
- Monitoring: $0 (free tier)

### Production (~$135-390/month)
```hcl
frontend_min_instances = 2
backend_min_instances  = 3
frontend_max_instances = 20
backend_max_instances  = 50
```

**Breakdown:**
- Cloud Run Frontend: $30-80
- Cloud Run Backend: $100-300
- Storage: $2-5
- Logging: $2-5
- Monitoring: $0

### High Traffic (~$500+/month)
Maximum instances running constantly

---

## 🐛 Troubleshooting

### Issue: "Backend configuration changed"

```bash
# Re-initialize
terraform init -reconfigure
```

### Issue: "Resource already exists"

```bash
# Import existing resource
terraform import google_storage_bucket.ml_models your-bucket-name

# Or remove from state
terraform state rm google_storage_bucket.ml_models
```

### Issue: "Permission denied"

```bash
# Check authentication
gcloud auth application-default login

# Verify permissions
gcloud projects get-iam-policy $GCP_PROJECT_ID
```

### Issue: "Service not ready"

```bash
# Wait for APIs to be enabled
sleep 60

# Retry
terraform apply
```

### Issue: "Quota exceeded"

```bash
# Check quotas
gcloud compute project-info describe

# Request increase
# Visit: https://console.cloud.google.com/iam-admin/quotas
```

---

## 📚 Advanced Topics

### Custom Domains

```hcl
resource "google_cloud_run_domain_mapping" "frontend" {
  location = var.region
  name     = "www.yourdomain.com"
  
  metadata {
    namespace = var.project_id
  }
  
  spec {
    route_name = google_cloud_run_service.frontend.name
  }
}
```

### Load Balancer

```hcl
resource "google_compute_global_address" "default" {
  name = "realestate-lb-ip"
}

resource "google_compute_global_forwarding_rule" "default" {
  name       = "realestate-lb"
  target     = google_compute_target_https_proxy.default.id
  port_range = "443"
  ip_address = google_compute_global_address.default.address
}
```

### VPC Connector

```hcl
resource "google_vpc_access_connector" "connector" {
  name          = "realestate-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = "default"
}
```

---

## 📖 Best Practices

### 1. **Use Workspaces for Environments**

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new production

# Switch workspace
terraform workspace select production

# Deploy
terraform apply
```

### 2. **Use Modules**

```hcl
# Reusable module
module "ml_service" {
  source = "./modules/ml_service"
  
  service_name = "realestate-backend"
  min_instances = 2
  max_instances = 20
}
```

### 3. **Use Data Sources**

```hcl
data "google_container_registry_image" "backend" {
  name = "realestate-backend"
}

resource "google_cloud_run_service" "backend" {
  template {
    spec {
      containers {
        image = data.google_container_registry_image.backend.image_url
      }
    }
  }
}
```

### 4. **Use Variables**

```hcl
variable "services" {
  type = map(object({
    min_instances = number
    max_instances = number
    memory       = string
  }))
}

# Loop over services
for_each = var.services
```

---

## 🎓 Learning Resources

- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Terraform Examples](https://cloud.google.com/run/docs/deploying)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [GCP Terraform Samples](https://github.com/terraform-google-modules)

---

## 📞 Support

**Issues?**
- Check [Troubleshooting](#troubleshooting) section
- View Terraform docs: `terraform --help`
- Check GCP status: https://status.cloud.google.com

**Questions?**
- Open an issue in GitHub
- Contact: your-email@example.com

---

**Built with Terraform for reliable, reproducible infrastructure! 🏗️**