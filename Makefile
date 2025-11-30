# ============================================================================
# MAKEFILE - Common Development & Deployment Commands
# ============================================================================
# PURPOSE: Simplify common tasks with easy-to-remember commands
# USAGE: make <command>
# EXAMPLE: make deploy-all
# ============================================================================

.PHONY: help
.DEFAULT_GOAL := help

# === Variables ===
PROJECT_ID ?= $(shell echo $$GCP_PROJECT_ID)
REGION ?= us-central1

# === Colors ===
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help message
	@echo "$(BLUE)Real Estate MLOps - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Usage: make <command>$(NC)"
	@echo ""

# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

install: ## Install all dependencies
	pip install -r backend/requirements.backend.txt
	pip install -r frontend/requirements.frontend.txt

run-backend: ## Run backend locally
	cd backend && uvicorn src.api.main:app --reload --port 8080

run-frontend: ## Run frontend locally
	streamlit run frontend/app/streamlit_app.py --server.port 8501

docker-up: ## Start all services with Docker Compose
	docker-compose up

docker-down: ## Stop all services
	docker-compose down

docker-build: ## Rebuild Docker images
	docker-compose build

docker-logs: ## View Docker logs
	docker-compose logs -f

# ============================================================================
# TRAINING
# ============================================================================

train: ## Train all ML models locally
	python backend/src/training/train_gcp.py \
		--data data/Housing.csv \
		--gcs-bucket $(PROJECT_ID)-ml-models \
		--gcs-path models/latest

train-local: ## Train models without GCS upload
	python backend/src/training/train_gcp.py \
		--data data/Housing.csv

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-all: ## Deploy both frontend and backend
	@echo "$(BLUE)Deploying complete system...$(NC)"
	chmod +x scripts/deploy_all.sh
	./scripts/deploy_all.sh

deploy-backend: ## Deploy only backend
	@echo "$(BLUE)Deploying backend...$(NC)"
	chmod +x scripts/deploy_backend.sh
	./scripts/deploy_backend.sh

deploy-frontend: ## Deploy only frontend
	@echo "$(BLUE)Deploying frontend...$(NC)"
	chmod +x scripts/deploy_frontend.sh
	./scripts/deploy_frontend.sh

# ============================================================================
# TESTING
# ============================================================================

test-backend: ## Test backend health
	@BACKEND_URL=$$(gcloud run services describe realestate-backend \
		--region=$(REGION) --format='value(status.url)'); \
	curl $$BACKEND_URL/health | jq

test-frontend: ## Test frontend
	@FRONTEND_URL=$$(gcloud run services describe realestate-frontend \
		--region=$(REGION) --format='value(status.url)'); \
	curl -I $$FRONTEND_URL

test-api: ## Test all API endpoints
	@BACKEND_URL=$$(gcloud run services describe realestate-backend \
		--region=$(REGION) --format='value(status.url)'); \
	echo "Testing: $$BACKEND_URL"; \
	curl $$BACKEND_URL/health && \
	curl $$BACKEND_URL/models/info | jq

# ============================================================================
# MONITORING
# ============================================================================

logs-backend: ## View backend logs
	gcloud run services logs read realestate-backend \
		--region=$(REGION) --limit=50

logs-frontend: ## View frontend logs
	gcloud run services logs read realestate-frontend \
		--region=$(REGION) --limit=50

logs-tail: ## Follow backend logs in real-time
	gcloud run services logs tail realestate-backend \
		--region=$(REGION)

setup-monitoring: ## Setup monitoring and alerts
	chmod +x scripts/setup_monitoring.sh
	./scripts/setup_monitoring.sh

# ============================================================================
# UTILITIES
# ============================================================================

urls: ## Show deployed service URLs
	@echo "$(BLUE)Service URLs:$(NC)"
	@echo "Frontend: $(GREEN)$$(gcloud run services describe realestate-frontend --region=$(REGION) --format='value(status.url)')$(NC)"
	@echo "Backend:  $(GREEN)$$(gcloud run services describe realestate-backend --region=$(REGION) --format='value(status.url)')$(NC)"

status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@gcloud run services list --region=$(REGION) | grep realestate

clean: ## Clean up local files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true

# ============================================================================
# GCP SETUP
# ============================================================================

gcp-init: ## Initialize GCP project
	@echo "$(BLUE)Initializing GCP project...$(NC)"
	gcloud config set project $(PROJECT_ID)
	@echo "$(GREEN)Project set to: $(PROJECT_ID)$(NC)"

gcp-enable-apis: ## Enable required GCP APIs
	gcloud services enable \
		run.googleapis.com \
		cloudbuild.googleapis.com \
		storage.googleapis.com \
		aiplatform.googleapis.com \
		logging.googleapis.com \
		monitoring.googleapis.com \
		secretmanager.googleapis.com

# ============================================================================
# GitHub Setup
# ============================================================================

github-secrets: ## Display commands to set GitHub secrets
	@echo "$(YELLOW)Run these commands to setup GitHub secrets:$(NC)"
	@echo ""
	@echo "gh secret set GCP_PROJECT_ID --body '$(PROJECT_ID)'"
	@echo "gh secret set GCP_SA_KEY --body \"\$$(cat path/to/service-account-key.json)\""
	@echo "gh secret set GCS_BUCKET_NAME --body '$(PROJECT_ID)-ml-models'"
	@echo "gh secret set GROQ_API_KEY --body 'your-groq-api-key'"
	@echo ""

# ============================================================================
# Quick Commands
# ============================================================================

dev: docker-up ## Start local development environment

all: train deploy-all setup-monitoring urls ## Complete setup: train, deploy, monitor

info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "Project ID: $(GREEN)$(PROJECT_ID)$(NC)"
	@echo "Region:     $(GREEN)$(REGION)$(NC)"
	@echo ""