# Complete MLOps Architecture - Real Estate Investment Advisor AI on GCP

## 🏗️ GCP Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Cloud Load Balancer                           │
│                    (Global HTTP(S) Load Balancer)                    │
└────────────────┬────────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────────┐
│  Cloud Run    │  │   Cloud Run      │
│  (Streamlit   │  │   (FastAPI       │
│   Frontend)   │  │   Backend API)   │
└───────┬───────┘  └────────┬─────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────┴──────────────────────────────────┐
        │                                             │
        ▼                                             ▼
┌──────────────────┐                      ┌──────────────────────┐
│  Cloud Storage   │                      │   Vertex AI          │
│  (GCS)           │                      │   (Training)         │
│  - Models        │                      │   - Model Training   │
│  - Data          │                      │   - Pipelines        │
│  - Reports       │                      │   - Experiments      │
└──────────────────┘                      └──────────────────────┘
        │                                             │
        └─────────────────┬───────────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌──────────────────┐              ┌──────────────────────┐
│  Cloud Logging   │              │  Cloud Monitoring    │
│  - App Logs      │              │  - Metrics           │
│  - Predictions   │              │  - Dashboards        │
│  - Errors        │              │  - Alerts            │
└──────────────────┘              └──────────────────────┘
        │                                     │
        └─────────────────┬───────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Secret Manager  │
                │  - API Keys      │
                │  - Groq API      │
                │  - LangChain     │
                └──────────────────┘
```

## 📦 Component Breakdown

### **Frontend Service (Cloud Run #1)**
- **Image**: Streamlit application
- **Purpose**: Web UI for users
- **Scaling**: 1-10 instances
- **Memory**: 2Gi
- **CPU**: 2

### **Backend API (Cloud Run #2)**
- **Image**: FastAPI application
- **Purpose**: ML predictions & analytics
- **Scaling**: 1-20 instances
- **Memory**: 4Gi
- **CPU**: 2

### **Storage (GCS)**
- **Bucket 1**: ML models (all 7 models)
- **Bucket 2**: Training data
- **Bucket 3**: User reports/exports
- **Bucket 4**: SHAP/LIME artifacts

### **Training (Vertex AI)**
- **Pipelines**: Automated retraining
- **Experiments**: Track model versions
- **Model Registry**: Version control

### **Monitoring**
- **Cloud Logging**: All logs
- **Cloud Monitoring**: Metrics & alerts
- **Error Reporting**: Crash analysis

---

## 🎯 Deployment Strategy

### **1. Dual Service Architecture**

**Why Two Services?**
- ✅ **Separation of concerns**: UI vs API
- ✅ **Independent scaling**: Frontend scales differently than ML backend
- ✅ **Better performance**: Dedicated resources
- ✅ **Cost optimization**: Scale each independently

**Service 1: Streamlit Frontend**
```yaml
Purpose: User interface
Port: 8501
URL: https://realestate-frontend-xxx.run.app
Endpoints:
  - / (Home)
  - /prediction
  - /analysis
  - /insights
  - /chat
  - /dashboard
```

**Service 2: FastAPI Backend**
```yaml
Purpose: ML API
Port: 8080
URL: https://realestate-api-xxx.run.app
Endpoints:
  - /predict
  - /analyze
  - /explain
  - /health
  - /models/info
```

---

## 📁 Updated Project Structure

```
realestate-mlops/
├── frontend/                          # Streamlit Frontend
│   ├── app/
│   │   └── streamlit_app.py          # Your 1000+ line app
│   ├── Dockerfile.frontend
│   ├── requirements.frontend.txt
│   └── .streamlit/
│       └── config.toml
│
├── backend/                           # FastAPI Backend
│   ├── src/
│   │   ├── api/
│   │   │   └── main.py               # FastAPI app
│   │   └── training/
│   │       ├── data_preprocessing.py # Your existing
│   │       ├── predictive_models.py  # Your existing
│   │       ├── investment_analytics.py
│   │       ├── explainability.py
│   │       └── train_gcp.py
│   ├── Dockerfile.backend
│   └── requirements.backend.txt
│
├── chatbot/                           # Optional: Separate chatbot service
│   ├── src/
│   │   └── chatbot.py                # Your LangChain chatbot
│   ├── Dockerfile.chatbot
│   └── requirements.chatbot.txt
│
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf                   # All GCP resources
│   │   ├── frontend.tf               # Frontend service
│   │   ├── backend.tf                # Backend service
│   │   ├── storage.tf                # GCS buckets
│   │   ├── vertex.tf                 # Vertex AI
│   │   └── monitoring.tf             # Monitoring setup
│   │
│   ├── cloudbuild/
│   │   ├── frontend.yaml             # Frontend CI/CD
│   │   ├── backend.yaml              # Backend CI/CD
│   │   └── training.yaml             # Model training pipeline
│   │
│   └── kubernetes/                   # Optional: GKE deployment
│       ├── frontend-deployment.yaml
│       └── backend-deployment.yaml
│
├── pipelines/
│   ├── vertex_training_pipeline.py   # Automated training
│   └── data_pipeline.py              # Data processing
│
├── monitoring/
│   ├── dashboards/
│   │   ├── app_dashboard.json
│   │   └── ml_dashboard.json
│   └── alerts/
│       ├── error_alerts.yaml
│       └── performance_alerts.yaml
│
├── scripts/
│   ├── deploy_all.sh                 # Deploy everything
│   ├── deploy_frontend.sh
│   ├── deploy_backend.sh
│   ├── train_models.sh
│   └── setup_monitoring.sh
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .github/
│   └── workflows/
│       ├── deploy-frontend.yml
│       ├── deploy-backend.yml
│       └── train-models.yml
│
├── docker-compose.yml                # Local development
├── Makefile                          # Common commands
└── README.md
```

---

## 🎨 Service Communication

### Frontend ↔ Backend Communication

```python
# frontend/app/streamlit_app.py

import requests
import os

BACKEND_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8080')

# Call backend API for predictions
def get_prediction(property_data):
    response = requests.post(
        f"{BACKEND_URL}/predict",
        json=property_data
    )
    return response.json()

# Call backend for analysis
def get_analysis(analysis_params):
    response = requests.post(
        f"{BACKEND_URL}/analyze",
        json=analysis_params
    )
    return response.json()

# Call backend for explanations
def get_explanation(prediction_data):
    response = requests.post(
        f"{BACKEND_URL}/explain",
        json=prediction_data
    )
    return response.json()
```

---

## 🚀 Deployment Files

### 1. Frontend Dockerfile

```dockerfile
# frontend/Dockerfile.frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.frontend.txt .
RUN pip install --no-cache-dir -r requirements.frontend.txt

# Copy application
COPY app/ ./app/
COPY .streamlit/ ./.streamlit/

# Set environment
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PORT=8501

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
```

### 2. Backend Dockerfile

```dockerfile
# backend/Dockerfile.backend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.backend.txt .
RUN pip install --no-cache-dir -r requirements.backend.txt

# Copy application
COPY src/ ./src/
COPY models/ ./models/

# Create directories
RUN mkdir -p models/saved_models models/explainability

# Set environment
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "4"]
```

### 3. Requirements Files

```txt
# frontend/requirements.frontend.txt
streamlit==1.35.0
plotly==5.22.0
pandas==2.2.2
numpy==1.26.4
requests==2.31.0
python-dotenv==1.0.0
```

```txt
# backend/requirements.backend.txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==1.10.13
typing-extensions==4.11.0

# Your existing ML/AI stack
numpy==1.26.4
tensorflow==2.16.1
pandas==2.2.2
scikit-learn==1.5.0
xgboost==2.0.3
lightgbm==4.3.0
shap==0.45.1
lime==0.2.0.1

# Chatbot (optional in backend)
langchain==0.1.0
langchain-groq==0.0.1
langchain-community==0.0.13

# GCP
google-cloud-storage==2.14.0
google-cloud-logging==3.9.0
google-cloud-aiplatform==1.42.1

# Utils
joblib==1.4.2
scipy==1.13.1
matplotlib==3.8.4
seaborn==0.12.2
```

---

## 🔧 Complete Terraform Configuration

```hcl
# infrastructure/terraform/main.tf

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "realestate-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "secretmanager.googleapis.com"
  ])
  
  service = each.key
  disable_on_destroy = false
}

# GCS Buckets
resource "google_storage_bucket" "models" {
  name     = "${var.project_id}-ml-models"
  location = var.region
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "data" {
  name     = "${var.project_id}-training-data"
  location = var.region
}

resource "google_storage_bucket" "reports" {
  name     = "${var.project_id}-reports"
  location = var.region
}

resource "google_storage_bucket" "explainability" {
  name     = "${var.project_id}-explainability"
  location = var.region
}

# Secret Manager for API Keys
resource "google_secret_manager_secret" "groq_api_key" {
  secret_id = "groq-api-key"
  
  replication {
    auto {}
  }
}

# Service Accounts
resource "google_service_account" "frontend" {
  account_id   = "realestate-frontend"
  display_name = "Real Estate Frontend Service"
}

resource "google_service_account" "backend" {
  account_id   = "realestate-backend"
  display_name = "Real Estate Backend Service"
}

# IAM for Backend (needs model access)
resource "google_storage_bucket_iam_member" "backend_models" {
  bucket = google_storage_bucket.models.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_secret" {
  secret_id = google_secret_manager_secret.groq_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# Frontend Cloud Run Service
resource "google_cloud_run_service" "frontend" {
  name     = "realestate-frontend"
  location = var.region
  
  template {
    spec {
      service_account_name = google_service_account.frontend.email
      
      containers {
        image = "gcr.io/${var.project_id}/realestate-frontend:latest"
        
        env {
          name  = "BACKEND_API_URL"
          value = google_cloud_run_service.backend.status[0].url
        }
        
        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }
        
        ports {
          container_port = 8501
        }
      }
      
      container_concurrency = 80
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "1"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Backend Cloud Run Service
resource "google_cloud_run_service" "backend" {
  name     = "realestate-backend"
  location = var.region
  
  template {
    spec {
      service_account_name = google_service_account.backend.email
      
      containers {
        image = "gcr.io/${var.project_id}/realestate-backend:latest"
        
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.models.name
        }
        
        env {
          name  = "GCS_MODEL_PATH"
          value = "models/latest"
        }
        
        env {
          name = "GROQ_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.groq_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = "2000m"
            memory = "4Gi"
          }
        }
        
        ports {
          container_port = 8080
        }
      }
      
      container_concurrency = 80
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "20"
        "autoscaling.knative.dev/minScale" = "2"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Public access (adjust as needed)
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "backend_public" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "frontend_url" {
  value = google_cloud_run_service.frontend.status[0].url
}

output "backend_url" {
  value = google_cloud_run_service.backend.status[0].url
}
```

---

This is Part 1 of the complete architecture. Shall I continue with:
- Part 2: Backend API implementation
- Part 3: Frontend adaptation
- Part 4: Training pipeline
- Part 5: Deployment scripts?