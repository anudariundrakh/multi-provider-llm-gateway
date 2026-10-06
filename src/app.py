import asyncio
import time

import streamlit as st

from gateway import UnifiedLLMGateway


st.set_page_config(
    page_title="Multi-Provider LLM Gateway",
    page_icon="🤖",
    layout="wide",
)

st.title("Multi-Provider LLM Gateway")

st.write(
    "Send a prompt to OpenAI or Anthropic and view live response telemetry."
)

st.info(
    "Demo Mode uses simulated responses and simulated telemetry. "
    "No paid API calls are made while Demo Mode is enabled."
)

demo_mode = st.checkbox(
    "Demo Mode",
    value=True,
    help="Use fake local responses without paid API calls.",
)


provider = st.selectbox(
    "Choose Provider",
    ["OpenAI", "Anthropic"],
)

if provider == "OpenAI":
    model = st.selectbox(
        "Choose Model",
        [
            "gpt-4o-mini",
            "gpt-4o",
        ],
    )
else:
    model = st.selectbox(
        "Choose Model",
        [
            "claude-3-5-haiku",
            "claude-3-5-sonnet",
        ],
    )


temperature = st.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.1,
)


prompt = st.text_area(
    "Enter your prompt",
    placeholder="Example: Explain recursion in simple terms.",
)


async def run_demo(provider, model):
    response_text = ""

    if provider == "OpenAI":
        fake_response = (
            "This is a simulated OpenAI response. "
            "The text is streaming locally without using a paid API."
        )
    else:
        fake_response = (
            "This is a simulated Anthropic response. "
            "The text is streaming locally without using a paid API."
        )

    response_placeholder = st.empty()

    start_time = time.perf_counter()
    first_token_time = None

    words = fake_response.split()

    for word in words:
        if first_token_time is None:
            first_token_time = time.perf_counter()

        response_text += word + " "

        response_placeholder.markdown(response_text)

        await asyncio.sleep(0.08)

    end_time = time.perf_counter()

    total_latency = end_time - start_time

    ttft_ms = (
        (first_token_time - start_time) * 1000
        if first_token_time
        else 0.0
    )

    input_tokens = 12
    output_tokens = len(words)
    total_tokens = input_tokens + output_tokens

    tokens_per_second = (
        output_tokens / total_latency
        if total_latency > 0
        else 0.0
    )

    fake_cost = 0.000142
    st.caption("Simulated telemetry for demonstration purposes")

    st.subheader("Telemetry")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "TTFT",
        f"{ttft_ms:.2f} ms",
    )

    col2.metric(
        "Tokens / Second",
        f"{tokens_per_second:.2f}",
    )

    col3.metric(
        "Total Tokens",
        total_tokens,
    )

    col4.metric(
        "Cost",
        f"${fake_cost:.6f}",
    )

    st.write(
        f"Input Tokens: {input_tokens}"
    )

    st.write(
        f"Output Tokens: {output_tokens}"
    )

    st.write(
        f"Total Latency: {total_latency:.3f} seconds"
    )


async def run_gateway(prompt, model, temperature):
    gateway = UnifiedLLMGateway()

    response_text = ""

    response_placeholder = st.empty()

    async for chunk in gateway.stream(
        prompt=prompt,
        model=model,
        temperature=temperature,
    ):

        if not chunk.is_final:
            response_text += chunk.delta_text

            response_placeholder.markdown(
                response_text
            )

        else:
            telemetry = chunk.telemetry

            st.subheader("Telemetry")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "TTFT",
                f"{telemetry.ttft_ms} ms",
            )

            col2.metric(
                "Tokens / Second",
                telemetry.tokens_per_second,
            )

            col3.metric(
                "Total Tokens",
                telemetry.total_tokens,
            )

            col4.metric(
                "Cost",
                f"${telemetry.total_cost_usd:.6f}",
            )

            st.write(
                f"Input Tokens: {telemetry.input_tokens}"
            )

            st.write(
                f"Output Tokens: {telemetry.output_tokens}"
            )

            st.write(
                f"Total Latency: "
                f"{telemetry.total_latency_seconds} seconds"
            )


if st.button("Send Prompt"):

    if not prompt.strip():
        st.warning(
            "Please enter a prompt first."
        )

    else:
        try:
            if demo_mode:
                asyncio.run(
                    run_demo(
                        provider,
                        model,
                    )
                )
            else:
                asyncio.run(
                    run_gateway(
                        prompt,
                        model,
                        temperature,
                    )
                )

        except Exception as error:
            st.error(
                f"Request failed: {error}"
            )