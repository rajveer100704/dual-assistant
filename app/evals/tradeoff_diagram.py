"""
Engineering tradeoff decision table — full-page, properly aligned.
All text fits within column boundaries using matplotlib's textwrap.
"""

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

CHARTS_DIR = Path(__file__).parent.parent.parent / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

BG     = "#0F1117"
PANEL  = "#1A1D2E"
PANEL2 = "#1C1F30"
BORDER = "#2D3748"
BLUE   = "#4C9BE8"
ORANGE = "#E87C4C"
GREEN  = "#52C87B"
RED    = "#E85C5C"
YELLOW = "#F5C26B"
TEXT   = "#E2E8F0"
MUTED  = "#718096"


def _box(ax, x, y, w, h, fc, ec=None, zorder=2):
    p = FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.003",
        facecolor=fc, edgecolor=ec or fc,
        linewidth=0.6 if ec else 0, zorder=zorder)
    ax.add_patch(p)


def _label(ax, x, y, txt, size=7.8, color=TEXT, bold=False,
           ha="left", va="center", wrap_width=None):
    """Draw text, optionally word-wrapped to wrap_width chars."""
    if wrap_width:
        lines = textwrap.wrap(str(txt), wrap_width)
        txt = "\n".join(lines)
    ax.text(x, y, txt, fontsize=size, color=color,
            ha=ha, va=va,
            fontweight="bold" if bold else "normal",
            zorder=10, linespacing=1.35)


def _dots(ax, cx, cy, filled, total=3, r=0.007, gap=0.022):
    """Draw impact dots."""
    for i in range(total):
        col = GREEN if i < filled else BORDER
        ax.add_patch(plt.Circle((cx + i * gap, cy), r, color=col, zorder=6))


def generate_tradeoff_diagram() -> Path:
    # ── Canvas ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(16, 14))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.text(0.5, 0.970, "Engineering Tradeoff Analysis  —  Dual AI Assistant",
            ha="center", va="center", fontsize=13.5, color=TEXT,
            fontweight="bold", zorder=10)
    ax.text(0.5, 0.945, "Every architectural decision involves benefit, cost, and an alternative path",
            ha="center", va="center", fontsize=8.5, color=MUTED, zorder=10)

    # ── Column definitions  (x_start, width, header, wrap_chars) ─────────────
    # Total usable width: 0.02 → 0.98  (0.96 wide)
    # Cols: Decision | Choice Made | Key Benefit | Cost/Risk | Impact | Alternative
    cols = [
        (0.020, 0.155, "Decision",     18),
        (0.180, 0.165, "Choice Made",  20),
        (0.350, 0.185, "Key Benefit",  24),
        (0.540, 0.160, "Cost / Risk",  21),
        (0.705, 0.090, "Impact",       None),
        (0.800, 0.185, "Alternative",  26),
    ]

    # ── Header row ────────────────────────────────────────────────────────────
    hdr_y, hdr_h = 0.905, 0.038
    _box(ax, 0.015, hdr_y, 0.970, hdr_h, "#252840", BORDER)
    for cx, cw, hdr, _ in cols:
        ax.text(cx + 0.008, hdr_y + hdr_h / 2, hdr,
                fontsize=8.2, color=MUTED, fontweight="bold",
                ha="left", va="center", zorder=10)

    # ── Data rows ─────────────────────────────────────────────────────────────
    rows = [
        {
            "decision":    "OSS Model Selection",
            "choice":      "Qwen2.5-0.5B-Instruct",
            "benefit":     "CPU-deployable, $0 cost, fully reproducible",
            "cost":        "38% hallucination rate, weaker safety alignment",
            "impact":      3,
            "alt":         "Qwen2.5-7B (better accuracy, needs GPU)",
            "color":       BLUE,
        },
        {
            "decision":    "Frontier Model",
            "choice":      "Gemini 2.5 Flash (Google)",
            "benefit":     "Free tier, fast inference, strong safety",
            "cost":        "Self-service rate limits, vendor dependency",
            "impact":      3,
            "alt":         "GPT-4.1-mini or Claude Sonnet (paid, stronger reasoning)",
            "color":       ORANGE,
        },
        {
            "decision":    "Moderation Strategy",
            "choice":      "Hybrid: Regex + Neural (LlamaGuard taxonomy)",
            "benefit":     "Catches both keyword & semantic violations",
            "cost":        "+150-200ms latency when neural layer fires",
            "impact":      3,
            "alt":         "LlamaGuard-3-1B on GPU (lower latency, infra cost)",
            "color":       RED,
        },
        {
            "decision":    "Evaluation Scoring",
            "choice":      "Hybrid: 40% keyword + 60% LLM judge",
            "benefit":     "Semantic correctness, paraphrase-robust scoring",
            "cost":        "Additional API calls (~$0.002 per prompt)",
            "impact":      3,
            "alt":         "Pure LLM judge (higher cost, slower, model-judge dependency)",
            "color":       YELLOW,
        },
        {
            "decision":    "Memory Architecture",
            "choice":      "Sliding window (k=5 exchanges)",
            "benefit":     "Zero-latency, deterministic, no infra dependency",
            "cost":        "No cross-session persistence, limited context",
            "impact":      2,
            "alt":         "ChromaDB vector memory (persistent, semantic recall, +infra)",
            "color":       GREEN,
        },
        {
            "decision":    "Frontend Framework",
            "choice":      "Streamlit",
            "benefit":     "Rapid iteration, built-in session state, easy deploy",
            "cost":        "Less flexible than React, single-threaded event loop",
            "impact":      2,
            "alt":         "FastAPI + React (more scalable, more dev overhead)",
            "color":       BLUE,
        },
        {
            "decision":    "Judge Model",
            "choice":      "Claude Haiku (evaluation)",
            "benefit":     "Lightweight semantic classifier, no GPU needed",
            "cost":        "Potential evaluator-evaluated circularity (documented)",
            "impact":      2,
            "alt":         "GPT-4.1-mini as cross-model judge (eliminates circularity)",
            "color":       ORANGE,
        },
        {
            "decision":    "Statistical Rigour",
            "choice":      "3-run avg with std + CI95 + seeded RNG",
            "benefit":     "Guards against cherry-picking, shows stability",
            "cost":        "3x evaluation time, additional API cost",
            "impact":      3,
            "alt":         "Single run (faster, less credible, variance hidden)",
            "color":       YELLOW,
        },
        {
            "decision":    "Deployment Target",
            "choice":      "HuggingFace Spaces (OSS) + API (Frontier)",
            "benefit":     "Free GPU tier, public URL, zero infra management",
            "cost":        "Cold starts, shared resources, limited compute",
            "impact":      2,
            "alt":         "Modal / RunPod (GPU, faster cold start, requires payment)",
            "color":       GREEN,
        },
    ]

    row_h   = 0.082          # height of each row
    start_y = hdr_y - 0.005  # first row starts just below header

    for i, row in enumerate(rows):
        y_top  = start_y - i * row_h
        y_bot  = y_top - row_h
        y_mid  = (y_top + y_bot) / 2
        bg     = PANEL if i % 2 == 0 else PANEL2

        # Row background
        _box(ax, 0.015, y_bot, 0.970, row_h - 0.003, bg, BORDER)

        # Left accent bar
        _box(ax, 0.015, y_bot + 0.004, 0.004, row_h - 0.011, row["color"])

        pad = 0.010   # left padding inside each cell

        # Decision (colored, bold)
        cx, cw, _, wc = cols[0]
        _label(ax, cx + pad, y_mid, row["decision"],
               size=8.0, color=row["color"], bold=True, wrap_width=wc)

        # Choice Made
        cx, cw, _, wc = cols[1]
        _label(ax, cx + pad, y_mid, row["choice"],
               size=7.6, color=TEXT, wrap_width=wc)

        # Key Benefit
        cx, cw, _, wc = cols[2]
        _label(ax, cx + pad, y_mid, row["benefit"],
               size=7.5, color="#A8D8A8", wrap_width=wc)

        # Cost / Risk
        cx, cw, _, wc = cols[3]
        _label(ax, cx + pad, y_mid, row["cost"],
               size=7.4, color="#D8B08A", wrap_width=wc)

        # Impact dots — centred in column
        cx, cw, _, _ = cols[4]
        dot_cx = cx + 0.010
        _dots(ax, dot_cx, y_mid, row["impact"], total=3)

        # Alternative (italic, muted)
        cx, cw, _, wc = cols[5]
        lines = textwrap.wrap(row["alt"], wc)
        for li, ln in enumerate(lines):
            offset = (len(lines) - 1) * 0.010
            ax.text(cx + pad, y_mid + offset - li * 0.020, ln,
                    fontsize=7.2, color=MUTED, style="italic",
                    ha="left", va="center", zorder=10)

    # ── Footer legend ─────────────────────────────────────────────────────────
    legend_y = start_y - len(rows) * row_h - 0.018
    ax.text(0.022, legend_y, "Impact scale:", fontsize=8, color=MUTED, va="center", zorder=10)

    for i, label in enumerate(["Low", "Medium", "High"]):
        bx = 0.115 + i * 0.095
        for d in range(i + 1):
            ax.add_patch(plt.Circle((bx + d * 0.020, legend_y), 0.007,
                                    color=GREEN, zorder=6))
        ax.text(bx + (i + 1) * 0.020 + 0.008, legend_y, label,
                fontsize=7.5, color=MUTED, va="center", zorder=10)

    ax.text(0.985, legend_y,
            "Radar scores normalized for visual comparison only — not used for ranking.",
            fontsize=7.5, color=MUTED, va="center", ha="right",
            style="italic", zorder=10)

    # ── Save ──────────────────────────────────────────────────────────────────
    plt.tight_layout(pad=0.3)
    path = CHARTS_DIR / "tradeoff_diagram.png"
    plt.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close()
    return path


if __name__ == "__main__":
    p = generate_tradeoff_diagram()
    print(f"Saved: {p}")
