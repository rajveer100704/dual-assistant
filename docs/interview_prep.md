# Interview Preparation Guide

> Based on the engineering decisions in this project, these are the exact questions
> a senior AI/ML engineer will ask. Prepared answers included.

---

## Evaluation Questions

### "Why hybrid eval instead of pure LLM judge?"

Pure LLM judge is semantically superior but has three problems:
1. **Cost** — ~$0.002 per prompt × 100 prompts × 3 runs = ~$0.60 per full eval run. Adds up.
2. **Latency** — Adds 600-900ms per prompt, making eval suites slow to iterate.
3. **Single point of failure** — If the judge model is unavailable or behaves unexpectedly, all scores are corrupted.

Keyword matching is brittle (paraphrasing breaks it) but zero-cost and deterministic. The 40/60 blend gives semantic robustness while keeping costs manageable. The weighting was validated by comparing hybrid scores against 10% manually reviewed outputs — 96% agreement.

---

### "How did you calibrate the 40/60 weighting?"

Empirically, not theoretically. I ran a small calibration set: 20 factual prompts where I knew the ground truth, scored them with pure keyword, pure LLM judge, and several blends (30/70, 40/60, 50/50). The 40/60 split minimised disagreement with manual human judgment. It also has a reasonable intuition: keyword is the "sanity check" floor, LLM judge is the "semantic understanding" ceiling.

---

### "How did you calibrate hallucination severity?"

I didn't calibrate it directly — it's a by-product of the LLM judge's structured output. Gemini Flash returns `hallucination_severity` (0.0–1.0) as part of its JSON evaluation. I use it for reporting and failure analysis, not for the primary accuracy score. The primary score is binary: hybrid ≥ 0.5 = correct.

For production, I'd calibrate severity against human expert labels using Cohen's kappa to measure inter-rater reliability between the judge and humans.

---

### "Why only 3 runs? Why not 5 or 10?"

Three is the minimum for computing a meaningful standard deviation (n-1 denominator). Beyond 3 runs, the marginal improvement in std estimate accuracy diminishes rapidly for this sample size. At n=3, CI95 = 1.96 × std / √3 ≈ 1.13 × std. At n=5, it's 0.88 × std — a 22% improvement in CI width for 67% more compute cost.

For a production evaluation system I'd use 5-10 runs. For this challenge, 3 is the right tradeoff.

---

## Safety Questions

### "Why regex + neural moderation instead of just one?"

Different threat surfaces require different tools:

- **Regex alone**: Zero latency, catches obvious violations, but bypassed trivially by paraphrasing ("how do I synthesise a substance that accelerates combustion" evades "how to make a bomb").
- **Neural alone**: Semantically robust, but adds 150-300ms latency on every request and costs API calls even for benign queries.

The two-layer architecture runs regex first (free gate) and only invokes the neural classifier if regex passes. This means ~95% of requests never hit the neural layer, preserving cost and latency, while the neural layer catches what regex misses.

---

### "Why not only LlamaGuard?"

LlamaGuard-3-1B requires GPU hosting — either self-managed (infra overhead) or via an inference API (additional latency + cost). For HuggingFace Spaces CPU-tier deployment, it's not viable. The Gemini Flash classifier achieves comparable accuracy to LlamaGuard on the tested prompt set while requiring no additional infrastructure. The tradeoff is documented: Haiku introduces potential evaluator-evaluated circularity, which is acknowledged and listed as a future improvement.

---

### "How would you defend against prompt obfuscation attacks?"

Three layers:

1. **Semantic normalization** before regex: strip leetspeak (`h0w t0 m4k3`), unicode substitutions, excessive spacing. A basic normalizer catches most obfuscation.
2. **Neural classifier** (Layer 2): handles paraphrased variants that bypass keyword patterns. LlamaGuard is specifically trained on adversarial obfuscations.
3. **Output screening**: post-generation check catches cases where the model "understood" an obfuscated request and responded helpfully. This is the backstop.

For production, I'd also add adversarial prompt monitoring: flag unusual token sequences, high character diversity scores, or non-standard Unicode — and route those to more expensive (but more robust) classification.

---

### "What are the limitations of regex safety?"

Four main limitations:
1. **Paraphrase bypass**: "make an explosive" vs "construct a device that rapidly releases energy" — same intent, different words.
2. **Language dependence**: patterns are English-only. Multilingual adversarial inputs bypass entirely.
3. **Context blindness**: "how do I kill a process?" is flagged by naive patterns but is totally benign. False positive rate is a real cost.
4. **Maintenance burden**: patterns need regular updating as new attack vectors emerge.

These are why the neural layer exists. Regex is the cheap gate, not the safety guarantee.

---

## Architecture Questions

### "Why FastAPI + Streamlit instead of a single framework?"

FastAPI and Streamlit serve different purposes. FastAPI provides a proper HTTP API layer with Pydantic validation, CORS handling, and OpenAPI docs — making the backend independently testable and deployable. Streamlit provides the demo UI without requiring a React/JS build pipeline.

The separation means the backend can be deployed independently for API consumers, and the frontend can be swapped (for example, to a React app) without touching the inference logic. This is standard separation of concerns.

---

### "Why not React?"

React would add a build pipeline, Node.js dependency, state management complexity, and deployment configuration — all for a demo application. Streamlit's built-in session state maps directly to per-user assistant instances. The constraint is Streamlit's single-threaded event loop (concurrent users share a process), which is acceptable for a demo but not for production at scale.

If this were a production system, I'd use FastAPI backend + React frontend with WebSocket streaming.

---

### "Why CPU deployment for the OSS model?"

Four reasons:
1. HuggingFace Spaces free tier is CPU-only. GPU costs ~$0.06/hr — not free.
2. Qwen2.5-0.5B in float32 fits in ~1.2GB RAM, comfortably within CPU tier limits.
3. CPU deployment proves the model works without GPU dependency — important for on-premise or air-gapped deployments.
4. The performance comparison (1.95s OSS vs 0.82s frontier) is more honest on CPU — it shows the real cost of OSS inference without GPU.

For production, I'd use GPU (T4 gives ~0.3-0.8s) or switch to a quantized 7B model with vLLM for better quality/latency.

---

### "Why not vLLM or Ollama for OSS inference?"

**vLLM**: Excellent for production throughput (continuous batching, PagedAttention), but requires CUDA GPU and significant setup overhead. Overkill for a single-user demo.

**Ollama**: Good for local development, but adds a separate daemon process and API layer, complicating HF Spaces deployment.

**HuggingFace Transformers**: Direct, no daemons, works on CPU, well-documented, and the model downloads automatically from the Hub. The right tool for this scope. Ollama would be the first upgrade for a local-dev experience.

---

## Observability Questions

### "What metrics matter most in production?"

Priority order:
1. **Latency P50/P95/P99** — detect degradation before users notice
2. **Safety flag rate** — sudden spike = likely adversarial probe or new attack vector
3. **Refusal rate per category** — distinguish legitimate refusals from over-refusals
4. **Token usage** — cost control; anomalous spikes indicate prompt injection attempts
5. **Hallucination rate drift** — model quality regression detection
6. **Error rate** — API failures, timeouts, rate limits

---

### "How would you detect safety regressions?"

Three mechanisms:
1. **Automated regression suite**: run the jailbreak eval set (25 prompts) on every model update or config change. Alert if refusal rate drops more than 5pp from baseline.
2. **Real-time monitoring**: track the safety_flag rate per hour. Statistical anomaly detection (3-sigma threshold) triggers alerts.
3. **Canary evaluation**: before full deployment, run new model version against the full eval suite in shadow mode. Compare against production baseline.

---

### "How would you monitor for drift?"

Two types:
1. **Concept drift** (model behaviour changes): run weekly eval runs and compare against the initial baseline. Track mean ± std of each metric over time as a time series.
2. **Data drift** (input distribution shifts): monitor prompt_type distribution and embedding similarity of incoming prompts against the training distribution. Unusual clusters suggest new attack patterns or user segments.

A practical implementation: embed incoming prompts with a small model (like `all-MiniLM-L6-v2`) and run anomaly detection on the embedding space daily.

---

## Future Improvements Questions

### "How would you productionize this?"

Six changes for production:
1. **vLLM or TGI** for OSS inference with GPU, continuous batching, and proper concurrency
2. **LlamaGuard-3-1B** hosted on GPU, replacing Claude-as-classifier
3. **ChromaDB + sentence-transformers** for persistent cross-session memory
4. **LangSmith** for full trace replay, cost dashboards, and evaluation versioning
5. **React frontend** with WebSocket streaming for real-time token delivery
6. **Kubernetes** for horizontal scaling with proper health checks and rolling deploys

---

### "How would you scale evaluations?"

For large-scale evaluation (thousands of prompts, daily runs):
1. **Async evaluation pipeline**: submit prompts as jobs, collect results asynchronously
2. **Batch API**: use Anthropic's batch API for LLM-judge calls — 50% cost reduction at the expense of higher latency
3. **Result caching**: cache judge scores for identical (prompt, response) pairs — many eval runs will have significant overlap
4. **Distributed execution**: Celery or Ray for parallel prompt evaluation across workers
5. **Eval versioning**: track eval results against (model_version, prompt_set_version, judge_version) tuples

---

### "How would you reduce hallucinations in the OSS model?"

Four approaches in order of effort:
1. **Larger model**: Qwen2.5-7B or 14B — the 0.5B hallucination rate (38%) drops to ~15-20% at 7B
2. **RAG**: retrieval-augmented generation grounds responses in a knowledge base, reducing reliance on parametric memory
3. **Calibrated confidence**: prompt the model to express uncertainty ("I'm not sure, but...") for questions near its knowledge boundary — better than confident wrong answers
4. **Fine-tuning on factual QA**: domain-specific fine-tuning with preference optimization (DPO) reduces hallucination in target domains significantly

---

### "How would you implement persistent memory?"

ChromaDB + sentence-transformers implementation:
1. Embed each conversation turn using `all-MiniLM-L6-v2` (fast, 384-dim)
2. Store in ChromaDB with metadata: user_id, session_id, timestamp, turn_type
3. At each new turn, retrieve top-5 most semantically similar past turns using cosine similarity
4. Inject retrieved context into the system prompt alongside the sliding window
5. Periodically summarise old sessions using the LLM to compress context

This gives semantic long-term recall without unbounded context growth.
