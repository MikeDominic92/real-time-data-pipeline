# Deployment Guide

This guide covers the deployment process for the Real-Time Data Pipeline across different environments.

## Prerequisites

- GCP project setup completed (see [GCP_PROJECT_SETUP.md](GCP_PROJECT_SETUP.md))
- Required permissions and credentials
- CI/CD pipeline access (GitHub Actions)

## Deployment Environments

### 1. Development
- Project ID: `[PROJECT_ID]-dev`
- Used for development and testing
- Limited resources and scale
- Debug logging enabled

### 2. Staging
- Project ID: `[PROJECT_ID]-staging`
- Mirror of production environment
- Used for integration testing
- Performance testing environment

### 3. Production
- Project ID: `[PROJECT_ID]-prod`
- Production environment
- High availability setup
- Monitoring and alerting enabled

## Deployment Process

### 1. Manual Deployment

```bash
# Set environment
export ENVIRONMENT=development  # or staging, production

# Deploy infrastructure
./scripts/deploy_infrastructure.sh --env $ENVIRONMENT

# Deploy pipeline
python -m rtdp.deploy \
    --config config/deployment_config.yaml \
    --env $ENVIRONMENT
```

### 2. CI/CD Deployment (GitHub Actions)

The pipeline automatically deploys to different environments based on branches:
- `develop` → Development
- `staging` → Staging
- `main` → Production

#### Workflow Steps:
1. **Build and Test:**
   ```yaml
   - name: Build and Test
     run: |
       python -m pip install -e ".[dev]"
       pytest
   ```

2. **Deploy Infrastructure:**
   ```yaml
   - name: Deploy Infrastructure
     run: |
       gcloud auth activate-service-account
       ./scripts/deploy_infrastructure.sh
   ```

3. **Deploy Pipeline:**
   ```yaml
   - name: Deploy Pipeline
     run: |
       python -m rtdp.deploy
   ```

## Configuration Management

### 1. Environment Variables
Set these in the deployment environment:
```bash
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
export ENVIRONMENT=production
```

### 2. Secrets Management
Store sensitive values in Secret Manager:
```bash
# Create secret
gcloud secrets create rtdp-config \
    --replication-policy="automatic"

# Add secret version
gcloud secrets versions add rtdp-config \
    --data-file="config/secrets.yaml"
```

## Monitoring Setup

### 1. Cloud Monitoring
- Set up dashboards
- Configure alerts
- Enable logging

### 2. Error Reporting
- Set up error notifications
- Configure error tracking
- Set up PagerDuty integration

## Rollback Procedures

### 1. Pipeline Rollback
```bash
# Rollback to previous version
python -m rtdp.deploy --rollback

# Verify rollback
python -m rtdp.verify
```

### 2. Infrastructure Rollback
```bash
# Rollback infrastructure
./scripts/rollback_infrastructure.sh --version <version>
```

## Health Checks

### 1. Pipeline Health
```bash
# Check pipeline status
python -m rtdp.health_check

# Verify data flow
python -m rtdp.verify_flow
```

### 2. Infrastructure Health
```bash
# Check infrastructure
./scripts/health_check.sh
```

## Performance Tuning

### 1. Dataflow Optimization
- Worker count adjustment
- Memory configuration
- Streaming engine settings

### 2. BigQuery Optimization
- Partition strategy
- Query optimization
- Resource allocation

## Security Measures

### 1. Access Control
- IAM role configuration
- Service account management
- Network security

### 2. Data Protection
- Encryption configuration
- Data retention policies
- Access logging

## Troubleshooting

### Common Issues

1. **Deployment Failures:**
   - Check service account permissions
   - Verify resource quotas
   - Review deployment logs

2. **Pipeline Issues:**
   - Monitor worker logs
   - Check error reporting
   - Verify data flow

3. **Performance Problems:**
   - Review monitoring metrics
   - Check resource utilization
   - Analyze bottlenecks

## Maintenance

### 1. Regular Tasks
- Log rotation
- Resource cleanup
- Performance monitoring

### 2. Updates
- Dependency updates
- Security patches
- Feature deployments

## Disaster Recovery

### 1. Backup Procedures
- Data backup
- Configuration backup
- Recovery testing

### 2. Recovery Procedures
- Service restoration
- Data recovery
- Verification steps

## Compliance

### 1. Audit Logging
- Enable audit logging
- Configure retention
- Set up exports

### 2. Compliance Monitoring
- Security scanning
- Compliance reporting
- Policy enforcement

## Cost Management

### 1. Resource Optimization
- Auto-scaling configuration
- Resource cleanup
- Usage monitoring

### 2. Cost Monitoring
- Budget alerts
- Usage reporting
- Optimization recommendations
