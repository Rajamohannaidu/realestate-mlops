# ============================================================================
# TERRAFORM MAIN CONFIGURATION - Real Estate MLOps Infrastructure
# ============================================================================
# PURPOSE: Define complete GCP infrastructure for dual-service architecture
# CREATES: All resources needed for production deployment
# ARCHITECTURE: Frontend (Streamlit) + Backend (FastAPI) + Storage + Monitoring
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Store Terraform state in GCS bucket
  backend "gcs" {
    bucket = "academic-atlas-475811-c5-terraform-state"
    prefix = "terraform/state"
  }
}

# ============================================================================
# PROVIDERS
# ============================================================================

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ============================================================================
# DATA SOURCES
# ============================================================================

data "google_project" "project" {
  project_id = var.project_id
}

# ============================================================================
# ENABLE REQUIRED APIS
# ============================================================================

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",               # Cloud Run
    "cloudbuild.googleapis.com",        # Cloud Build
    "storage.googleapis.com",           # Cloud Storage
    "aiplatform.googleapis.com",        # Vertex AI
    "logging.googleapis.com",           # Cloud Logging
    "monitoring.googleapis.com",        # Cloud Monitoring
    "secretmanager.googleapis.com",     # Secret Manager
    "containerregistry.googleapis.com", # Container Registry
    "cloudscheduler.googleapis.com",    # Cloud Scheduler
    "compute.googleapis.com",           # Compute (for networking)
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy = false

  timeouts {
    create = "30m"
    update = "40m"
  }
}

# ============================================================================
# GOOGLE CLOUD STORAGE BUCKETS
# ============================================================================

# Bucket 1: ML Models Storage
resource "google_storage_bucket" "ml_models" {
  name     = "${var.project_id}-ml-models"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "ml-models"
    component   = "backend"
  }

  depends_on = [google_project_service.required_apis]
}

# Bucket 2: Training Data Storage
resource "google_storage_bucket" "training_data" {
  name     = "${var.project_id}-training-data"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90 # Delete data older than 90 days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "training-data"
    component   = "training"
  }

  depends_on = [google_project_service.required_apis]
}

# Bucket 3: Reports and Exports
resource "google_storage_bucket" "reports" {
  name     = "${var.project_id}-reports"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30 # Delete reports older than 30 days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "user-reports"
    component   = "frontend"
  }

  depends_on = [google_project_service.required_apis]
}

# Bucket 4: Explainability Artifacts (SHAP/LIME)
resource "google_storage_bucket" "explainability" {
  name     = "${var.project_id}-explainability"
  location = var.region

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    purpose     = "explainability"
    component   = "backend"
  }

  depends_on = [google_project_service.required_apis]
}

# ============================================================================
# SECRET MANAGER
# ============================================================================

# Secret for Groq API Key
resource "google_secret_manager_secret" "groq_api_key" {
  secret_id = "groq-api-key"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    purpose     = "chatbot"
  }

  depends_on = [google_project_service.required_apis]
}

# Note: The actual secret value must be added manually or via separate process
# gcloud secrets versions add groq-api-key --data-file=-

# Secret for LangChain API Key (optional)
resource "google_secret_manager_secret" "langchain_api_key" {
  secret_id = "langchain-api-key"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    purpose     = "chatbot"
  }

  depends_on = [google_project_service.required_apis]
}

# ============================================================================
# SERVICE ACCOUNTS
# ============================================================================

# Service Account for Frontend (Streamlit)
resource "google_service_account" "frontend" {
  account_id   = "realestate-frontend"
  display_name = "Real Estate Frontend Service Account"
  description  = "Service account for Streamlit frontend application"
}

# Service Account for Backend (FastAPI)
resource "google_service_account" "backend" {
  account_id   = "realestate-backend"
  display_name = "Real Estate Backend Service Account"
  description  = "Service account for FastAPI ML backend"
}

# Service Account for Training Jobs
resource "google_service_account" "training" {
  account_id   = "realestate-training"
  display_name = "Real Estate Training Service Account"
  description  = "Service account for model training jobs"
}

# ============================================================================
# IAM PERMISSIONS - Backend
# ============================================================================

# Backend: Read access to ML models bucket
resource "google_storage_bucket_iam_member" "backend_models_viewer" {
  bucket = google_storage_bucket.ml_models.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# Backend: Read/Write access to explainability bucket
resource "google_storage_bucket_iam_member" "backend_explainability_admin" {
  bucket = google_storage_bucket.explainability.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# Backend: Write logs
resource "google_project_iam_member" "backend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Backend: Access Groq API secret
resource "google_secret_manager_secret_iam_member" "backend_groq_secret" {
  secret_id = google_secret_manager_secret.groq_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# Backend: Access LangChain API secret
resource "google_secret_manager_secret_iam_member" "backend_langchain_secret" {
  secret_id = google_secret_manager_secret.langchain_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# ============================================================================
# IAM PERMISSIONS - Frontend
# ============================================================================

# Frontend: Read access to reports bucket
resource "google_storage_bucket_iam_member" "frontend_reports_admin" {
  bucket = google_storage_bucket.reports.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.frontend.email}"
}

# Frontend: Write logs
resource "google_project_iam_member" "frontend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

# ============================================================================
# IAM PERMISSIONS - Training
# ============================================================================

# Training: Full access to models bucket
resource "google_storage_bucket_iam_member" "training_models_admin" {
  bucket = google_storage_bucket.ml_models.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.training.email}"
}

# Training: Read access to training data bucket
resource "google_storage_bucket_iam_member" "training_data_viewer" {
  bucket = google_storage_bucket.training_data.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.training.email}"
}

# Training: Vertex AI user
resource "google_project_iam_member" "training_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.training.email}"
}

# Training: Write logs
resource "google_project_iam_member" "training_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.training.email}"
}
/*
# ============================================================================
# CLOUD RUN - BACKEND SERVICE (FastAPI)
# ============================================================================

resource "google_cloud_run_service" "backend" {
  name     = "realestate-backend"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.backend.email

      containers {
        image = "${var.artifact_registry_repo}/realestate-backend:latest"

        # Environment Variables
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.ml_models.name
        }

        env {
          name  = "GCS_MODEL_PATH"
          value = "models/latest"
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "LOG_LEVEL"
          value = "INFO"
        }

        # Secrets
        env {
          name = "GROQ_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.groq_api_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "LANGCHAIN_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.langchain_api_key.secret_id
              key  = "latest"
            }
          }
        }

        # Resource Limits
        resources {
          limits = {
            cpu    = "2000m"
            memory = "4Gi"
          }
        }

        # Port
        ports {
          name           = "http1"
          container_port = 8080
        }

        # Startup probe
        startup_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 10
          timeout_seconds       = 10
          period_seconds        = 10
          failure_threshold     = 3
        }

        # Liveness probe
        liveness_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 30
          timeout_seconds       = 10
          period_seconds        = 60
          failure_threshold     = 3
        }
      }

      container_concurrency = 80
      timeout_seconds       = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"     = var.backend_max_instances
        "autoscaling.knative.dev/minScale"     = var.backend_min_instances
        "run.googleapis.com/cpu-throttling"    = "false"
        "run.googleapis.com/startup-cpu-boost" = "true"
      }

      labels = {
        environment = var.environment
        component   = "backend"
        service     = "ml-api"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required_apis,
    google_service_account.backend
  ]
}

# ============================================================================
# CLOUD RUN - FRONTEND SERVICE (Streamlit)
# ============================================================================

resource "google_cloud_run_service" "frontend" {
  name     = "realestate-frontend"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.frontend.email

      containers {
        image = "${var.artifact_registry_repo}/realestate-frontend:latest"

        # Environment Variables
        env {
          name  = "BACKEND_API_URL"
          value = google_cloud_run_service.backend.status[0].url
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "LOG_LEVEL"
          value = "INFO"
        }

        # Resource Limits
        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }

        # Port
        ports {
          name           = "http1"
          container_port = 8501
        }

        # Startup probe
        startup_probe {
          http_get {
            path = "/_stcore/health"
            port = 8501
          }
          initial_delay_seconds = 10
          timeout_seconds       = 10
          period_seconds        = 10
          failure_threshold     = 3
        }

        # Liveness probe
        liveness_probe {
          http_get {
            path = "/_stcore/health"
            port = 8501
          }
          initial_delay_seconds = 30
          timeout_seconds       = 10
          period_seconds        = 60
          failure_threshold     = 3
        }
      }

      container_concurrency = 80
      timeout_seconds       = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"  = var.frontend_max_instances
        "autoscaling.knative.dev/minScale"  = var.frontend_min_instances
        "run.googleapis.com/cpu-throttling" = "true"
      }

      labels = {
        environment = var.environment
        component   = "frontend"
        service     = "streamlit-ui"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required_apis,
    google_service_account.frontend,
    google_cloud_run_service.backend # Frontend needs backend URL
  ]
}

# ============================================================================
# IAM - PUBLIC ACCESS (Adjust for production)
# ============================================================================

# Backend: Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "backend_public" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Frontend: Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================================
# CLOUD SCHEDULER - Automated Model Retraining
# ============================================================================

resource "google_cloud_scheduler_job" "model_retraining" {
  name        = "model-retraining-weekly"
  description = "Trigger model retraining every Sunday at 2 AM"
  schedule    = "0 2 * * 0" # Every Sunday at 2 AM
  time_zone   = "America/New_York"
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.backend.status[0].url}/train"

    oidc_token {
      service_account_email = google_service_account.training.email
    }
  }

  retry_config {
    retry_count = 3
  }

  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_service.backend
  ]
}
*/
