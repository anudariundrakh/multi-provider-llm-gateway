FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    openai \
    anthropic \
    pydantic \
    tiktoken \
    fastapi \
    uvicorn \
    python-dotenv \
    pytest \
    pytest-asyncio \
    streamlit

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "src/app.py", "--server.address=0.0.0.0"]