<img width="819" height="635" alt="image" src="https://github.com/user-attachments/assets/582ae37e-df6c-49dd-aafa-46ebe653a863" />---
title: Dual AI Assistant
emoji: 🤖
colorFrom: blue
colorTo: yellow
sdk: docker
sdk_version: 1.35.0
app_file: app.py
pinned: true
license: mit
short_description: Dual AI assistant OSS (Qwen2.5-0.5B) vs Frontier (Gemini 2.5 Flash) · Memory · Safety · Evals
tags:
  - llm
  - evaluation
  - safety
  - streamlit
  - qwen
---

# Dual AI Assistant

Compare **Qwen2.5-0.5B-Instruct** (OSS, CPU-only) vs **Gemini 2.5 Flash** (Frontier API) with:

- ✅ Multi-turn memory (k=5 sliding window)
- ✅ Hybrid safety pipeline (Regex + LlamaGuard taxonomy)
- ✅ Side-by-side comparison tab
- ✅ Live metrics: latency, cost, safety flags
- ✅ Architecture documentation tab

## Setup

Add `GEMINI_API_KEY` in **Settings → Repository Secrets** to enable the Frontier assistant.
The OSS assistant (Qwen2.5-0.5B) runs entirely on CPU — no API key needed.

> ⏱️ **First request to OSS assistant takes ~30s** (model download). Subsequent requests are fast.

## Local Quickstart

```bash
git clone https://github.com/rajveer100704/dual-assistant
cd dual-assistant && make setup && make run
```
