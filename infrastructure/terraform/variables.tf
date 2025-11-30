# ============================================================================
# TERRAFORM VARIABLES - Configuration Values
# ============================================================================
# PURPOSE: Define all configurable variables for infrastructure
# USAGE: Set via terraform.tfvars or -var flags
# ============================================================================

variable "project_id" {
  description = "GCP Project ID where resources will be created"
  type        = string
  
  validation {
    condition     = length(var.project_id) > 0
    error_message = "Project ID must not be empty."
  }
}

variable "region" {
  description = "GCP Region for deploying resources"
  type        = string
  default     = "us-central1"
  
  validation {
    condition = contains([
      "us-central1", "us-east1", "us-west1", "europe-west1", 
      "asia-southeast1", "asia-northeast1"
    ], var.region)
    error_message = "The region must be a valid Google Cloud Platform region."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "The environment must be dev, staging, or production."
  }
}

# ============================================================================
# FRONTEND CONFIGURATION
# ============================================================================

variable "frontend_min_instances" {
  description = "Minimum number of frontend instances"
  type        = number
  default     = 1
  
  validation {
    condition     = var.frontend_min_instances >= 0 && var.frontend_min_instances <= 10
    error_message = "The frontend minimum instance count must be between 0 and 10."
  }
}

variable "frontend_max_instances" {
  description = "Maximum number of frontend instances"
  type        = number
  default     = 10
  
  validation {
    condition     = var.frontend_max_instances >= 1 && var.frontend_max_instances <= 100
    error_message = "The frontend maximum instance count must be between 1 and 100."
  }
}

variable "frontend_memory" {
  description = "Memory allocation for frontend"
  type        = string
  default     = "2Gi"
  
  validation {
    condition     = can(regex("^[0-9]+(Mi|Gi)$", var.frontend_memory))
    error_message = "The frontend memory value must be in a format such as 512Mi or 2Gi."
  }
}

variable "frontend_cpu" {
  description = "CPU allocation for frontend"
  type        = string
  default     = "2000m"
}

# ============================================================================
# BACKEND CONFIGURATION
# ============================================================================

variable "backend_min_instances" {
  description = "Minimum number of backend instances"
  type        = number
  default     = 2
  
  validation {
    condition     = var.backend_min_instances >= 0 && var.backend_min_instances <= 20
    error_message = "The backend minimum instance count must be between 0 and 20."
  }
}

variable "backend_max_instances" {
  description = "Maximum number of backend instances"
  type        = number
  default     = 20
  
  validation {
    condition     = var.backend_max_instances >= 1 && var.backend_max_instances <= 100
    error_message = "The backend maximum instance count must be between 1 and 100."
  }
}

variable "backend_memory" {
  description = "Memory allocation for backend"
  type        = string
  default     = "4Gi"
}

variable "backend_cpu" {
  description = "CPU allocation for backend"
  type        = string
  default     = "2000m"
}

variable "backend_timeout" {
  description = "Request timeout for backend (seconds)"
  type        = number
  default     = 300
  
  validation {
    condition     = var.backend_timeout >= 60 && var.backend_timeout <= 3600
    error_message = "The backend timeout value must be between 60 and 3600 seconds."
  }
}

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

variable "models_bucket_lifecycle_days" {
  description = "Number of days to keep old model versions"
  type        = number
  default     = 90
}

variable "training_data_lifecycle_days" {
  description = "Number of days to keep training data"
  type        = number
  default     = 90
}

variable "reports_lifecycle_days" {
  description = "Number of days to keep user reports"
  type        = number
  default     = 30
}

# ============================================================================
# MONITORING CONFIGURATION
# ============================================================================

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable Cloud Logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

variable "enable_public_access" {
  description = "Allow public access to services (set false for production)"
  type        = bool
  default     = true
}

variable "enable_iap" {
  description = "Enable Identity-Aware Proxy"
  type        = bool
  default     = false
}

# ============================================================================
# TRAINING CONFIGURATION
# ============================================================================

variable "enable_scheduled_training" {
  description = "Enable scheduled model retraining"
  type        = bool
  default     = true
}

variable "training_schedule" {
  description = "Cron schedule for model retraining"
  type        = string
  default     = "0 2 * * 0"
}

variable "training_timezone" {
  description = "Timezone for scheduled training"
  type        = string
  default     = "America/New_York"
}

# ============================================================================
# COST OPTIMIZATION
# ============================================================================

variable "enable_cpu_throttling" {
  description = "Enable CPU throttling for cost savings"
  type        = bool
  default     = false
}

variable "enable_startup_cpu_boost" {
  description = "Enable startup CPU boost for faster cold starts"
  type        = bool
  default     = true
}

# ============================================================================
# LABELS
# ============================================================================

variable "common_labels" {
  description = "Common labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "realestate-mlops"
    managed_by  = "terraform"
    team        = "ml-engineering"
  }
}
