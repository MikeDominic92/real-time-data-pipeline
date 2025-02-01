# Configuration Directory

This directory contains configuration files for the Real-Time Data Pipeline project.

## Files

### `pipeline_config.yaml`
Main configuration file for the data pipeline. Contains settings for:
- GCP Project configuration
- Pub/Sub settings
- BigQuery settings
- Schema definitions
- Pipeline performance settings
- Monitoring configuration

### `.env.template`
Template for environment variables. Copy this file to `.env` and update with your values.
Contains configuration for:
- GCP credentials and project settings
- Service endpoints
- Pipeline settings
- Development environment configuration

### `service-account.json.template`
Template for GCP service account credentials. Replace with your actual service account key file.
**Important:** Never commit actual service account keys to version control.

### `deployment_config.yaml`
Configuration for different deployment environments (development, staging, production).
Includes:
- Environment-specific settings
- Dataflow job configuration
- Resource requirements
- Security settings
- Monitoring and logging configuration

## Usage

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Update `.env` with your specific values:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. Set up your service account:
   - Create a service account in GCP Console
   - Download the key file
   - Save it as `service-account.json`
   - Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

4. Update `pipeline_config.yaml` with your specific configuration:
   - Modify schema definitions if needed
   - Adjust performance settings based on your requirements
   - Configure monitoring settings

5. Choose appropriate deployment configuration from `deployment_config.yaml`

## Security Notes

- Never commit `.env` or actual service account keys to version control
- Keep your service account keys secure
- Regularly rotate service account keys
- Use minimal required permissions for service accounts
