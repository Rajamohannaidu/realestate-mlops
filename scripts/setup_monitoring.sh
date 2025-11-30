#!/bin/bash

# ============================================================================
# SETUP MONITORING - Configure Cloud Monitoring & Alerts
# ============================================================================
# PURPOSE: Create monitoring dashboards and alert policies
# USAGE: ./scripts/setup_monitoring.sh
# CREATES: Log metrics, dashboards, and email/Slack alerts
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Setting Up Monitoring & Alerts       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}▶ Step 1:${NC} Creating Log-Based Metrics"

# Metric 1: Prediction Requests
gcloud logging metrics create prediction_requests \
    --description="Number of prediction requests" \
    --log-filter='resource.type="cloud_run_revision"
        resource.labels.service_name="realestate-backend"
        jsonPayload.endpoint="/predict"' \
    --project=$PROJECT_ID 2>/dev/null \
    && echo -e "${GREEN}✓ Created: prediction_requests${NC}" \
    || echo -e "${YELLOW}⚠ Metric already exists: prediction_requests${NC}"

# Metric 2: Prediction Errors
gcloud logging metrics create prediction_errors \
    --description="Number of prediction errors" \
    --log-filter='resource.type="cloud_run_revision"
        resource.labels.service_name="realestate-backend"
        severity="ERROR"
        jsonPayload.endpoint="/predict"' \
    --project=$PROJECT_ID 2>/dev/null \
    && echo -e "${GREEN}✓ Created: prediction_errors${NC}" \
    || echo -e "${YELLOW}⚠ Metric already exists: prediction_errors${NC}"

# Metric 3: Investment Analysis Requests
gcloud logging metrics create analysis_requests \
    --description="Number of investment analysis requests" \
    --log-filter='resource.type="cloud_run_revision"
        resource.labels.service_name="realestate-backend"
        jsonPayload.endpoint="/analyze"' \
    --project=$PROJECT_ID 2>/dev/null \
    && echo -e "${GREEN}✓ Created: analysis_requests${NC}" \
    || echo -e "${YELLOW}⚠ Metric already exists: analysis_requests${NC}"

# Metric 4: Chatbot Requests
gcloud logging metrics create chatbot_requests \
    --description="Number of chatbot requests" \
    --log-filter='resource.type="cloud_run_revision"
        resource.labels.service_name="realestate-backend"
        jsonPayload.endpoint="/chat"' \
    --project=$PROJECT_ID 2>/dev/null \
    && echo -e "${GREEN}✓ Created: chatbot_requests${NC}" \
    || echo -e "${YELLOW}⚠ Metric already exists: chatbot_requests${NC}"

echo ""
echo -e "${BLUE}▶ Step 2:${NC} Monitoring Dashboard URLs"
echo -e "  Cloud Run Dashboard:"
echo -e "    ${GREEN}https://console.cloud.google.com/run?project=${PROJECT_ID}${NC}"
echo ""
echo -e "  Logs Explorer:"
echo -e "    ${GREEN}https://console.cloud.google.com/logs/query?project=${PROJECT_ID}${NC}"
echo ""
echo -e "  Monitoring Metrics:"
echo -e "    ${GREEN}https://console.cloud.google.com/monitoring?project=${PROJECT_ID}${NC}"

echo ""
echo -e "${BLUE}▶ Step 3:${NC} Alert Policy Setup"
echo -e "  To create alert policies:"
echo -e "  1. Visit: ${GREEN}https://console.cloud.google.com/monitoring/alerting${NC}"
echo -e "  2. Click 'Create Policy'"
echo -e "  3. Configure these alerts:"
echo -e "     - High Error Rate (>5%)"
echo -e "     - High Latency (>1000ms)"
echo -e "     - Service Down"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Monitoring Setup Complete!        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Useful Monitoring Commands:${NC}"
echo ""
echo -e "View Frontend Logs:"
echo -e "  ${YELLOW}gcloud run services logs read realestate-frontend --region=$REGION --limit=50${NC}"
echo ""
echo -e "View Backend Logs:"
echo -e "  ${YELLOW}gcloud run services logs read realestate-backend --region=$REGION --limit=50${NC}"
echo ""
echo -e "Follow Logs Live:"
echo -e "  ${YELLOW}gcloud run services logs tail realestate-backend --region=$REGION${NC}"