import os
import time
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.pricing import calculate_cost
from src.schemas import ChunkTelemetry, StreamChunk


load_dotenv()


class GatewayProviderError(Exception):
    """Base exception for provider-related errors."""


class AuthenticationError(GatewayProviderError):
    """Raised when an API key is missing or invalid."""


class UnifiedLLMGateway:
    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        self.openai_client = (
            AsyncOpenAI(api_key=openai_key)
            if openai_key
            else None
        )

        self.anthropic_client = (
            AsyncAnthropic(api_key=anthropic_key)
            if anthropic_key
            else None
        )

    async def stream(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[StreamChunk, None]:

        if model.startswith("gpt"):
            async for chunk in self._stream_openai(
                prompt,
                model,
                temperature,
            ):
                yield chunk

        elif model.startswith("claude"):
            async for chunk in self._stream_anthropic(
                prompt,
                model,
                temperature,
            ):
                yield chunk

        else:
            raise GatewayProviderError(
                f"Unsupported model: {model}"
            )

    async def _stream_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
    ) -> AsyncGenerator[StreamChunk, None]:

        if self.openai_client is None:
            raise AuthenticationError(
                "OPENAI_API_KEY is missing."
            )

        start_time = time.perf_counter()
        first_token_time = None
        output_text = ""
        input_tokens = 0
        output_tokens = 0

        try:
            stream = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=temperature,
                stream=True,
                stream_options={
                    "include_usage": True
                },
            )

            async for event in stream:

                if event.usage:
                    input_tokens = event.usage.prompt_tokens
                    output_tokens = event.usage.completion_tokens

                if not event.choices:
                    continue

                text = event.choices[0].delta.content

                if not text:
                    continue

                if first_token_time is None:
                    first_token_time = time.perf_counter()

                output_text += text

                yield StreamChunk(
                    delta_text=text,
                    provider="openai",
                    model=model,
                    is_final=False,
                )

        except Exception as exc:
            raise GatewayProviderError(
                "OpenAI request failed."
            ) from exc

        end_time = time.perf_counter()

        total_latency = end_time - start_time

        ttft_ms = (
            (first_token_time - start_time) * 1000
            if first_token_time
            else 0.0
        )

        tokens_per_second = (
            output_tokens / total_latency
            if total_latency > 0
            else 0.0
        )

        cost = calculate_cost(
            model,
            input_tokens,
            output_tokens,
        )

        telemetry = ChunkTelemetry(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            ttft_ms=round(ttft_ms, 2),
            total_latency_seconds=round(
                total_latency,
                3,
            ),
            tokens_per_second=round(
                tokens_per_second,
                2,
            ),
            total_cost_usd=cost,
        )

        yield StreamChunk(
            delta_text="",
            provider="openai",
            model=model,
            is_final=True,
            telemetry=telemetry,
        )

    async def _stream_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
    ) -> AsyncGenerator[StreamChunk, None]:

        if self.anthropic_client is None:
            raise AuthenticationError(
                "ANTHROPIC_API_KEY is missing."
            )

        start_time = time.perf_counter()
        first_token_time = None
        output_text = ""

        try:
            async with self.anthropic_client.messages.stream(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            ) as stream:

                async for text in stream.text_stream:

                    if first_token_time is None:
                        first_token_time = time.perf_counter()

                    output_text += text

                    yield StreamChunk(
                        delta_text=text,
                        provider="anthropic",
                        model=model,
                        is_final=False,
                    )

                final_message = await stream.get_final_message()

        except Exception as exc:
            raise GatewayProviderError(
                "Anthropic request failed."
            ) from exc

        input_tokens = final_message.usage.input_tokens
        output_tokens = final_message.usage.output_tokens

        end_time = time.perf_counter()
        total_latency = end_time - start_time

        ttft_ms = (
            (first_token_time - start_time) * 1000
            if first_token_time
            else 0.0
        )

        tokens_per_second = (
            output_tokens / total_latency
            if total_latency > 0
            else 0.0
        )

        cost = calculate_cost(
            model,
            input_tokens,
            output_tokens,
        )

        telemetry = ChunkTelemetry(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            ttft_ms=round(ttft_ms, 2),
            total_latency_seconds=round(
                total_latency,
                3,
            ),
            tokens_per_second=round(
                tokens_per_second,
                2,
            ),
            total_cost_usd=cost,
        )

        yield StreamChunk(
            delta_text="",
            provider="anthropic",
            model=model,
            is_final=True,
            telemetry=telemetry,
        )