# Local Development Setup Guide

This guide walks through setting up your local development environment for the Real-Time Data Pipeline project.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git
- Google Cloud SDK
- A code editor (VS Code recommended)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/mikedominic92/real-time-data-pipeline.git

# Navigate to project directory
cd real-time-data-pipeline
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install project dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### 4. Configure Environment Variables

1. Copy the environment template:
   ```bash
   cp config/.env.template .env
   ```

2. Update the `.env` file with your GCP project details:
   ```plaintext
   GCP_PROJECT_ID=your-project-id
   GCP_REGION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
   ```

### 5. Set Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install
```

### 6. Configure IDE (VS Code)

1. Install recommended extensions:
   - Python
   - Python Type Hint
   - YAML
   - Docker
   - GitLens

2. Configure VS Code settings:
   ```json
   {
       "python.linting.enabled": true,
       "python.linting.flake8Enabled": true,
       "python.formatting.provider": "black",
       "editor.formatOnSave": true,
       "editor.codeActionsOnSave": {
           "source.organizeImports": true
       }
   }
   ```

## Development Workflow

### 1. Code Style

This project uses:
- `black` for code formatting
- `isort` for import sorting
- `flake8` for linting
- `mypy` for type checking

Run the following commands before committing:

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8

# Type checking
mypy src
```

### 2. Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_publisher.py

# Run specific test case
pytest tests/test_publisher.py::test_publish_message
```

### 3. Local Development Server

For local development and testing:

```bash
# Start local development server
python src/rtdp/main.py --local

# Run with specific configuration
python src/rtdp/main.py --config config/pipeline_config.yaml
```

### 4. Using the Pub/Sub Emulator

For local testing without actual GCP resources:

```bash
# Start Pub/Sub emulator
gcloud beta emulators pubsub start

# Set environment variables
$(gcloud beta emulators pubsub env-init)
```

## Troubleshooting

### Common Issues

1. **Import Errors:**
   - Ensure virtual environment is activated
   - Verify all dependencies are installed
   - Check PYTHONPATH includes project root

2. **Authentication Issues:**
   - Verify service account key path is correct
   - Ensure GCP project ID is set correctly
   - Check gcloud authentication

3. **Test Failures:**
   - Update test dependencies
   - Check test data fixtures
   - Verify emulator settings

## Best Practices

1. **Code Quality:**
   - Write tests for new features
   - Maintain type hints
   - Follow PEP 8 guidelines
   - Document public APIs

2. **Version Control:**
   - Create feature branches
   - Write meaningful commit messages
   - Keep commits atomic
   - Rebase before merging

3. **Security:**
   - Never commit sensitive data
   - Use environment variables
   - Regularly update dependencies
   - Follow security guidelines

## Additional Resources

- [Python Development Guide](https://docs.python.org/3/devguide/)
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Apache Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/)
