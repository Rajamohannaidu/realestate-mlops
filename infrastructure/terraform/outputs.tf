# ============================================================================
# TERRAFORM OUTPUTS - Deployment Information
# ============================================================================
# PURPOSE: Output important values after deployment
# USAGE: terraform output <name>
# ============================================================================

# ============================================================================
# SERVICE URLS
# ============================================================================

output "frontend_url" {
  description = "Public URL of the Streamlit frontend application"
  value       = google_cloud_run_service.frontend.status[0].url
}

output "backend_url" {
  description = "Public URL of the FastAPI backend API"
  value       = google_cloud_run_service.backend.status[0].url
}

output "backend_api_docs" {
  description = "URL to access interactive API documentation (Swagger UI)"
  value       = "${google_cloud_run_service.backend.status[0].url}/docs"
}

output "backend_redoc" {
  description = "URL to access alternative API documentation (ReDoc)"
  value       = "${google_cloud_run_service.backend.status[0].url}/redoc"
}

# ============================================================================
# STORAGE BUCKETS
# ============================================================================

output "models_bucket" {
  description = "GCS bucket name for ML models"
  value       = google_storage_bucket.ml_models.name
}

output "models_bucket_url" {
  description = "GCS URL for ML models bucket"
  value       = "gs://${google_storage_bucket.ml_models.name}"
}

output "training_data_bucket" {
  description = "GCS bucket name for training data"
  value       = google_storage_bucket.training_data.name
}

output "training_data_bucket_url" {
  description = "GCS URL for training data bucket"
  value       = "gs://${google_storage_bucket.training_data.name}"
}

output "reports_bucket" {
  description = "GCS bucket name for user reports"
  value       = google_storage_bucket.reports.name
}

output "reports_bucket_url" {
  description = "GCS URL for reports bucket"
  value       = "gs://${google_storage_bucket.reports.name}"
}

output "explainability_bucket" {
  description = "GCS bucket name for SHAP/LIME artifacts"
  value       = google_storage_bucket.explainability.name
}

output "explainability_bucket_url" {
  description = "GCS URL for explainability bucket"
  value       = "gs://${google_storage_bucket.explainability.name}"
}

# ============================================================================
# SERVICE ACCOUNTS
# ============================================================================

output "backend_service_account" {
  description = "Email of backend service account"
  value       = google_service_account.backend.email
}

output "frontend_service_account" {
  description = "Email of frontend service account"
  value       = google_service_account.frontend.email
}

output "training_service_account" {
  description = "Email of training service account"
  value       = google_service_account.training.email
}

# ============================================================================
# SERVICE INFORMATION
# ============================================================================

output "backend_service_name" {
  description = "Name of the backend Cloud Run service"
  value       = google_cloud_run_service.backend.name
}

output "frontend_service_name" {
  description = "Name of the frontend Cloud Run service"
  value       = google_cloud_run_service.frontend.name
}

output "backend_region" {
  description = "Region where backend is deployed"
  value       = google_cloud_run_service.backend.location
}

output "frontend_region" {
  description = "Region where frontend is deployed"
  value       = google_cloud_run_service.frontend.location
}

# ============================================================================
# SECRETS
# ============================================================================

output "groq_secret_name" {
  description = "Name of Groq API key secret in Secret Manager"
  value       = google_secret_manager_secret.groq_api_key.secret_id
}

output "langchain_secret_name" {
  description = "Name of LangChain API key secret in Secret Manager"
  value       = google_secret_manager_secret.langchain_api_key.secret_id
}

# ============================================================================
# MONITORING & LOGGING
# ============================================================================

output "cloud_console_url" {
  description = "URL to view Cloud Run services in console"
  value       = "https://console.cloud.google.com/run?project=${var.project_id}"
}

output "logs_explorer_url" {
  description = "URL to view logs in Cloud Console"
  value       = "https://console.cloud.google.com/logs/query?project=${var.project_id}"
}

output "monitoring_dashboard_url" {
  description = "URL to view monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring?project=${var.project_id}"
}

# ============================================================================
# DEPLOYMENT COMMANDS
# ============================================================================

output "upload_models_command" {
  description = "Command to upload models to GCS"
  value       = "gsutil -m cp -r models/saved_models/* gs://${google_storage_bucket.ml_models.name}/models/latest/"
}

output "upload_training_data_command" {
  description = "Command to upload training data to GCS"
  value       = "gsutil cp data/Housing.csv gs://${google_storage_bucket.training_data.name}/data/"
}

output "view_backend_logs_command" {
  description = "Command to view backend logs"
  value       = "gcloud run services logs read ${google_cloud_run_service.backend.name} --region=${var.region} --limit=50"
}

output "view_frontend_logs_command" {
  description = "Command to view frontend logs"
  value       = "gcloud run services logs read ${google_cloud_run_service.frontend.name} --region=${var.region} --limit=50"
}

output "update_backend_command" {
  description = "Command to update backend service"
  value       = "gcloud run services update ${google_cloud_run_service.backend.name} --region=${var.region}"
}

output "update_frontend_command" {
  description = "Command to update frontend service"
  value       = "gcloud run services update ${google_cloud_run_service.frontend.name} --region=${var.region}"
}

# ============================================================================
# COST ESTIMATION
# ============================================================================

output "estimated_monthly_cost_range" {
  description = "Estimated monthly cost range in USD"
  value = {
    minimum = "$50-100 (dev with min instances = 0)"
    typical = "$135-390 (production with typical load)"
    maximum = "$500+ (high traffic with max instances)"
  }
}

# ============================================================================
# COMPLETE DEPLOYMENT SUMMARY
# ============================================================================

output "deployment_summary" {
  description = "Complete deployment information"
  value = {
    # Services
    frontend = {
      url           = google_cloud_run_service.frontend.status[0].url
      service_name  = google_cloud_run_service.frontend.name
      region        = google_cloud_run_service.frontend.location
      min_instances = var.frontend_min_instances
      max_instances = var.frontend_max_instances
      memory        = var.frontend_memory
      cpu           = var.frontend_cpu
    }

    backend = {
      url           = google_cloud_run_service.backend.status[0].url
      api_docs      = "${google_cloud_run_service.backend.status[0].url}/docs"
      service_name  = google_cloud_run_service.backend.name
      region        = google_cloud_run_service.backend.location
      min_instances = var.backend_min_instances
      max_instances = var.backend_max_instances
      memory        = var.backend_memory
      cpu           = var.backend_cpu
    }

    # Storage
    storage = {
      models         = "gs://${google_storage_bucket.ml_models.name}"
      training_data  = "gs://${google_storage_bucket.training_data.name}"
      reports        = "gs://${google_storage_bucket.reports.name}"
      explainability = "gs://${google_storage_bucket.explainability.name}"
    }

    # Service Accounts
    service_accounts = {
      frontend = google_service_account.frontend.email
      backend  = google_service_account.backend.email
      training = google_service_account.training.email
    }

    # Environment
    environment = var.environment
    region      = var.region
    project_id  = var.project_id
  }
}

# ============================================================================
# QUICK ACCESS COMMANDS
# ============================================================================

output "quick_access" {
  description = "Quick access commands and URLs"
  value = {
    test_frontend = "curl ${google_cloud_run_service.frontend.status[0].url}"
    test_backend  = "curl ${google_cloud_run_service.backend.status[0].url}/health"
    view_api_docs = "${google_cloud_run_service.backend.status[0].url}/docs"
    upload_models = "gsutil -m cp -r models/saved_models/* gs://${google_storage_bucket.ml_models.name}/models/latest/"
    backend_logs  = "gcloud run services logs read ${google_cloud_run_service.backend.name} --region=${var.region}"
    frontend_logs = "gcloud run services logs read ${google_cloud_run_service.frontend.name} --region=${var.region}"
  }
}