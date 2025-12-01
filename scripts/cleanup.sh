# ===============================================
# CONFIG
# ===============================================
PROJECT_ID="academic-atlas-475811-c5"
PROJECT_NUMBER="557418654131"
GITHUB_ORG="Rajamohan-Organization"
GITHUB_REPO="realestate-mlops"

gcloud config set project $PROJECT_ID

# Service Accounts
TERRAFORM_SA="terraformservice@${PROJECT_ID}.iam.gserviceaccount.com"
CICD_SA="cicdservice@${PROJECT_ID}.iam.gserviceaccount.com"

# Workload Identity pool/provider names
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"

# Artifact Registry Repo
REPO_NAME="realestate-repo"

# Terraform bucket
BUCKET_NAME="${PROJECT_ID}-terraform-state"


echo "=============================="
echo "DELETING CI/CD INFRASTRUCTURE"
echo "=============================="
sleep 2


# ===============================================
# 1. Delete GitHub Workload Identity Bindings
# ===============================================
echo "Removing IAM bindings for service accounts..."

REPOSITORY_ATTR="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"

gcloud iam service-accounts remove-iam-policy-binding $TERRAFORM_SA \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${REPOSITORY_ATTR}" \
  --quiet || true

gcloud iam service-accounts remove-iam-policy-binding $CICD_SA \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${REPOSITORY_ATTR}" \
  --quiet || true


# ===============================================
# 2. Remove IAM roles assigned at project level
# ===============================================
echo "Removing project IAM bindings..."

for ROLE in roles/editor roles/storage.admin roles/artifactregistry.admin; do
  gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${TERRAFORM_SA}" \
    --role="$ROLE" \
    --quiet || true
done

for ROLE in roles/artifactregistry.writer roles/run.admin roles/iam.serviceAccountUser; do
  gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CICD_SA}" \
    --role="$ROLE" \
    --quiet || true
done


# ===============================================
# 3. Delete service accounts
# ===============================================
echo "Deleting service accounts..."

gcloud iam service-accounts delete $TERRAFORM_SA --quiet || true
gcloud iam service-accounts delete $CICD_SA --quiet || true



# ===============================================
# 4. Delete Artifact Registry Repo
# ===============================================
echo "Deleting Artifact Registry repository..."

gcloud artifacts repositories delete $REPO_NAME \
  --location=us-central1 \
  --quiet || true


# ===============================================
# 5. Delete Terraform backend bucket
# ===============================================
echo "Deleting Terraform backend bucket..."

gsutil -m rm -r gs://$BUCKET_NAME || true


echo "=============================="
echo "CLEANUP COMPLETE"
echo "=============================="
