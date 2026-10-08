# AI Prompt Log

## Initial AI Prompt

I used ChatGPT as an AI pair-programming assistant to help create the first version of the project.

The prompt used was:

> Create a Python 3.11+ asynchronous multi-provider LLM gateway that supports OpenAI and Anthropic. Use official async clients, normalize streaming responses into a shared StreamChunk schema, calculate token usage, TTFT, tokens per second, latency, and total request cost. Include error handling and avoid exposing API keys.

The generated code was not accepted without review. I manually inspected the implementation for asynchronous programming issues, provider-specific streaming differences, telemetry accuracy, and security concerns.

---

## Audit Finding 1: OpenAI Final Streaming Chunk

### Problem

OpenAI streaming events do not always contain normal text output.

A final usage event may contain an empty `choices` list, and some chunks may contain:

```python
delta.content = None
```

Code that assumes every event contains text could fail when it reaches one of these chunks.

### Unsafe Version

```python
text = event.choices[0].delta.content
output_text += text
```

This assumes:

1. `event.choices` always contains an item.
2. `delta.content` always contains a string.

Neither assumption is safe.

### Fix

The implementation now checks the event before accessing the text:

```python
if not event.choices:
    continue

text = event.choices[0].delta.content

if not text:
    continue
```

### Result

Usage-only and empty streaming events are safely ignored instead of causing the application to crash.

---

## Audit Finding 2: Time-to-First-Token Calculation

### Problem

Time-to-first-token (TTFT) should measure how long the user waits until the first real generated text appears.

An incorrect implementation could record the time when the connection is opened instead of when actual text arrives.

### Unsafe Version

```python
first_token_time = time.perf_counter()

stream = await client.chat.completions.create(...)
```

This would not measure the real first-token delay.

### Fix

The start time is recorded before the request:

```python
start_time = time.perf_counter()
first_token_time = None
```

Then the first-token time is recorded only when a non-empty text chunk is received:

```python
if first_token_time is None:
    first_token_time = time.perf_counter()
```

TTFT is then calculated using:

```python
ttft_ms = (
    (first_token_time - start_time) * 1000
    if first_token_time
    else 0.0
)
```

### Result

TTFT now represents the delay between starting the request and receiving the first visible response text.

---

## Audit Finding 3: Recreating Provider Clients

### Problem

A poor implementation may create a new OpenAI or Anthropic client inside every streaming request.

Example:

```python
async def stream(...):
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

Repeatedly constructing clients is unnecessary and reduces the benefits of connection reuse.

### Fix

The provider clients are initialized when the `UnifiedLLMGateway` object is created:

```python
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
```

Streaming methods then reuse those clients.

### Result

The gateway has a cleaner lifecycle and avoids recreating provider clients during every request.

---

## Audit Finding 4: API Key and Error Exposure

### Problem

Returning raw provider exceptions directly to the application can reveal internal information.

For example:

```python
except Exception as exc:
    raise exc
```

or:

```python
st.error(str(exc))
```

could potentially expose information contained in provider SDK errors.

### Fix

Provider exceptions are wrapped in custom domain exceptions with generic messages:

```python
except Exception as exc:
    raise GatewayProviderError(
        "OpenAI request failed."
    ) from exc
```

Anthropic uses the same pattern:

```python
except Exception as exc:
    raise GatewayProviderError(
        "Anthropic request failed."
    ) from exc
```

The application also stores API keys in environment variables rather than directly in source code.

### Result

The user-facing application does not intentionally expose raw API credentials or provider exception details.

---

## Audit Finding 5: Missing API Keys

### Problem

The application should not crash unpredictably when an API key has not been configured.

### Fix

The gateway only creates provider clients when the matching environment variable exists:

```python
self.openai_client = (
    AsyncOpenAI(api_key=openai_key)
    if openai_key
    else None
)
```

Before sending an OpenAI request:

```python
if self.openai_client is None:
    raise AuthenticationError(
        "OPENAI_API_KEY is missing."
    )
```

Anthropic uses the same approach.

### Result

Missing credentials result in a descriptive application error instead of an uncontrolled failure.

---

## Verification

The project includes automated tests covering:

- normalized `StreamChunk` objects
- concatenation of streamed text
- telemetry values
- token-count tolerance
- request cost calculation
- unknown model handling
- authentication errors
- missing API keys
- API key redaction
- gateway exception behavior

The current test suite can be executed with:

```bash
pytest -v
```

At the time of verification, all 11 tests passed.

---

## Summary

The AI-generated baseline required manual review before it could be treated as a reliable implementation.

The most important issues identified were:

1. OpenAI streaming chunks may not always contain text.
2. TTFT must be measured when the first real text arrives.
3. Provider clients should be reused instead of recreated for every request.
4. Raw provider exceptions should not be exposed directly.
5. Missing API keys should be handled with clear custom errors.

These changes improved the reliability, security, and correctness of the multi-provider gateway.