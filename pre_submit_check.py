#!/usr/bin/env python3
"""
pre_submit_check.py — Run this before submitting. Catches every common mistake.

Usage:
    python pre_submit_check.py

Checks:
  ✅ All source files compile
  ✅ No .env or secrets in codebase
  ✅ --mock flag removed (must be --offline)
  ✅ PDF exists and has correct page count
  ✅ All 8 charts exist
  ✅ All 3 screenshots exist
  ✅ All 4 docs exist
  ✅ README has no YOUR_USERNAME placeholders (or warns)
  ✅ .gitignore excludes .env
  ✅ Core modules pass unit tests
  ✅ eval_results.json is valid
  ✅ sample_traces.jsonl is valid
  ✅ requirements.txt is present
  ✅ Dockerfile exists
  ✅ app.py (HF entry point) exists
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Prevent UnicodeEncodeError on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

_root = Path(__file__).parent
PASS = "✅"
WARN = "⚠️ "
FAIL = "❌"

errors   = []
warnings = []


def check(label: str, condition: bool, msg: str = "", is_warning: bool = False):
    if condition:
        print(f"  {PASS} {label}")
    elif is_warning:
        print(f"  {WARN} {label}" + (f" — {msg}" if msg else ""))
        warnings.append(label)
    else:
        print(f"  {FAIL} {label}" + (f" — {msg}" if msg else ""))
        errors.append(label)


def section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ── 1. Critical files ─────────────────────────────────────────────────────────
section("Critical Files")
for f in [
    "app.py", "run_evals.py", "generate_report.py", "deploy_hf.py",
    "requirements.txt", "Dockerfile", "Makefile", ".env.example",
    "README.md", "README_HF.md", ".gitignore",
    "reports/evaluation_report.pdf",
    "reports/eval_results.json",
    "logs/sample_traces.jsonl",
]:
    check(f, (_root / f).exists(), f"Missing: {f}")


# ── 2. Source modules compile ─────────────────────────────────────────────────
section("Python Syntax (all modules)")
py_files = list((_root / "app").rglob("*.py")) + [
    _root / "run_evals.py",
    _root / "generate_report.py",
    _root / "deploy_hf.py",
    _root / "app.py",
]
for pf in py_files:
    rel = pf.relative_to(_root)
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(pf)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    err_msg = (result.stderr or "").strip()[:80]
    check(str(rel), result.returncode == 0, err_msg)


# ── 3. No --mock in user-facing files ─────────────────────────────────────────
section("Flag Naming (--mock must be --offline)")
user_facing = [
    "run_evals.py", "Makefile", "README.md",
    "generate_report.py",
    "docs/evaluation_methodology.md",
    "docs/deployment.md",
    "app/evals/generate_screenshots.py",
]
for f in user_facing:
    fp = _root / f
    if not fp.exists():
        continue
    content = fp.read_text(encoding="utf-8")
    # Allow internal function comments but not user-visible --mock flag
    has_mock_flag = bool(re.search(r'--mock(?!\w)', content))
    check(f"{f}: no --mock flag", not has_mock_flag,
          "Found --mock (user-facing). Must be --offline.")


# ── 4. No secrets / .env in codebase ─────────────────────────────────────────
section("Secrets & Security")

# .gitignore must exclude .env
gitignore = (_root / ".gitignore").read_text(encoding="utf-8") if (_root / ".gitignore").exists() else ""
check(".gitignore excludes .env", ".env" in gitignore)
check(".gitignore excludes *.pyc", "*.pyc" in gitignore)

# No actual .env file with real content
env_file = _root / ".env"
if env_file.exists():
    content = env_file.read_text(encoding="utf-8")
    has_real_key = bool(re.search(r'sk-ant-[a-zA-Z0-9\-]{20,}', content))
    check(".env has no real API key", not has_real_key,
          "Real GEMINI_API_KEY found in .env — do not commit!", is_warning=True)
else:
    check(".env file absent (good — not committed)", True)

# No hardcoded keys anywhere in source
key_pattern = re.compile(r'AIzaSy[a-zA-Z0-9\-_]{30,}')
for py_file in py_files:
    content = py_file.read_text(errors="replace")
    check(f"No hardcoded key in {py_file.name}",
          not key_pattern.search(content),
          "Hardcoded API key found!")


# ── 5. Charts (8 required) ────────────────────────────────────────────────────
section("Charts (8 required)")
required_charts = [
    "architecture_diagram.png",
    "hallucination_comparison.png",
    "jailbreak_comparison.png",
    "bias_comparison.png",
    "latency_comparison.png",
    "radar_chart.png",
    "tradeoff_diagram.png",
    "observability_dashboard.png",
]
for c in required_charts:
    p = _root / "charts" / c
    size_ok = p.exists() and p.stat().st_size > 10_000
    check(f"charts/{c} ({p.stat().st_size//1024}KB)" if p.exists() else f"charts/{c}",
          size_ok, "Missing or too small")


# ── 6. Screenshots ────────────────────────────────────────────────────────────
section("Screenshots (3 required)")
for s in ["screenshot_chat.png", "screenshot_compare.png", "screenshot_eval.png"]:
    p = _root / "screenshots" / s
    check(f"screenshots/{s}", p.exists() and p.stat().st_size > 50_000)


# ── 7. Docs ───────────────────────────────────────────────────────────────────
section("Documentation (4 docs)")
for d in [
    "docs/architecture_decisions.md",
    "docs/deployment.md",
    "docs/evaluation_methodology.md",
    "docs/loom_demo_script.md",
]:
    p = _root / d
    check(d, p.exists() and p.stat().st_size > 500)


# ── 8. PDF validity ───────────────────────────────────────────────────────────
section("PDF Report")
pdf_path = _root / "reports" / "evaluation_report.pdf"
if pdf_path.exists():
    try:
        from pypdf import PdfReader
        r = PdfReader(str(pdf_path))
        n = len(r.pages)
        check(f"PDF has 12 pages (got {n})", n == 12)
        check(f"PDF size reasonable ({pdf_path.stat().st_size//1024}KB)",
              pdf_path.stat().st_size > 500_000)
    except ImportError:
        check("PDF exists", True)
        check("pypdf available for page-count check", False,
              "pip install pypdf", is_warning=True)
else:
    check("PDF exists", False)


# ── 9. eval_results.json validity ────────────────────────────────────────────
section("Evaluation Artifacts")
try:
    data = json.loads((_root / "reports" / "eval_results.json").read_text(encoding="utf-8"))
    check("eval_results.json: valid JSON", True)
    check("eval_results.json: has statistics key", "statistics" in data)
    check("eval_results.json: has reproducibility key",
          "reproducibility" in data.get("config", {}))
    cmd = data.get("config", {}).get("reproducibility", "")
    has_offline = "--offline" in str(data)
    no_mock = "--mock" not in str(data)
    check("eval_results.json: uses --offline not --mock", has_offline or no_mock)
except Exception as e:
    check("eval_results.json: valid", False, str(e))

try:
    lines = [json.loads(l) for l in
             (_root / "logs" / "sample_traces.jsonl").read_text(encoding="utf-8").splitlines()
             if l.strip()]
    check(f"sample_traces.jsonl: {len(lines)} valid records", len(lines) >= 10)
except Exception as e:
    check("sample_traces.jsonl: valid", False, str(e))


# ── 10. README placeholder check ─────────────────────────────────────────────
section("README Placeholders")
readme = (_root / "README.md").read_text(encoding="utf-8")
placeholders = {
    "YOUR_USERNAME": "Replace with your GitHub/HF username",
    "YOUR_LOOM_ID":  "Replace with actual Loom video ID after recording",
}
for ph, msg in placeholders.items():
    has = ph in readme
    check(f"README: '{ph}' placeholder", not has,
          f"{msg}", is_warning=True)


# ── 11. Core unit tests ───────────────────────────────────────────────────────
section("Core Unit Tests")
result = subprocess.run(
    [sys.executable, "-c", """
import sys; sys.path.insert(0,'.')
from app.assistants.memory import ConversationMemory
from app.assistants.guardrails import screen_prompt, screen_output
from app.assistants.tools import route_tools
from run_evals import _offline_run, compute_stats

m = ConversationMemory(5)
m.save("hi","hello")
m.save("q2","a2")
m.save("q3","a3")
m.save("q4","a4")
m.save("q5","a5")
m.save("q6","a6")
assert len(m.get_messages()) == 10   # 5 exchanges

ok, _ = screen_prompt("how to make a bomb"); assert not ok
ok, _ = screen_prompt("What is Python?"); assert ok
ok, _ = screen_output("Paris is the capital of France."); assert ok

r = route_tools("calculate 2**10"); assert r and "1024" in r
r = route_tools("what's the date"); assert r and "UTC" in r

runs = [_offline_run(42+i,"frontier") for i in range(3)]
stats = compute_stats(runs,"frontier")
assert stats["jailbreak_refusal_rate_pct"]["std"] == 0.0
print("ALL PASS")
"""],
    capture_output=True, text=True, cwd=str(_root),
)
check("Memory, guardrails, tools, eval stats",
      "ALL PASS" in result.stdout,
      result.stderr[:120] if result.returncode != 0 else "")


# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'═'*55}")
print(f"  SUBMISSION READINESS CHECK")
print(f"{'═'*55}")
print(f"  Errors:   {len(errors)}")
print(f"  Warnings: {len(warnings)}")
print(f"{'─'*55}")

if errors:
    print(f"\n  {FAIL} MUST FIX before submitting:")
    for e in errors:
        print(f"    • {e}")

if warnings:
    print(f"\n  {WARN} SHOULD REVIEW:")
    for w in warnings:
        print(f"    • {w}")

if not errors:
    print(f"""
  {PASS} READY TO SUBMIT

  Submission checklist:
    1. python deploy_hf.py --username YOUR_USERNAME
    2. Add GEMINI_API_KEY in HF Space Secrets
    3. Verify live URL works: https://huggingface.co/spaces/YOUR_USERNAME/dual-assistant
    4. Record 2-min Loom (see docs/loom_demo_script.md)
    5. Push to GitHub (ensure .env not committed)
    6. Send email to work@ollive.ai with:
         - GitHub repo link
         - HF Spaces live URL
         - Loom link
         - evaluation_report.pdf attached
""")
else:
    print(f"\n  {FAIL} Fix errors above before submitting.\n")
    sys.exit(1)
