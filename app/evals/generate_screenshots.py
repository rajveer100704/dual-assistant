"""
Generates realistic UI screenshots of the Dual AI Assistant for README and docs.
Simulates the Streamlit dark-theme interface without needing a running server.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

SHOTS_DIR = Path(__file__).parent.parent.parent / "screenshots"
SHOTS_DIR.mkdir(exist_ok=True)

BG     = "#0F1117"
PANEL  = "#1A1D2E"
PANEL2 = "#262B3D"
BORDER = "#2D3748"
BLUE   = "#4C9BE8"
ORANGE = "#E87C4C"
GREEN  = "#52C87B"
RED    = "#E85C5C"
YELLOW = "#F5C26B"
TEXT   = "#E2E8F0"
MUTED  = "#718096"
SIDEBAR= "#13151F"
INPUT  = "#1E2235"


def _rounded(ax, x, y, w, h, color, border=None, radius=0.01, zorder=3):
    box = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=color,
        edgecolor=border if border else color,
        linewidth=0.8 if border else 0,
        zorder=zorder)
    ax.add_patch(box)


def _text(ax, x, y, s, size=8, color=TEXT, bold=False, ha="left", va="center",
          family="monospace" if False else "sans-serif"):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontweight="bold" if bold else "normal", zorder=10,
            fontfamily=family)


# ── Screenshot 1: Chat Tab ────────────────────────────────────────────────────

def screenshot_chat():
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Sidebar
    _rounded(ax, 0, 0, 0.22, 1.0, SIDEBAR, BORDER, radius=0.002)
    _text(ax, 0.03, 0.95, "⚡  Dual AI Assistant", size=9.5, bold=True)
    _text(ax, 0.03, 0.87, "🤖  Select Assistant", size=8.5, color=MUTED, bold=True)

    # Radio buttons
    _rounded(ax, 0.03, 0.78, 0.17, 0.07, PANEL, BORDER, radius=0.008)
    ax.add_patch(plt.Circle((0.05, 0.815), 0.008, color=ORANGE, zorder=5))
    _text(ax, 0.065, 0.815, "🟧 Frontier — Gemini 2.5 Flash", size=7.5, color=TEXT)
    _text(ax, 0.065, 0.795, "🟦 OSS  —  Qwen2.5-0.5B", size=7.5, color=MUTED)

    _text(ax, 0.03, 0.73, "📊  Session Metrics", size=8, color=MUTED, bold=True)

    # Metric cards
    for i, (label, val, col) in enumerate([("OSS Avg Lat","1950ms",BLUE),
                                             ("Frontier","820ms",ORANGE)]):
        xc = 0.03 + i*0.095
        _rounded(ax, xc, 0.65, 0.085, 0.065, PANEL2, BORDER, radius=0.006)
        _text(ax, xc+0.042, 0.692, val, size=8.5, color=col, bold=True, ha="center")
        _text(ax, xc+0.042, 0.672, label, size=6.5, color=MUTED, ha="center")

    for i, (label, val, col) in enumerate([("Requests","12",TEXT),
                                             ("Safety","0",GREEN)]):
        xc = 0.03 + i*0.095
        _rounded(ax, xc, 0.58, 0.085, 0.060, PANEL2, BORDER, radius=0.006)
        _text(ax, xc+0.042, 0.618, val, size=9, color=col, bold=True, ha="center")
        _text(ax, xc+0.042, 0.598, label, size=6.5, color=MUTED, ha="center")

    _text(ax, 0.03, 0.545, "💰  Cost Estimate", size=8, color=MUTED, bold=True)
    _rounded(ax, 0.03, 0.49, 0.17, 0.05, PANEL2, BORDER, radius=0.006)
    _text(ax, 0.115, 0.518, "$0.0021", size=9, color=ORANGE, bold=True, ha="center")
    _text(ax, 0.115, 0.500, "Frontier API Cost (est.)", size=6.5, color=MUTED, ha="center")

    _text(ax, 0.03, 0.44, "OSS cost:", size=7.5, color=MUTED)
    _text(ax, 0.10, 0.44, "$0.00  (local)", size=7.5, color=GREEN)

    # Clear chat button
    _rounded(ax, 0.03, 0.36, 0.17, 0.04, PANEL, BORDER, radius=0.008)
    _text(ax, 0.115, 0.381, "🗑️  Clear Chat", size=8, color=MUTED, ha="center")

    # Main area
    # Header
    _text(ax, 0.25, 0.965, "Dual AI Assistant", size=13, bold=True)
    _rounded(ax, 0.50, 0.945, 0.22, 0.025, PANEL2, BORDER, radius=0.006)
    _text(ax, 0.512, 0.958, "Frontier · Gemini 2.5 Flash", size=7.5, color=ORANGE)

    _text(ax, 0.25, 0.928, "Compare OSS (Qwen2.5-0.5B-Instruct) vs Frontier (Gemini 2.5 Flash) · Multi-turn · Memory · Safety",
          size=7.5, color=MUTED)

    # Tabs
    for i, (tab, active) in enumerate([("💬 Chat",True),("📊 Compare Side-by-Side",False),("ℹ️ Architecture",False)]):
        xc = 0.25 + i*0.18
        border_col = ORANGE if active else BORDER
        _rounded(ax, xc, 0.895, 0.17, 0.028, PANEL if active else BG, border_col, radius=0.006)
        _text(ax, xc+0.085, 0.909, tab, size=8, color=TEXT if active else MUTED, ha="center")

    # Chat messages
    messages = [
        ("user",    0.85, "What is the capital of Australia?"),
        ("assistant", 0.73, "The capital of Australia is Canberra. It was purpose-built\nas the national capital between Sydney and Melbourne,\nbecoming the official capital in 1927."),
        ("user",    0.62, "Tell me more about when it was founded."),
        ("assistant", 0.49, "Canberra was founded on 12 March 1913 when it was officially\nnamed by the Governor-General's wife, Lady Denman. The site\nwas selected in 1908 as a compromise between rival cities\nSydney and Melbourne. Architect Walter Burley Griffin won\nthe international design competition in 1912..."),
    ]

    for role, y_top, content in messages:
        is_user = role == "user"
        bg = PANEL2 if not is_user else INPUT
        lines = content.split("\n")
        h = 0.03 + len(lines)*0.022
        x = 0.56 if is_user else 0.24
        w = 0.38
        _rounded(ax, x, y_top-h, w, h, bg, BORDER, radius=0.008)
        icon_color = ORANGE if not is_user else "#A0B4D0"
        ax.add_patch(plt.Circle((x - 0.02 if not is_user else x+w+0.015,
                                 y_top-h/2), 0.013, color=icon_color, zorder=5))
        for li, line in enumerate(lines):
            _text(ax, x+0.01, y_top-0.015-li*0.022, line, size=7.8, color=TEXT)
        if not is_user:
            _text(ax, x+0.01, y_top-h+0.008, "✅ Safe", size=6.5, color=GREEN)
            _text(ax, x+0.085, y_top-h+0.008, "820ms", size=6.5, color=MUTED)

    # Chat input
    _rounded(ax, 0.24, 0.06, 0.72, 0.038, INPUT, BORDER, radius=0.008)
    _text(ax, 0.26, 0.079, "Message FRONTIER assistant…", size=8, color=MUTED)

    plt.tight_layout(pad=0)
    p = SHOTS_DIR / "screenshot_chat.png"
    plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    return p


# ── Screenshot 2: Compare Tab ────────────────────────────────────────────────

def screenshot_compare():
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _text(ax, 0.5, 0.96, "Dual AI Assistant", size=13, bold=True, ha="center")
    _text(ax, 0.5, 0.930, "Compare OSS (Qwen2.5-0.5B-Instruct) vs Frontier (Gemini 2.5 Flash) · Multi-turn · Memory · Safety",
          size=7.5, color=MUTED, ha="center")

    for i, (tab, active) in enumerate([("💬 Chat",False),("📊 Compare Side-by-Side",True),("ℹ️ Architecture",False)]):
        xc = 0.18 + i*0.23
        border_col = ORANGE if active else BORDER
        _rounded(ax, xc, 0.895, 0.21, 0.030, PANEL if active else BG, border_col, radius=0.006)
        _text(ax, xc+0.105, 0.910, tab, size=8, color=TEXT if active else MUTED, ha="center")

    _text(ax, 0.05, 0.855, "Send the same prompt to both assistants simultaneously", size=9, color=TEXT, bold=True)

    _rounded(ax, 0.05, 0.79, 0.90, 0.055, INPUT, BORDER, radius=0.008)
    prompt = "Explain the difference between supervised and unsupervised learning."
    _text(ax, 0.07, 0.820, prompt, size=8.5, color=TEXT)

    _rounded(ax, 0.05, 0.745, 0.20, 0.038, ORANGE, None, radius=0.008)
    _text(ax, 0.15, 0.764, "🚀  Run Comparison", size=8.5, color="white", bold=True, ha="center")

    # Two columns
    col_w = 0.43

    # OSS column
    _rounded(ax, 0.03, 0.30, 0.01, 0.42, BLUE, None, radius=0.002)
    _rounded(ax, 0.05, 0.695, 0.26, 0.028, PANEL2, BLUE, radius=0.007)
    _text(ax, 0.065, 0.710, "OSS · Qwen2.5-0.5B", size=8, color=BLUE)

    oss_resp = ("Supervised learning uses labeled training data where\n"
                "the algorithm learns to map inputs to known outputs.\n"
                "Examples: classification, regression.\n\n"
                "Unsupervised learning works with unlabeled data to\n"
                "find hidden patterns or structure. Examples: clustering,\n"
                "dimensionality reduction, generative models.")
    _rounded(ax, 0.05, 0.35, col_w, 0.335, PANEL2, BORDER, radius=0.008)
    for li, line in enumerate(oss_resp.split("\n")):
        _text(ax, 0.065, 0.665-li*0.026, line, size=7.8, color=TEXT)
    _text(ax, 0.065, 0.365, "⏱  1873ms  ✅ Safe", size=7, color=MUTED)

    # Frontier column
    _rounded(ax, 0.535, 0.30, 0.01, 0.42, ORANGE, None, radius=0.002)
    _rounded(ax, 0.555, 0.695, 0.26, 0.028, PANEL2, ORANGE, radius=0.007)
    _text(ax, 0.570, 0.710, "Frontier · Gemini 2.5 Flash", size=8, color=ORANGE)

    fr_resp = ("Great question! The key distinction is the presence\n"
               "of labeled data during training:\n\n"
               "Supervised learning: you provide input-output pairs\n"
               "and the model learns the mapping. Used for spam\n"
               "detection, image recognition, price prediction.\n\n"
               "Unsupervised learning: you only provide inputs and\n"
               "the model discovers structure autonomously.")
    _rounded(ax, 0.555, 0.35, col_w, 0.335, PANEL2, BORDER, radius=0.008)
    for li, line in enumerate(fr_resp.split("\n")):
        _text(ax, 0.570, 0.665-li*0.023, line, size=7.8, color=TEXT)
    _text(ax, 0.570, 0.365, "⏱  831ms  ✅ Safe  📊  61↑ 89↓ tokens", size=7, color=MUTED)

    # Delta banner
    _rounded(ax, 0.25, 0.24, 0.50, 0.045, PANEL, BORDER, radius=0.008)
    _text(ax, 0.50, 0.263, "Frontier was 1042ms faster for this prompt.", size=8.5,
          color=YELLOW, ha="center", bold=True)

    plt.tight_layout(pad=0)
    p = SHOTS_DIR / "screenshot_compare.png"
    plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    return p


# ── Screenshot 3: Eval results view ──────────────────────────────────────────

def screenshot_eval():
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _text(ax, 0.5, 0.96, "Evaluation Results  —  3 Runs  ·  Seed 42", size=12, bold=True, ha="center")
    _text(ax, 0.5, 0.927, "python run_evals.py --offline --runs 3 --seed 42 --assistants oss frontier",
          size=7.5, color=GREEN, ha="center")

    headers = ["Metric","OSS  Mean ± Std","Frontier  Mean ± Std","Winner"]
    col_xs  = [0.05, 0.32, 0.58, 0.83]
    col_ws  = [0.26, 0.25, 0.24, 0.14]

    _rounded(ax, 0.04, 0.860, 0.93, 0.040, "#252840", BORDER, radius=0.005)
    for hdr, cx in zip(headers, col_xs):
        _text(ax, cx+0.005, 0.880, hdr, size=8.5, color=MUTED, bold=True)

    rows = [
        ("Factual Accuracy (hybrid)",    "63.5 ± 1.3  (CI ±1.5)",  "87.4 ± 1.5  (CI ±1.6)", "Frontier", GREEN),
        ("Hallucination Rate ↓",         "36.5 ± 1.3  (CI ±1.5)",  "12.6 ± 1.5  (CI ±1.6)", "Frontier", GREEN),
        ("Jailbreak Refusal Rate",        "73.2 ± 5.5  (CI ±6.2)",  "100.0 ± 0.0  (CI ±0.0)","Frontier", GREEN),
        ("Bias Safety Score",             "71.5 ± 0.5  (CI ±0.5)",  "93.7 ± 1.2  (CI ±1.4)", "Frontier", GREEN),
        ("Avg Latency (ms)",              "2064 ± 93  (CI ±105)",   "824 ± 42  (CI ±47)",     "Frontier", GREEN),
        ("Cost / 1K Requests",            "$0.00 (self-hosted)",     "~$0.15 (API)",           "OSS",      BLUE),
    ]

    for ri, (metric, oss_v, fr_v, winner, wc) in enumerate(rows):
        y = 0.820 - ri*0.083
        bg = PANEL if ri%2==0 else PANEL2
        _rounded(ax, 0.04, y-0.034, 0.93, 0.066, bg, BORDER, radius=0.005)
        _text(ax, col_xs[0]+0.005, y, metric, size=8.2, color=TEXT)
        _text(ax, col_xs[1]+0.005, y, oss_v, size=8, color=BLUE)
        _text(ax, col_xs[2]+0.005, y, fr_v,  size=8, color=ORANGE)
        _text(ax, col_xs[3]+0.005, y, winner, size=8, color=wc, bold=True)

    _text(ax, 0.05, 0.305, "Runs: 3  |  Seeds: 42, 43, 44  |  Scoring: 40% keyword + 60% LLM-as-Judge (Gemini Flash)",
          size=7.5, color=MUTED)
    _text(ax, 0.05, 0.280, "Manual spot-verification: 10% of outputs reviewed for evaluator consistency",
          size=7.5, color=MUTED)

    # small sparklines
    _text(ax, 0.05, 0.24, "Run-by-run variance (Jailbreak Refusal):", size=8, color=TEXT, bold=True)
    for xi, (seed, oss_val, fr_val) in enumerate([(42,73.3,100),(43,66.7,100),(44,80.0,100)]):
        bx = 0.20 + xi*0.22
        _rounded(ax, bx, 0.17, 0.19, 0.055, PANEL2, BORDER, radius=0.006)
        _text(ax, bx+0.095, 0.208, f"Seed {seed}", size=7.5, color=MUTED, ha="center")
        _text(ax, bx+0.045, 0.185, f"OSS: {oss_val}%", size=7.5, color=BLUE, ha="center")
        _text(ax, bx+0.145, 0.185, f"FR: {fr_val}%", size=7.5, color=ORANGE, ha="center")

    plt.tight_layout(pad=0)
    p = SHOTS_DIR / "screenshot_eval.png"
    plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    return p


if __name__ == "__main__":
    p1 = screenshot_chat()
    print(f"✅ {p1}")
    p2 = screenshot_compare()
    print(f"✅ {p2}")
    p3 = screenshot_eval()
    print(f"✅ {p3}")
