"""BigQuery operations module."""

from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class BigQueryClient:
    """Handles BigQuery operations."""

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        schema: Optional[List[bigquery.SchemaField]] = None,
    ) -> None:
        """Initialize the BigQuery client.

        Args:
            project_id: The GCP project ID.
            dataset_id: The BigQuery dataset ID.
            table_id: The BigQuery table ID.
            schema: Optional schema for table creation.
        """
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        self.schema = schema

    def create_dataset(self) -> None:
        """Create the BigQuery dataset if it doesn't exist."""
        dataset = bigquery.Dataset(f"{self.client.project}.{self.dataset_id}")
        dataset.location = "US"  # Specify the location

        try:
            dataset = self.client.create_dataset(dataset, exists_ok=True)
            print(f"Dataset {self.dataset_id} created or already exists.")
        except Exception as e:
            print(f"Error creating dataset: {e}")
            raise

    def create_table(self) -> None:
        """Create the BigQuery table if it doesn't exist."""
        if not self.schema:
            raise ValueError("Schema is required for table creation")

        table = bigquery.Table(self.table_ref, schema=self.schema)

        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {self.table_id} created or already exists.")
        except Exception as e:
            print(f"Error creating table: {e}")
            raise

    def insert_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert rows into the BigQuery table.

        Args:
            rows: List of row data to insert.

        Returns:
            List of errors if any occurred during insertion.
        """
        table = self.client.get_table(self.table_ref)
        errors = self.client.insert_rows_json(table, rows)

        if errors:
            print(f"Encountered errors while inserting rows: {errors}")

        return errors

    def query(self, query: str) -> bigquery.table.RowIterator:
        """Execute a query against BigQuery.

        Args:
            query: The SQL query to execute.

        Returns:
            Query results as a RowIterator.
        """
        return self.client.query(query).result()
