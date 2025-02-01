from setuptools import setup, find_packages

setup(
    name="real-time-data-pipeline",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-cloud-pubsub>=2.18.4",
        "google-cloud-bigquery>=3.11.4",
        "apache-beam[gcp]>=2.50.0",
        "google-cloud-storage>=2.13.0",
    ],
    extras_require={
        "dev": [
            "python-dotenv>=1.0.0",
            "black>=23.12.1",
            "isort>=5.13.2",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "test": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ],
    },
    python_requires=">=3.9",
    author="Mike Dominic",
    author_email="mikedominic92@gmail.com",
    description="A real-time data processing pipeline using Google Cloud Platform services",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mikedominic92/real-time-data-pipeline",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
