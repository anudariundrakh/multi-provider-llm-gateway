import pytest

from src.pricing import calculate_cost
from src.schemas import ChunkTelemetry, StreamChunk


def test_stream_chunk_schema():
    chunk = StreamChunk(
        delta_text="Hello",
        provider="openai",
        model="gpt-4o-mini",
        is_final=False,
    )

    assert chunk.delta_text == "Hello"
    assert chunk.provider == "openai"
    assert chunk.model == "gpt-4o-mini"
    assert chunk.is_final is False


def test_final_chunk_with_telemetry():
    telemetry = ChunkTelemetry(
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        ttft_ms=100.0,
        total_latency_seconds=1.0,
        tokens_per_second=20.0,
        total_cost_usd=0.000014,
    )

    chunk = StreamChunk(
        delta_text="",
        provider="openai",
        model="gpt-4o-mini",
        is_final=True,
        telemetry=telemetry,
    )

    assert chunk.is_final is True
    assert chunk.telemetry is not None
    assert chunk.telemetry.total_tokens == 30
    assert chunk.telemetry.tokens_per_second > 0


def test_cost_calculation():
    cost = calculate_cost(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=1000,
    )

    assert cost > 0