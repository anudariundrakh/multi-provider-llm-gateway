import os

from src.gateway import (
    AuthenticationError,
    GatewayProviderError,
    UnifiedLLMGateway,
)


def test_authentication_error_message():
    error = AuthenticationError(
        "OPENAI_API_KEY is missing."
    )

    assert "missing" in str(error).lower()


def test_error_message_does_not_expose_api_key():
    fake_api_key = "sk-test-super-secret-key"

    error = GatewayProviderError(
        "Provider request failed."
    )

    assert fake_api_key not in str(error)


def test_gateway_error_is_exception():
    error = GatewayProviderError(
        "Something went wrong."
    )

    assert isinstance(error, Exception)


def test_missing_openai_key_creates_no_client(monkeypatch):
    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False,
    )

    gateway = UnifiedLLMGateway()

    assert gateway.openai_client is None


def test_missing_anthropic_key_creates_no_client(monkeypatch):
    monkeypatch.delenv(
        "ANTHROPIC_API_KEY",
        raising=False,
    )

    gateway = UnifiedLLMGateway()

    assert gateway.anthropic_client is None