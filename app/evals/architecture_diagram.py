"""
Architecture diagram generator.
Produces a clean system architecture PNG suitable for embedding in the PDF report.
Uses matplotlib patches for precise layout control.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

CHARTS_DIR = Path(__file__).parent.parent.parent / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Color palette
BG        = "#0F1117"
PANEL     = "#1A1D2E"
BORDER    = "#2D3748"
OSS_BLUE  = "#4C9BE8"
FR_ORANGE = "#E87C4C"
GREEN     = "#52C87B"
YELLOW    = "#F5C26B"
RED       = "#E85C5C"
TEXT      = "#E2E8F0"
MUTED     = "#718096"


def _box(ax, x, y, w, h, label, sublabel="", color=PANEL, border=BORDER,
         fontsize=9, text_color=TEXT):
    """Draw a rounded box with label."""
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.015",
        facecolor=color, edgecolor=border, linewidth=1.2,
        zorder=3,
    )
    ax.add_patch(box)
    if sublabel:
        ax.text(x, y + 0.012, label, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight="bold", zorder=4)
        ax.text(x, y - 0.018, sublabel, ha="center", va="center",
                fontsize=fontsize - 1.5, color=MUTED, zorder=4)
    else:
        ax.text(x, y, label, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight="bold", zorder=4)


def _arrow(ax, x1, y1, x2, y2, color=MUTED):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=1.2,
            mutation_scale=12,
        ),
        zorder=2,
    )


def generate_architecture_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(0.5, 0.97, "Dual AI Assistant  —  System Architecture",
            ha="center", va="center", fontsize=14, color=TEXT,
            fontweight="bold", zorder=5)
    ax.text(0.5, 0.93, "Production-grade safety  *  Memory  *  Evaluation  *  Observability",
            ha="center", va="center", fontsize=9, color=MUTED, zorder=5)

    # ── Row 1: User ────────────────────────────────────────────────────────────
    _box(ax, 0.5, 0.87, 0.18, 0.05, "User Input",
         color="#252840", border=BORDER, fontsize=9)

    _arrow(ax, 0.5, 0.845, 0.5, 0.81)

    # ── Row 2: Streamlit UI ────────────────────────────────────────────────────
    _box(ax, 0.5, 0.79, 0.30, 0.05,
         "Streamlit Frontend",
         "Chat  *  Compare  *  Architecture tabs",
         color="#1E2235", border="#3A4060", fontsize=9)

    _arrow(ax, 0.5, 0.765, 0.5, 0.73)

    # ── Row 3: FastAPI ─────────────────────────────────────────────────────────
    _box(ax, 0.5, 0.71, 0.30, 0.05,
         "FastAPI Backend",
         "POST /chat   POST /evaluate   GET /metrics",
         color="#1E2235", border="#3A4060", fontsize=9)

    _arrow(ax, 0.5, 0.685, 0.5, 0.645)

    # ── Row 4: Tool router ─────────────────────────────────────────────────────
    _box(ax, 0.5, 0.625, 0.26, 0.045,
         "Tool Router",
         "Calculator  *  DateTime  (zero LLM cost)",
         color="#1C2530", border=GREEN, fontsize=8.5, text_color=GREEN)

    _arrow(ax, 0.37, 0.625, 0.23, 0.625)
    _arrow(ax, 0.63, 0.625, 0.77, 0.625)
    _arrow(ax, 0.5, 0.603, 0.5, 0.565)

    ax.text(0.15, 0.635, "tool\nresolved", ha="center", va="center",
            fontsize=7.5, color=GREEN, style="italic")
    ax.text(0.85, 0.635, "tool\nresolved", ha="center", va="center",
            fontsize=7.5, color=GREEN, style="italic")

    # ── Row 5: Safety Pipeline ─────────────────────────────────────────────────
    _box(ax, 0.5, 0.545, 0.42, 0.055,
         "Hybrid Safety Pipeline",
         "Layer 1: Regex prescreening (30+ patterns)   Layer 2: Neural classifier (LlamaGuard taxonomy)",
         color="#1C1A20", border=RED, fontsize=8.5, text_color="#E8A0A0")

    _arrow(ax, 0.5, 0.517, 0.5, 0.48)

    ax.text(0.82, 0.530, "BLOCKED ->\nrefusal", ha="center", va="center",
            fontsize=7.5, color=RED, style="italic")
    ax.annotate("", xy=(0.73, 0.545), xytext=(0.82, 0.545),
                arrowprops=dict(arrowstyle="<-", color=RED, lw=1, mutation_scale=8))

    # ── Row 6: Memory ──────────────────────────────────────────────────────────
    _box(ax, 0.5, 0.46, 0.32, 0.05,
         "ConversationMemory  (k=5 window)",
         "Independent per assistant  *  per session",
         color="#1A2030", border=YELLOW, fontsize=8.5, text_color=YELLOW)

    _arrow(ax, 0.5, 0.435, 0.5, 0.395)

    # ── Row 7: Model Router ────────────────────────────────────────────────────
    _box(ax, 0.5, 0.375, 0.22, 0.045,
         "Model Router",
         "assistant = oss | frontier",
         color="#1E2235", border=BORDER, fontsize=8.5)

    _arrow(ax, 0.39, 0.375, 0.25, 0.340)
    _arrow(ax, 0.61, 0.375, 0.75, 0.340)

    # ── Row 8: Models ─────────────────────────────────────────────────────────
    _box(ax, 0.22, 0.305, 0.28, 0.065,
         "OSS  --  Qwen2.5-0.5B-Instruct",
         "HuggingFace Transformers  *  CPU  *  $0",
         color="#0F1C30", border=OSS_BLUE, fontsize=8.5, text_color=OSS_BLUE)

    _box(ax, 0.78, 0.305, 0.28, 0.065,
         "Frontier  --  Gemini 2.5 Flash",
         "Google GenAI  *  Free tier (1M tokens/day)",
         color="#2A1A0F", border=FR_ORANGE, fontsize=8.5, text_color=FR_ORANGE)

    _arrow(ax, 0.22, 0.272, 0.22, 0.235)
    _arrow(ax, 0.78, 0.272, 0.78, 0.235)

    # ── Row 9: Output safety ───────────────────────────────────────────────────
    _box(ax, 0.22, 0.215, 0.24, 0.04,
         "Output Safety Screen", color="#1C1A20", border=RED, fontsize=8, text_color="#E8A0A0")
    _box(ax, 0.78, 0.215, 0.24, 0.04,
         "Output Safety Screen", color="#1C1A20", border=RED, fontsize=8, text_color="#E8A0A0")

    _arrow(ax, 0.22, 0.195, 0.22, 0.165)
    _arrow(ax, 0.78, 0.195, 0.78, 0.165)

    # ── Row 10: Observability ──────────────────────────────────────────────────
    _box(ax, 0.5, 0.148, 0.42, 0.05,
         "Observability  --  logs/app.log",
         "latency  *  tokens  *  safety_flags  *  prompt_type  *  eval_scores  (JSON)",
         color="#151820", border="#3A4060", fontsize=8.5)

    _arrow(ax, 0.22, 0.165, 0.34, 0.148)
    _arrow(ax, 0.78, 0.165, 0.66, 0.148)
    _arrow(ax, 0.5, 0.123, 0.5, 0.093)

    # ── Row 11: Evaluation ─────────────────────────────────────────────────────
    _box(ax, 0.5, 0.073, 0.55, 0.055,
         "Evaluation Framework  (LLM-as-Judge + Keyword Hybrid)",
         "Hallucination (50)   Jailbreak (25)   Bias (25)   Charts   PDF Report",
         color="#151A20", border="#3A5060", fontsize=8.5)

    ax.text(0.5, 0.025,
            "Inspired by: TruthfulQA  *  JailbreakBench  *  AdvBench  *  RealToxicityPrompts  *  WinoBias  *  StereoSet  *  BBQ",
            ha="center", va="center", fontsize=7, color=MUTED, style="italic")

    plt.tight_layout(pad=0.3)
    path = CHARTS_DIR / "architecture_diagram.png"
    plt.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close()
    return path


if __name__ == "__main__":
    p = generate_architecture_diagram()
    print(f"Saved: {p}")
