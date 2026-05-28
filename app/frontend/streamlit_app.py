"""
Dual AI Assistant — Streamlit Frontend
Run: streamlit run app/frontend/streamlit_app.py
"""

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

# ─── Path setup ───────────────────────────────────────────────────────────────
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

from dotenv import load_dotenv
load_dotenv(_root / ".env")

from app.assistants.memory import ConversationMemory
from app.assistants.frontier_assistant import FrontierAssistant
from app.assistants.oss_assistant import OSSAssistant
from app.assistants.tools import route_tools
from app.observability.tracing import log_request, metrics

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dual AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
  }

  .main { background: #0F1117; }

  .stApp { background: linear-gradient(135deg, #0F1117 0%, #1A1D2E 100%); }

  .block-container { padding-top: 1.5rem; }

  /* Header badge */
  .model-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .badge-oss {
    background: rgba(76, 155, 232, 0.15);
    color: #4C9BE8;
    border: 1px solid rgba(76, 155, 232, 0.3);
  }
  .badge-frontier {
    background: rgba(232, 124, 76, 0.15);
    color: #E87C4C;
    border: 1px solid rgba(232, 124, 76, 0.3);
  }

  /* Metric cards */
  .metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
  }
  .metric-value {
    font-size: 22px;
    font-weight: 700;
    color: #E2E8F0;
    font-family: 'JetBrains Mono', monospace;
  }
  .metric-label {
    font-size: 11px;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 2px;
  }

  /* Safety indicator */
  .safety-ok { color: #52C87B; font-size: 13px; }
  .safety-warn { color: #E85C5C; font-size: 13px; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #13151F !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
  }

  /* Chat message overrides */
  [data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px !important;
    margin-bottom: 4px !important;
  }

  /* Input */
  [data-testid="stChatInputTextArea"] {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.12) !important;
    color: #E2E8F0 !important;
  }

  h1, h2, h3 { color: #E2E8F0 !important; }
  p, li { color: #A0AEC0 !important; }

  .stSelectbox label, .stRadio label { color: #A0AEC0 !important; }

  div[data-testid="stButton"] button {
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
  }

  .latency-chip {
    display: inline-block;
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    padding: 2px 7px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #718096;
    margin-left: 6px;
  }
</style>
""", unsafe_allow_html=True)


# ─── Session state init ───────────────────────────────────────────────────────

def _init_state():
    if "oss_assistant" not in st.session_state:
        st.session_state.oss_assistant = OSSAssistant(memory=ConversationMemory(5))
    if "frontier_assistant" not in st.session_state:
        st.session_state.frontier_assistant = FrontierAssistant(memory=ConversationMemory(5))
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []      # [{role, content, assistant, latency, safe}]
    if "active_assistant" not in st.session_state:
        st.session_state.active_assistant = "frontier"
    if "total_requests" not in st.session_state:
        st.session_state.total_requests = 0
    if "latencies" not in st.session_state:
        st.session_state.latencies = {"oss": [], "frontier": []}
    if "safety_flags" not in st.session_state:
        st.session_state.safety_flags = 0


_init_state()


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ Dual AI Assistant")
    st.markdown("---")

    # Assistant selector
    st.markdown("### 🤖 Select Assistant")
    assistant_choice = st.radio(
        "Active assistant",
        options=["frontier", "oss"],
        format_func=lambda x: {
            "oss": "🟦 OSS  —  Qwen2.5-0.5B",
            "frontier": "🟧 Frontier  —  Gemini 2.5 Flash",
        }[x],
        index=0 if st.session_state.active_assistant == "frontier" else 1,
        label_visibility="collapsed",
    )
    st.session_state.active_assistant = assistant_choice

    st.markdown("---")
    metrics_placeholder = st.container()

    def render_sidebar_metrics(placeholder):
        oss_lats = st.session_state.latencies["oss"]
        fr_lats = st.session_state.latencies["frontier"]

        fr_input_tokens = sum(
            m.get("input_tokens", 0)
            for m in metrics.get_all()
            if m.get("assistant") == "frontier"
        )
        fr_output_tokens = sum(
            m.get("output_tokens", 0)
            for m in metrics.get_all()
            if m.get("assistant") == "frontier"
        )
        est_cost = (fr_input_tokens * 3 / 1_000_000) + (fr_output_tokens * 15 / 1_000_000)

        avg_lat = (sum(oss_lats) / len(oss_lats)) if oss_lats else 0
        avg_lat_fr = (sum(fr_lats) / len(fr_lats)) if fr_lats else 0
        flags = st.session_state.safety_flags
        flag_color = "#E85C5C" if flags > 0 else "#52C87B"

        with placeholder:
            st.markdown("### 📊 Session Metrics")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-value">{avg_lat:.0f}<span style="font-size:11px;color:#718096">ms</span></div>
                  <div class="metric-label">OSS Avg Lat</div>
                </div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-value">{avg_lat_fr:.0f}<span style="font-size:11px;color:#718096">ms</span></div>
                  <div class="metric-label">Frontier Avg</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-value">{st.session_state.total_requests}</div>
                  <div class="metric-label">Requests</div>
                </div>""", unsafe_allow_html=True)
            with col_d:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-value" style="color:{flag_color}">{flags}</div>
                  <div class="metric-label">Safety Flags</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 💰 Cost Estimate")
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value">${est_cost:.4f}</div>
              <div class="metric-label">Frontier API Cost (est.)</div>
            </div>
            <div style="margin-top:6px; font-size:11px; color:#4A5568;">
              {fr_input_tokens} in / {fr_output_tokens} out tokens<br>
              OSS cost: <b style="color:#52C87B">$0.00</b> (local)
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

    render_sidebar_metrics(metrics_placeholder)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.oss_assistant.reset()
        st.session_state.frontier_assistant.reset()
        st.rerun()

    # Cold-start info — shown when OSS assistant is selected
    if st.session_state.active_assistant == "oss":
        st.markdown("---")
        st.info(
            "⏱️ **OSS model note:** Qwen2.5-0.5B may take "
            "20–40s on the first request (model loading). "
            "Subsequent requests are faster.",
            icon="ℹ️",
        )


# ─── Header ──────────────────────────────────────────────────────────────────

badge_html = {
    "oss": '<span class="model-badge badge-oss">OSS · Qwen2.5-0.5B-Instruct</span>',
    "frontier": '<span class="model-badge badge-frontier">Frontier · Gemini 2.5 Flash</span>',
}

st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
  <span style="font-size:28px; font-weight:700; color:#E2E8F0;">Dual AI Assistant</span>
  {badge_html[st.session_state.active_assistant]}
</div>
<p style="color:#718096; margin-top:0; font-size:13px;">
  Compare OSS (Qwen2.5-0.5B-Instruct) vs Frontier (Gemini 2.5 Flash) · Multi-turn · Memory · Safety pipeline
</p>
""", unsafe_allow_html=True)

# Tabs
tab_chat, tab_compare, tab_info = st.tabs(["💬 Chat", "📊 Compare Side-by-Side", "ℹ️ Architecture"])

# ─── Chat tab ─────────────────────────────────────────────────────────────────

with tab_chat:
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["assistant"] != st.session_state.active_assistant and msg["role"] == "assistant":
                continue  # only show messages from active assistant

            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    safe_icon = "✅ Safe" if msg.get("safe", True) else "⚠️ Flagged"
                    safe_class = "safety-ok" if msg.get("safe", True) else "safety-warn"
                    st.markdown(
                        f'<span class="{safe_class}">{safe_icon}</span>'
                        f'<span class="latency-chip">{msg.get("latency_ms", 0):.0f}ms</span>',
                        unsafe_allow_html=True,
                    )

    user_input = st.chat_input(
        f"Message {st.session_state.active_assistant.upper()} assistant…"
    )

    if user_input:
        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)

        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "assistant": st.session_state.active_assistant,
        })

        # Tool routing
        tool_result = route_tools(user_input)
        if tool_result:
            result = {
                "response": tool_result,
                "latency_ms": 0,
                "model": "tool",
                "safe": True,
                "flagged_reason": "",
                "input_tokens": 0,
                "output_tokens": 0,
            }
        else:
            with st.spinner("Thinking…"):
                if st.session_state.active_assistant == "oss":
                    result = st.session_state.oss_assistant.chat(user_input)
                else:
                    result = st.session_state.frontier_assistant.chat(user_input)

        # Display assistant message
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(result["response"])
                safe_icon = "✅ Safe" if result["safe"] else "⚠️ Flagged"
                safe_class = "safety-ok" if result["safe"] else "safety-warn"
                st.markdown(
                    f'<span class="{safe_class}">{safe_icon}</span>'
                    f'<span class="latency-chip">{result["latency_ms"]:.0f}ms</span>',
                    unsafe_allow_html=True,
                )

        # Update metrics
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["response"],
            "assistant": st.session_state.active_assistant,
            "latency_ms": result["latency_ms"],
            "safe": result["safe"],
        })
        st.session_state.total_requests += 1
        st.session_state.latencies[st.session_state.active_assistant].append(
            result["latency_ms"]
        )
        if not result["safe"]:
            st.session_state.safety_flags += 1

        log_request(
            assistant=st.session_state.active_assistant,
            prompt=user_input,
            response=result["response"],
            latency_ms=result["latency_ms"],
            model=result["model"],
            safe=result["safe"],
            flagged_reason=result.get("flagged_reason", ""),
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
        )
        render_sidebar_metrics(metrics_placeholder)


# ─── Compare tab ──────────────────────────────────────────────────────────────

with tab_compare:
    st.markdown("### Send the same prompt to both assistants simultaneously")

    compare_input = st.text_area(
        "Enter a prompt to compare",
        height=80,
        placeholder="e.g. Explain quantum entanglement in simple terms.",
    )

    if st.button("🚀 Run Comparison", type="primary"):
        if not compare_input.strip():
            st.warning("Please enter a prompt.")
        else:
            col_oss, col_frontier = st.columns(2)

            with col_oss:
                st.markdown('<span class="model-badge badge-oss">OSS · Qwen2.5-0.5B</span>',
                            unsafe_allow_html=True)
                with st.spinner("Loading OSS model…"):
                    oss_result = st.session_state.oss_assistant.chat(compare_input)

                st.markdown(f"**Response:**\n\n{oss_result['response']}")
                st.markdown(
                    f"⏱ `{oss_result['latency_ms']:.0f}ms`  "
                    f"{'✅' if oss_result['safe'] else '⚠️'} "
                    f"{'Safe' if oss_result['safe'] else 'Flagged'}",
                )

            with col_frontier:
                st.markdown('<span class="model-badge badge-frontier">Frontier · Gemini 2.5 Flash</span>',
                            unsafe_allow_html=True)
                with st.spinner("Calling Frontier API…"):
                    fr_result = st.session_state.frontier_assistant.chat(compare_input)

                st.markdown(f"**Response:**\n\n{fr_result['response']}")
                st.markdown(
                    f"⏱ `{fr_result['latency_ms']:.0f}ms`  "
                    f"{'✅' if fr_result['safe'] else '⚠️'} "
                    f"{'Safe' if fr_result['safe'] else 'Flagged'}  "
                    f"📊 {fr_result.get('input_tokens',0)}↑ {fr_result.get('output_tokens',0)}↓ tokens",
                )

            # Latency delta
            delta = fr_result["latency_ms"] - oss_result["latency_ms"]
            faster = "Frontier" if delta < 0 else "OSS"
            st.info(f"**{faster}** was {abs(delta):.0f}ms faster for this prompt.")


# ─── Architecture tab ─────────────────────────────────────────────────────────

with tab_info:
    st.markdown("""
## Architecture Overview

```
User Input
    │
    ├── Tool Router (calculator / datetime — no model call)
    │
    ├── Safety Pipeline
    │   ├── Prompt Injection Detector  (regex patterns)
    │   └── Harmful Content Filter     (regex + keyword patterns)
    │
    ├── Memory Layer (ConversationBufferWindowMemory, k=5)
    │
    ├── Model Layer
    │   ├── OSS  ── Qwen2.5-0.5B-Instruct  (HuggingFace Transformers, CPU)
    │   └── Frontier ── Gemini 2.5 Flash  (Google GenAI (free))
    │
    ├── Output Safety Check
    │
    └── Observability  (JSON-newline logs → logs/app.log)
```

## Model Comparison

| Property        | OSS (Qwen2.5-0.5B)       | Frontier (Gemini 2.5 Flash)      |
|-----------------|--------------------------|-------------------------------|
| Parameters      | 0.5 B                    | ~100B+ (estimated)            |
| Deployment      | Local / HF Spaces        | Cloud API (Google AI Studio)  |
| Cost            | $0                       | ~$3/$15 per M tokens in/out   |
| GPU Required    | No (CPU works)           | N/A (API)                     |
| Avg Latency     | 1.5–3 s (CPU)            | 0.5–1.5 s                    |
| Context Window  | 32K tokens               | 200K tokens                   |
| Safety Tuning   | Moderate                 | Extensive (Constitutional AI) |

## Safety Pipeline

- **Input Screening**: 30+ regex patterns covering malware, weapons, fraud, hate speech, CSAM, self-harm
- **Injection Defense**: 10+ patterns detecting prompt override / system prompt extraction attempts
- **Output Screening**: Post-generation filter on all model outputs
- **Refusal Rate**: Tracked per session in sidebar metrics

## Memory System

Window-based memory stores the last 5 exchanges (10 messages).
Each assistant maintains an independent memory object, so switching assistants
does not bleed context between them.

## Evaluation Framework

Run `python run_evals.py` from the project root to execute:
1. **Hallucination eval** — 20 factual prompts, keyword-based scoring
2. **Jailbreak eval** — 15 adversarial prompts, refusal classification
3. **Bias eval** — 15 sensitive prompts, safety/correction classification

Charts are generated in `charts/` and a PDF report in `reports/`.
    """)
