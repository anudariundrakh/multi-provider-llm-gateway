# Multi-Provider LLM Gateway

A Python application that provides a unified interface for interacting with multiple large language model providers.

The project currently supports:

- OpenAI
- Anthropic
- Real-time streaming responses
- Token usage tracking
- Time-to-first-token (TTFT)
- Tokens per second
- Request latency
- Estimated API cost
- Demo mode for testing without paid API calls

---

## Project Architecture

```mermaid
flowchart LR
    A[User] --> B[Streamlit Interface]
    B --> C[UnifiedLLMGateway]
    C --> D[OpenAI]
    C --> E[Anthropic]
    D --> C
    E --> C
    C --> B
    B --> F[Telemetry Display]