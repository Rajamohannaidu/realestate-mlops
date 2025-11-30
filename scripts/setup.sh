# 1. Set project
PROJECT_ID="academic-atlas-475811-c5"
PROJECT_NUMBER="557418654131"   # get from gcloud projects describe $PROJECT_ID --format='value(projectNumber)'
GITHUB_ORG="Rajamohan-Organization"
GITHUB_REPO="realestate-mlops"

gcloud config set project $PROJECT_ID

# 2. Create Artifact Registry repo (Docker) in us-central1
gcloud artifacts repositories create realestate-repo \
  --repository-format=docker --location=us-central1 \
  --description="Docker repo for realestate images"

# 3. Create Terraform backend GCS bucket (must be globally unique)
BUCKET_NAME="${PROJECT_ID}-terraform-state"
gsutil mb -l us-central1 gs://$BUCKET_NAME
gsutil versioning set on gs://$BUCKET_NAME

# 4. Create Terraform service account
gcloud iam service-accounts create terraform-sa \
  --display-name="Terraform Service Account"

SA_EMAIL="terraform-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# 5. Grant SA required roles (adjust least privilege as needed)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.admin"

# 6. Create Workload Identity Pool + Provider for GitHub OIDC
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub OIDC pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"

# 7. Allow the GitHub repo to impersonate the Terraform SA (adjust repo slug)
REPOSITORY_ATTR="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"

gcloud iam service-accounts add-iam-policy-binding ${SA_EMAIL} \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${REPOSITORY_ATTR}"

# 8. Also create a CI service account for pushing images (optional) or reuse the terraform-sa
gcloud iam service-accounts create ci-sa --display-name="CI Service Account"
CI_SA_EMAIL="ci-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# grant Artifact Registry + Storage + Run deploy permissions to CI SA
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Bind GitHub pool to CI SA as well (so GitHub Actions can push images)
gcloud iam service-accounts add-iam-policy-binding ${CI_SA_EMAIL} \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${REPOSITORY_ATTR}"
