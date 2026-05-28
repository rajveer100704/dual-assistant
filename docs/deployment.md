# Deployment Guide

## Option 1 — HuggingFace Spaces (Recommended, Free)

Best for: public demo, zero infra, free CPU tier.

### Steps

```bash
# 1. Create a new Space at https://huggingface.co/spaces
#    SDK: Streamlit | Hardware: CPU Basic (free)

# 2. Add remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/dual-assistant

# 3. Push
git push hf main
```

**Add Secret:** Space Settings → Repository Secrets → `GEMINI_API_KEY = AIzaSy...`

**Cold start:** ~60-90s on first load (model download). Subsequent loads are faster.

**Known limitations:**
- Shared CPU — latency spikes under concurrent load
- OSS model (~1.2 GB) downloads on first cold start

---

## Option 2 — Docker (Any Cloud)

Best for: Railway, Render, Fly.io, AWS ECS, GCP Cloud Run.

```bash
# Build
docker build -t dual-assistant:latest .

# Run locally
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=AIzaSy... \
  dual-assistant:latest

# Open http://localhost:8501
```

**Deploy to Railway:**
```bash
railway login
railway new
railway up
railway variables set GEMINI_API_KEY=AIzaSy...
```

---

## Option 3 — Modal (GPU, Fast Cold Start)

Best for: production load, GPU-accelerated OSS inference.

```bash
pip install modal
modal setup

# Create modal_deploy.py (see below) and run:
modal deploy modal_deploy.py
```

```python
# modal_deploy.py
import modal
stub = modal.Stub("dual-assistant")

@stub.function(
    gpu="T4",
    image=modal.Image.debian_slim().pip_install_from_requirements("requirements.txt"),
    secrets=[modal.Secret.from_name("anthropic-key")],
)
@modal.web_endpoint()
def app():
    import subprocess
    subprocess.Popen(["streamlit", "run", "app.py", "--server.port=8000"])
```

---

## Option 4 — RunPod Serverless

Best for: GPU inference at low cost.

1. Create a RunPod account at https://runpod.io
2. Create a Serverless endpoint with this Docker image
3. Set `GEMINI_API_KEY` as environment variable
4. Your endpoint URL is your demo link

---

## Option 5 — Ollama (Local, No GPU)

Best for: fully offline deployment, data-residency requirements.

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Qwen model
ollama pull qwen2.5:0.5b

# Set env var to use Ollama instead of HF Transformers
export USE_OLLAMA=true
export OLLAMA_BASE_URL=http://localhost:11434

# Run UI
streamlit run app/frontend/streamlit_app.py
```

---

## Cost & Latency Table

| Platform        | Cost (OSS)       | Cold Start | Latency (OSS) | GPU |
|-----------------|------------------|------------|---------------|-----|
| HF Spaces (CPU) | Free             | 60-90s     | 1.5-3s        | No  |
| HF Spaces (T4)  | ~$0.06/hr        | 10-20s     | 0.3-0.8s      | Yes |
| Modal (T4)      | ~$0.00056/s      | 3-5s       | 0.3-0.8s      | Yes |
| RunPod (RTX)    | ~$0.20/hr        | 5-10s      | 0.2-0.5s      | Yes |
| Railway (CPU)   | ~$5/mo           | 5-10s      | 1.5-3s        | No  |
| Local CPU       | $0 (power only)  | 30s (load) | 1.5-3s        | No  |
| Docker (Cloud)  | Varies           | Varies     | Varies        | No  |

Frontier (Gemini 2.5 Flash) API cost: ~$3/$15 per M input/output tokens regardless of deployment.

---

## Environment Variables Reference

| Variable            | Required | Description                          |
|---------------------|----------|--------------------------------------|
| `GEMINI_API_KEY` | Yes*     | Google GenAI (free) key (Frontier model)   |
| `USE_OLLAMA`        | No       | `true` to use Ollama for OSS model   |
| `OLLAMA_BASE_URL`   | No       | Ollama base URL (default localhost)  |
| `DEBUG`             | No       | `true` for verbose logging           |
| `LANGCHAIN_API_KEY` | No       | LangSmith tracing (optional)         |

*OSS assistant works without `GEMINI_API_KEY`. Only Frontier assistant requires it.
