# ─── Dual AI Assistant — Production Dockerfile ───────────────────────────────
# Supports: Docker, Modal, RunPod, Replicate, Railway, Render
# CPU-only image — no GPU required for Qwen2.5-0.5B inference
#
# Build:  docker build -t dual-assistant .
# Run:    docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-ant-... dual-assistant

FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs charts reports screenshots

# Pre-download Qwen model to avoid cold-start delay
# (comment out to keep image small; model will download on first request)
# RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
#     AutoTokenizer.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct', trust_remote_code=True); \
#     AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct', trust_remote_code=True)"

# Streamlit config
ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_THEME_BASE=dark
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
