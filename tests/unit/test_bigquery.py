"""Unit tests for the BigQuery storage module."""

from typing import Any, Dict

import pytest
from google.api_core import exceptions
from google.cloud import bigquery

from rtdp.storage.bigquery import BigQueryClient


def test_bigquery_client_initialization(test_config: Any) -> None:
    """Test BigQuery client initialization."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    assert client.project_id == test_config.project_id
    assert client.dataset_id == test_config.dataset_id
    assert client.table_id == test_config.table_id
    assert isinstance(client.client, bigquery.Client)


def test_insert_rows(
    mock_bigquery_client: None, test_config: Any, sample_message_data: Dict[str, Any]
) -> None:
    """Test inserting rows into BigQuery."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    # Insert a single row
    errors = client.insert_rows([sample_message_data])
    assert not errors

    # Verify the row was inserted
    assert len(client.client.inserted_rows) == 1
    assert client.client.inserted_rows[0] == sample_message_data


def test_insert_multiple_rows(
    mock_bigquery_client: None, test_config: Any, sample_message_data: Dict[str, Any]
) -> None:
    """Test inserting multiple rows into BigQuery."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    # Create multiple rows
    rows = [
        sample_message_data,
        dict(sample_message_data, event_id="test-event-456"),
        dict(sample_message_data, event_id="test-event-789"),
    ]

    # Insert multiple rows
    errors = client.insert_rows(rows)
    assert not errors

    # Verify all rows were inserted
    assert len(client.client.inserted_rows) == 3
    assert all(row in client.client.inserted_rows for row in rows)


def test_query_data(mock_bigquery_client: None, test_config: Any) -> None:
    """Test querying data from BigQuery."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    # Execute a query
    query = f"""
    SELECT *
    FROM `{test_config.project_id}.{test_config.dataset_id}.{test_config.table_id}`
    LIMIT 10
    """
    results = client.query(query)

    # Verify query was executed
    assert len(client.client.queries) == 1
    assert client.client.queries[0] == query
    assert isinstance(results, list)


def test_table_exists(mock_bigquery_client: None, test_config: Any) -> None:
    """Test checking if table exists."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    assert client.table_exists()


def test_get_table_schema(mock_bigquery_client: None, test_config: Any) -> None:
    """Test getting table schema."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    schema = client.get_table_schema()
    assert isinstance(schema, list)
    assert all(isinstance(field, bigquery.SchemaField) for field in schema)


def test_error_handling(
    mock_bigquery_client: None, test_config: Any, sample_message_data: Dict[str, Any]
) -> None:
    """Test error handling in BigQuery operations."""
    client = BigQueryClient(
        project_id=test_config.project_id,
        dataset_id=test_config.dataset_id,
        table_id=test_config.table_id,
    )

    # Test with invalid data
    invalid_data = {"invalid_field": "value"}
    with pytest.raises(exceptions.BadRequest):
        client.insert_rows([invalid_data])

    # Test with invalid query
    invalid_query = "INVALID SQL QUERY"
    with pytest.raises(exceptions.BadRequest):
        client.query(invalid_query)
