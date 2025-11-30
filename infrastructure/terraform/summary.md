# 🎯 Terraform Infrastructure - Complete Package

## 📦 What You Have

### 5 Terraform Files (700+ lines total)

1. **`main.tf`** (700+ lines) - Complete infrastructure
2. **`variables.tf`** (200+ lines) - All configuration variables
3. **`outputs.tf`** (250+ lines) - Deployment information
4. **`terraform.tfvars.example`** - Configuration template
5. **`README.md`** - Complete Terraform guide

### 1 Deployment Script

6. **`deploy_with_terraform.sh`** - Automated deployment

---

## 🏗️ Infrastructure Created

### ✅ Cloud Run Services (2)

**Frontend (Streamlit UI)**
```hcl
Service: realestate-frontend
Region: us-central1
Memory: 2Gi
CPU: 2000m
Instances: 1-10 (auto-scaling)
Port: 8501
Health: /_stcore/health
```

**Backend (FastAPI ML)**
```hcl
Service: realestate-backend
Region: us-central1
Memory: 4Gi
CPU: 2000m
Instances: 2-20 (auto-scaling)
Port: 8080
Health: /health
Timeout: 300s
```

### ✅ Storage Buckets (4)

1. **ML Models** - `${project_id}-ml-models`
   - Purpose: Store all 7 trained ML models
   - Versioning: Enabled (keeps last 5 versions)
   - Access: Backend service account (read)

2. **Training Data** - `${project_id}-training-data`
   - Purpose: Housing.csv and datasets
   - Lifecycle: 90 days retention
   - Access: Training service account (read)

3. **Reports** - `${project_id}-reports`
   - Purpose: User-generated reports
   - Lifecycle: 30 days retention
   - Access: Frontend service account (read/write)

4. **Explainability** - `${project_id}-explainability`
   - Purpose: SHAP/LIME artifacts
   - Access: Backend service account (read/write)

### ✅ Service Accounts (3)

1. **Frontend SA** - `realestate-frontend@project.iam.gserviceaccount.com`
   - Permissions: Write logs, read/write reports

2. **Backend SA** - `realestate-backend@project.iam.gserviceaccount.com`
   - Permissions: Read models, write logs, access secrets, read/write explainability

3. **Training SA** - `realestate-training@project.iam.gserviceaccount.com`
   - Permissions: Write models, read training data, use Vertex AI

### ✅ Secrets (2)

1. **Groq API Key** - `groq-api-key`
   - For: AI Chatbot (LangChain + Groq)

2. **LangChain API Key** - `langchain-api-key`
   - For: LangChain features (optional)

### ✅ Automation (1)

**Cloud Scheduler Job**
- Name: `model-retraining-weekly`
- Schedule: Every Sunday at 2 AM
- Action: Trigger model retraining
- Timezone: America/New_York

### ✅ Monitoring

- Cloud Logging: Enabled
- Cloud Monitoring: Enabled
- Health Checks: Startup + Liveness probes
- Auto-scaling: Based on CPU/Concurrency

---

## 🚀 Deployment Options

### Option 1: Automated Script (Easiest)

```bash
# One command does everything
./scripts/deploy_with_terraform.sh
```

**What it does:**
1. ✅ Checks prerequisites
2. ✅ Creates state bucket
3. ✅ Configures Terraform
4. ✅ Initializes Terraform
5. ✅ Plans infrastructure
6. ✅ Applies changes
7. ✅ Builds Docker images
8. ✅ Updates services
9. ✅ Uploads models
10. ✅ Configures secrets

**Time:** 15-20 minutes

---

### Option 2: Manual Terraform (More Control)

```bash
# 1. Setup
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values

# 2. Initialize
terraform init

# 3. Plan
terraform plan

# 4. Deploy
terraform apply

# 5. View outputs
terraform output
```

**Time:** 10-15 minutes (infrastructure only)

---

## ⚙️ Configuration

### Quick Config (`terraform.tfvars`)

**Minimal (Required):**
```hcl
project_id = "your-actual-project-id"  # CHANGE THIS!
region     = "us-central1"
```

**Development:**
```hcl
project_id             = "realestate-dev"
environment           = "dev"
frontend_min_instances = 0  # Cost saving
backend_min_instances  = 0  # Cost saving
frontend_max_instances = 3
backend_max_instances  = 5
```

**Production:**
```hcl
project_id             = "realestate-prod"
environment           = "production"
frontend_min_instances = 2
backend_min_instances  = 3
frontend_max_instances = 20
backend_max_instances  = 50
enable_iap            = true  # Security
```

---

## 📊 Key Features

### 1. **Auto-Scaling**
```hcl
# Frontend scales based on traffic
autoscaling.knative.dev/minScale = 1
autoscaling.knative.dev/maxScale = 10

# Backend scales for ML inference
autoscaling.knative.dev/minScale = 2
autoscaling.knative.dev/maxScale = 20
```

### 2. **Health Checks**
```hcl
# Startup probe (initial readiness)
startup_probe {
  http_get { path = "/health" }
  initial_delay_seconds = 10
  failure_threshold     = 3
}

# Liveness probe (ongoing health)
liveness_probe {
  http_get { path = "/health" }
  period_seconds = 60
}
```

### 3. **Resource Limits**
```hcl
# Frontend
resources {
  limits = {
    cpu    = "2000m"  # 2 CPUs
    memory = "2Gi"    # 2GB RAM
  }
}

# Backend (needs more for ML)
resources {
  limits = {
    cpu    = "2000m"  # 2 CPUs
    memory = "4Gi"    # 4GB RAM
  }
}
```

### 4. **Secret Management**
```hcl
# Secrets injected as environment variables
env {
  name = "GROQ_API_KEY"
  value_from {
    secret_key_ref {
      name = "groq-api-key"
      key  = "latest"
    }
  }
}
```

### 5. **IAM (Least Privilege)**
```hcl
# Backend only gets what it needs
- Read models bucket ✓
- Write logs ✓
- Access secrets ✓
- NO admin access ✗
```

---

## 💰 Cost Estimation

### Development (Scale to Zero)
```hcl
frontend_min_instances = 0
backend_min_instances  = 0
```
**Cost:** $10-30/month

### Production (Always On)
```hcl
frontend_min_instances = 2
backend_min_instances  = 3
```
**Cost:** $135-390/month

### High Traffic
```hcl
frontend_max_instances = 20
backend_max_instances  = 50
```
**Cost:** $500+/month (at max scale)

---

## 🎯 Common Operations

### View All Resources
```bash
cd infrastructure/terraform
terraform state list
```

### Update Configuration
```bash
# 1. Edit config
nano terraform.tfvars

# 2. Apply changes
terraform apply
```

### View Service URLs
```bash
terraform output frontend_url
terraform output backend_url
```

### Destroy Everything
```bash
terraform destroy
```

### Update Specific Resource
```bash
# Update only backend
terraform apply -target=google_cloud_run_service.backend
```

---

## 📋 Outputs Reference

After deployment, get useful info:

```bash
# Service URLs
terraform output frontend_url
# → https://realestate-frontend-xxx.run.app

terraform output backend_url
# → https://realestate-backend-xxx.run.app

terraform output backend_api_docs
# → https://realestate-backend-xxx.run.app/docs

# Storage
terraform output models_bucket
# → your-project-ml-models

# Quick commands
terraform output upload_models_command
# → gsutil -m cp -r models/* gs://your-project-ml-models/...

# Complete summary
terraform output deployment_summary
# → JSON with all deployment info
```

---

## ✅ Verification Steps

After deployment:

```bash
cd infrastructure/terraform

# 1. Check services are running
terraform output frontend_url
terraform output backend_url

# 2. Test frontend
curl $(terraform output -raw frontend_url)

# 3. Test backend health
curl $(terraform output -raw backend_url)/health

# 4. View all outputs
terraform output

# 5. Check storage
gsutil ls

# 6. Check service accounts
gcloud iam service-accounts list
```

---

## 🔧 Customization

### Change Scaling Limits

**Edit `terraform.tfvars`:**
```hcl
backend_max_instances = 30  # Increase from 20
```

**Apply:**
```bash
terraform apply
```

### Add Custom Domain

**Add to `main.tf`:**
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

### Enable Private Access

**Edit `terraform.tfvars`:**
```hcl
enable_public_access = false
enable_iap          = true
```

---

## 🆚 Terraform vs Shell Scripts

| Feature | Terraform | Shell Scripts |
|---------|-----------|---------------|
| **Infrastructure** | ✅ Declarative | ❌ Imperative |
| **State Management** | ✅ Built-in | ❌ Manual |
| **Idempotent** | ✅ Yes | ⚠️ Partial |
| **Plan Changes** | ✅ Yes | ❌ No |
| **Destroy** | ✅ Easy | ❌ Manual |
| **Team Collaboration** | ✅ State locking | ⚠️ Difficult |
| **Learning Curve** | ⚠️ Medium | ✅ Easy |

**Recommendation:**
- Use **Terraform** for infrastructure
- Use **Scripts** for application deployment

---

## 🎓 Learning Path

1. **Start:** Run deployment script
2. **Understand:** Read main.tf comments
3. **Experiment:** Change variables, apply
4. **Advanced:** Add custom resources
5. **Master:** Create reusable modules

---

## 📚 Resources

- [Terraform Main File](main.tf) - 700+ lines, fully documented
- [Variables File](variables.tf) - All configuration options
- [Outputs File](outputs.tf) - What you get after deployment
- [README](README.md) - Complete Terraform guide
- [Deployment Script](../scripts/deploy_with_terraform.sh) - Automated deployment

---

## 🎉 Summary

**You have complete Terraform infrastructure that creates:**

✅ 2 Cloud Run services (frontend + backend)  
✅ 4 GCS buckets (models, data, reports, explainability)  
✅ 3 Service accounts (frontend, backend, training)  
✅ 2 Secrets (Groq, LangChain)  
✅ IAM policies (least privilege)  
✅ Monitoring & logging  
✅ Auto-scaling (1-20 instances)  
✅ Health checks  
✅ Scheduled retraining  

**Total Lines of Code:** 1,150+  
**Files:** 6 (5 Terraform + 1 script)  
**Deployment Time:** 15-20 minutes  
**Result:** Production-ready infrastructure! 🚀

---

**Deploy now:**
```bash
./scripts/deploy_with_terraform.sh
```

**Or explore first:**
```bash
cd infrastructure/terraform
cat README.md
```