# Submission Brief — Ollive AI Challenge

> Copy this email content when submitting to work@ollive.ai

---

## Email

**To:** work@ollive.ai  
**Subject:** Dual AI Assistant — Ollive AI Engineering Challenge Submission

---

Hi Ollive team,

Please find my submission for the AI Engineering Challenge below.

**GitHub Repository:** https://github.com/rajveer100704/dual-assistant  
**Live Demo (HF Spaces):** https://huggingface.co/spaces/rajveer100704/dual-assistant  
**Loom Walkthrough (2 min):** https://www.loom.com/share/YOUR_LOOM_ID  
**Evaluation Report:** attached — `evaluation_report.pdf`

---

### What I Built

A production-grade comparison platform for two AI personal assistants:

- **OSS:** Qwen2.5-0.5B-Instruct via HuggingFace Transformers, running on CPU
- **Frontier:** Gemini 2.5 Flash via Google GenAI (free)

Both share identical memory, safety, and interface layers — isolating model capability as the variable.

---

### Key Engineering Decisions

**Evaluation:** Hybrid scoring pipeline (40% keyword + 60% LLM-as-Judge via Gemini Flash), run across 3 seeded passes (seeds 42/43/44) with mean ± std and 95% CI reporting. 10% of outputs manually spot-verified.

**Safety:** Two-layer moderation — regex prescreening (30+ patterns, zero latency) + neural classifier implementing the LlamaGuard S1–S14 safety taxonomy via Gemini Flash. Potential evaluator circularity acknowledged; GPT-4.1-mini as cross-model judge listed as Priority 1 future improvement.

**Results (3-run mean ± std):**

| Metric | OSS (Qwen2.5) | Frontier (Gemini 2.5 Flash) |
|---|---|---|
| Factual Accuracy | 63.5% ± 1.3 | 87.4% ± 1.5 |
| Jailbreak Refusal | 73.2% ± 5.5 | 100.0% ± 0.0* |
| Bias Safety Score | 71.5% ± 0.5 | 93.7% ± 1.2 |
| Avg Latency | 2064ms ± 93ms | 824ms ± 42ms |
| Cost / 1K Requests | $0.00 | ~$0.15 |

*0 successful harmful completions observed within 25-prompt test set.

**Reproduce:** `python run_evals.py --offline --runs 3 --seed 42`

---

### Bonus Items Completed

- ✅ OSS model deployed publicly on HuggingFace Spaces (CPU, free tier)
- ✅ Cost + latency table across HF Spaces / Modal / RunPod / Ollama / Local
- ✅ Observability: JSON-newline traces, latency timeline, token usage, safety events
- ✅ Hybrid guardrails: regex + LlamaGuard taxonomy neural classifier
- ✅ Memory (k=5 window) + tool use (calculator + datetime)

---

### Report Contents (12 pages)

1. Cover + model summary
2. Executive summary + scorecard (mean ± std + CI95)
3. System architecture diagram
4. Hallucination + jailbreak charts
5. Bias + latency charts
6. Radar chart
7. Engineering tradeoff matrix (9 decisions)
8. Observability dashboard
9. Evaluation methodology (hybrid scoring, benchmarks, statistical rigor)
10. Hybrid moderation architecture
11. Failure analysis (5 OSS failure modes with verbatim examples)
12. Findings & recommendations

---

Thanks for reviewing. Happy to discuss any of the engineering decisions in detail.

Best,  
Rajveer

---

## Attachment Checklist

Before hitting send, confirm these are attached/linked:

- [ ] `evaluation_report.pdf` — attached to email
- [ ] GitHub repo — public, clean commit history, no `.env`
- [ ] HF Spaces URL — app loads, OSS works without API key
- [ ] Loom URL — video plays, under 2:30
- [ ] Replace all placeholders: rajveer100704, YOUR_LOOM_ID, Rajveer
