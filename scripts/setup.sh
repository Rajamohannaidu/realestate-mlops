# ===============================================
# CONFIG
# ===============================================
PROJECT_ID="academic-atlas-475811-c5"
PROJECT_NUMBER="557418654131"

# IMPORTANT: Must match EXACT GitHub org + repo name
GITHUB_ORG="Rajamohan-Organization"
GITHUB_REPO="realestate-mlops"

gcloud config set project $PROJECT_ID


# ===============================================
# 1. Artifact Registry Repo
# ===============================================
gcloud artifacts repositories create realestate-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repo for realestate images"


# ===============================================
# 2. Terraform backend bucket
# ===============================================
BUCKET_NAME="${PROJECT_ID}-terraform-state"
gsutil mb -l us-central1 gs://$BUCKET_NAME
gsutil versioning set on gs://$BUCKET_NAME


# ===============================================
# 3. Terraform Service Account
# ===============================================
gcloud iam service-accounts create terraformservice \
  --display-name="Terraform Service Account"

SA_EMAIL="terraformservice@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.admin"


# ===============================================
# 4. Bind Terraform SA → GitHub Repository
# ===============================================
REPOSITORY_ATTR="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"

gcloud iam service-accounts add-iam-policy-binding ${SA_EMAIL} \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${REPOSITORY_ATTR}"


# ===============================================
# 5. CI/CD Service Account (for Build & Deploy)
# ===============================================
gcloud iam service-accounts create cicdservice \
  --display-name="CI/CD Service Account"

CI_SA_EMAIL="cicdservice@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"


# Bind CI SA to GitHub OIDC
gcloud iam.service-accounts add-iam-policy-binding ${CI_SA_EMAIL} \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${REPOSITORY_ATTR}"
