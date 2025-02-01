# GCP Project Setup Guide

This guide walks through the process of setting up your Google Cloud Platform (GCP) project for the Real-Time Data Pipeline.

## Prerequisites

- A Google Cloud Platform account
- `gcloud` CLI installed and configured
- Billing enabled on your GCP account
- Required permissions to create and manage:
  - Pub/Sub topics and subscriptions
  - Dataflow jobs
  - BigQuery datasets and tables
  - IAM roles and service accounts

## Step-by-Step Setup

### 1. Create a New GCP Project

```bash
# Create a new project
gcloud projects create [PROJECT_ID] --name="Real-Time Data Pipeline"

# Set the project as active
gcloud config set project [PROJECT_ID]
```

### 2. Enable Required APIs

```bash
# Enable required APIs
gcloud services enable \
    pubsub.googleapis.com \
    dataflow.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com \
    cloudresourcemanager.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create rtdp-sa \
    --description="Real-Time Data Pipeline Service Account" \
    --display-name="RTDP Service Account"

# Get your project number
PROJECT_NUMBER=$(gcloud projects describe [PROJECT_ID] --format="value(projectNumber)")

# Grant necessary roles
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:rtdp-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:rtdp-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:rtdp-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/dataflow.worker"
```

### 4. Create Pub/Sub Resources

```bash
# Create topic
gcloud pubsub topics create raw-data-topic

# Create subscription
gcloud pubsub subscriptions create data-processing-sub \
    --topic raw-data-topic \
    --message-retention-duration=1h \
    --ack-deadline=60
```

### 5. Create BigQuery Resources

```bash
# Create dataset
bq mk --dataset \
    --description="Real-time data processing dataset" \
    --location=US \
    [PROJECT_ID]:real_time_data

# Create table (schema defined in config/pipeline_config.yaml)
bq mk \
    --table \
    --description="Processed events table" \
    [PROJECT_ID]:real_time_data.processed_events \
    event_id:STRING,timestamp:TIMESTAMP,data:STRING,processing_timestamp:TIMESTAMP
```

### 6. Set Up Storage Buckets

```bash
# Create storage buckets for Dataflow
gcloud storage buckets create gs://[PROJECT_ID]-dataflow-temp \
    --location=us-central1 \
    --uniform-bucket-level-access

gcloud storage buckets create gs://[PROJECT_ID]-dataflow-staging \
    --location=us-central1 \
    --uniform-bucket-level-access
```

## Verification Steps

1. **Verify API Enablement:**
   ```bash
   gcloud services list --enabled
   ```

2. **Verify Service Account:**
   ```bash
   gcloud iam service-accounts list
   ```

3. **Verify Pub/Sub Setup:**
   ```bash
   gcloud pubsub topics list
   gcloud pubsub subscriptions list
   ```

4. **Verify BigQuery Setup:**
   ```bash
   bq ls
   bq show real_time_data.processed_events
   ```

5. **Verify Storage Buckets:**
   ```bash
   gcloud storage ls
   ```

## Troubleshooting

### Common Issues

1. **API Enablement Failures:**
   - Ensure billing is enabled
   - Check for necessary permissions
   - Wait a few minutes after enabling APIs

2. **Permission Denied Errors:**
   - Verify IAM roles are correctly assigned
   - Check service account email is correct
   - Ensure you're using the correct project

3. **Resource Creation Failures:**
   - Check for naming conflicts
   - Verify resource location constraints
   - Ensure quota limits aren't exceeded

## Next Steps

After completing this setup:
1. Update the `.env` file with your project details
2. Configure the service account key in your development environment
3. Run the pipeline tests to verify everything is working

## Security Considerations

- Regularly rotate service account keys
- Use minimal required permissions
- Enable audit logging
- Set up monitoring and alerting
- Follow the principle of least privilege
