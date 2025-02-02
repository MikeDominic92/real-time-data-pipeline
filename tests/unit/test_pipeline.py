"""Unit tests for the pipeline processor module."""

import json
from datetime import datetime
from typing import Any, Dict

import apache_beam as beam
import pytest
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

from rtdp.processor.pipeline import DataPipeline, ParseJsonDoFn, ValidateMessageDoFn


@pytest.fixture
def test_pipeline():
    from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
    options = PipelineOptions()
    options.view_as(StandardOptions).streaming = True
    return TestPipeline(options=options)


def test_parse_json_dofn(test_pipeline, sample_message_data: Dict[str, Any]) -> None:
    """Test JSON parsing transformation."""
    with test_pipeline as p:
        input_data = [json.dumps(sample_message_data).encode("utf-8")]
        output = (
            p
            | beam.Create(input_data)
            | beam.ParDo(ParseJsonDoFn())
        )

        assert_that(output, equal_to([sample_message_data]))


def test_validate_message_dofn(sample_message_data: Dict[str, Any]) -> None:
    """Test message validation transformation."""
    with test_pipeline() as p:
        output = (
            p
            | beam.Create([sample_message_data])
            | beam.ParDo(ValidateMessageDoFn())
        )

        # The validation should pass and output the same message
        assert_that(output, equal_to([sample_message_data]))


def test_validate_message_dofn_invalid_message() -> None:
    """Test message validation with invalid message."""
    invalid_message = {
        "invalid": "message"
    }

    with test_pipeline() as p:
        output = (
            p
            | beam.Create([invalid_message])
            | beam.ParDo(ValidateMessageDoFn())
        )

        # Invalid message should be filtered out
        assert_that(output, equal_to([]))


def test_pipeline_creation(test_config: Any) -> None:
    """Test pipeline creation."""
    pipeline = DataPipeline(config=test_config)
    assert pipeline.config == test_config


def test_pipeline_transforms(
    test_config: Any,
    sample_message_data: Dict[str, Any]
) -> None:
    """Test pipeline transformations."""
    pipeline = DataPipeline(config=test_config)

    with test_pipeline() as p:
        # Create sample input
        input_data = [json.dumps(sample_message_data).encode("utf-8")]

        # Apply pipeline transforms
        output = pipeline.apply_transforms(
            p | beam.Create(input_data)
        )

        def check_output(elements: list) -> None:
            """Check output elements."""
            assert len(elements) == 1
            element = elements[0]
            # Check that all original fields are present and unchanged
            assert element["event_id"] == sample_message_data["event_id"]
            assert element["timestamp"] == sample_message_data["timestamp"]
            assert element["data"] == sample_message_data["data"]
            assert element["metadata"] == sample_message_data["metadata"]
            # Check that processing_timestamp exists and is in ISO format
            assert "processing_timestamp" in element
            # Verify it's a valid ISO timestamp
            try:
                datetime.fromisoformat(element["processing_timestamp"])
            except ValueError:
                pytest.fail("processing_timestamp is not in valid ISO format")

        assert_that(output, check_output)


def test_pipeline_with_windowing(
    test_config: Any,
    sample_message_data: Dict[str, Any]
) -> None:
    """Test pipeline with windowing transforms."""
    pipeline = DataPipeline(config=test_config)

    with test_pipeline() as p:
        # Create sample input
        input_data = [
            json.dumps(sample_message_data).encode("utf-8"),
            json.dumps(sample_message_data).encode("utf-8")
        ]

        # Apply pipeline transforms with windowing
        output = (
            p
            | beam.Create(input_data)
            | beam.WindowInto(beam.window.FixedWindows(60))  # 1-minute windows
            | pipeline.apply_transforms()
        )

        def check_windowed_output(elements: list) -> None:
            """Check windowed output elements."""
            assert len(elements) == 2
            for element in elements:
                assert element["event_id"] == sample_message_data["event_id"]
                assert element["timestamp"] == sample_message_data["timestamp"]
                assert "processing_timestamp" in element

        assert_that(output, check_windowed_output)


def test_pipeline_error_handling(
    test_config: Any,
    sample_message_data: Dict[str, Any]
) -> None:
    """Test pipeline error handling."""
    pipeline = DataPipeline(config=test_config)

    with test_pipeline() as p:
        # Create mixed input with valid and invalid messages
        input_data = [
            json.dumps(sample_message_data).encode("utf-8"),
            b"invalid json",
            json.dumps({"invalid": "message"}).encode("utf-8")
        ]

        # Apply pipeline transforms
        output = pipeline.apply_transforms(
            p | beam.Create(input_data)
        )

        # Only valid messages should pass through
        def check_error_handling(elements: list) -> None:
            """Check error handling output."""
            assert len(elements) == 1
            element = elements[0]
            assert element["event_id"] == sample_message_data["event_id"]
            assert element["timestamp"] == sample_message_data["timestamp"]
            assert "processing_timestamp" in element

        assert_that(output, check_error_handling)


sample_message_data = {
    "event_id": "12345",
    "timestamp": "2022-01-01T12:00:00",
    "data": {"key": "value"},
    "metadata": {"source": "test", "version": "1.0"}
}
