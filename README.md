# Real-Time Data Processing Pipeline

A production-grade data processing pipeline built on Google Cloud Platform (GCP) that demonstrates real-time data ingestion, processing, and analytics capabilities.

## Project Overview

This project showcases a scalable, real-time data processing pipeline using various GCP services:
- Cloud Pub/Sub for real-time message ingestion
- Cloud Dataflow for stream processing
- BigQuery for data warehousing and analytics
- (Optional) Cloud Storage for data lake storage

## Architecture

```
[Data Sources] → [Pub/Sub] → [Dataflow] → [BigQuery] → [Analytics/Visualization]
                    ↓
             [Cloud Storage]
                (Optional)
```

## Directory Structure

- `/src` - Source code for data pipeline components
- `/docs` - Project documentation and setup guides
- `/config` - Configuration files and templates
- `/tests` - Unit and integration tests

## Prerequisites

- Python 3.9+
- Google Cloud SDK
- Active GCP Project with enabled billing
- Required GCP APIs enabled (documented in `/docs/GCP_PROJECT_SETUP.md`)

## Setup Instructions

Detailed setup instructions can be found in the following documentation:
1. [GCP Project Setup](docs/GCP_PROJECT_SETUP.md)
2. [Local Development Setup](docs/LOCAL_DEV_SETUP.md)
3. [Pipeline Configuration](docs/PIPELINE_CONFIG.md)

## Development

### Local Development Setup
```bash
# Clone the repository
git clone https://github.com/mikedominic92/real-time-data-pipeline.git

# Navigate to project directory
cd real-time-data-pipeline

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Testing

```bash
# Run unit tests
python -m pytest tests/unit

# Run integration tests
python -m pytest tests/integration
```

## Deployment

Deployment instructions and CI/CD pipeline configuration can be found in [DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Mike Dominic - [GitHub Profile](https://github.com/mikedominic92)
