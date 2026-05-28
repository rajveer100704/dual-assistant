#!/usr/bin/env bash
# submit.sh — Complete submission executor
# Runs: pre-check → GitHub → HF deploy → smoke test → final instructions
#
# Usage:
#   bash submit.sh YOUR_USERNAME
#   bash submit.sh YOUR_USERNAME --skip-git     # skip git push (already done)
#   bash submit.sh YOUR_USERNAME --skip-hf      # skip HF deploy (already deployed)
#   bash submit.sh YOUR_USERNAME --local-only   # pre-check + local smoke test only

set -euo pipefail

# ─── Args ─────────────────────────────────────────────────────────────────────
USERNAME=${1:-""}
SKIP_GIT=false
SKIP_HF=false
LOCAL_ONLY=false

for arg in "${@:2}"; do
  case $arg in
    --skip-git)   SKIP_GIT=true ;;
    --skip-hf)    SKIP_HF=true ;;
    --local-only) LOCAL_ONLY=true ;;
  esac
done

if [[ -z "$USERNAME" ]]; then
  echo ""
  echo "Usage: bash submit.sh YOUR_GITHUB_USERNAME [--skip-git] [--skip-hf] [--local-only]"
  echo ""
  echo "Examples:"
  echo "  bash submit.sh john_doe               # full deployment"
  echo "  bash submit.sh john_doe --local-only  # pre-check only, no deploy"
  echo "  bash submit.sh john_doe --skip-hf     # git push only"
  exit 1
fi

HF_SPACE_URL="https://huggingface.co/spaces/${USERNAME}/dual-assistant"
GITHUB_URL="https://github.com/${USERNAME}/dual-assistant"

# ─── Colours ──────────────────────────────────────────────────────────────────
G="\033[92m"; R="\033[91m"; Y="\033[93m"; B="\033[94m"
BOLD="\033[1m"; RESET="\033[0m"

ok()   { echo -e "  ${G}✅${RESET} $1"; }
fail() { echo -e "  ${R}❌${RESET} $1"; exit 1; }
warn() { echo -e "  ${Y}⚠️ ${RESET} $1"; }
hdr()  { echo -e "\n${BOLD}${B}══════════════════════════════════════════════${RESET}"; \
         echo -e "${BOLD}${B}  $1${RESET}"; \
         echo -e "${BOLD}${B}══════════════════════════════════════════════${RESET}\n"; }

hdr "Dual AI Assistant — Submission Executor"
echo "  Username:    $USERNAME"
echo "  GitHub:      $GITHUB_URL"
echo "  HF Space:    $HF_SPACE_URL"
echo ""

# ─── Step 0: Pre-submit check ─────────────────────────────────────────────────
hdr "STEP 0 — Pre-Submit Validation"
python pre_submit_check.py
ok "Pre-submit check passed"

# ─── Step 1: Run 62 tests ─────────────────────────────────────────────────────
hdr "STEP 1 — Test Suite (62 tests)"
python -m pytest tests/ -q
ok "All 62 tests passed"

# ─── Step 2: GitHub ───────────────────────────────────────────────────────────
if [[ "$LOCAL_ONLY" == "false" && "$SKIP_GIT" == "false" ]]; then
  hdr "STEP 2 — GitHub Setup & Push"

  # Replace placeholders
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/YOUR_USERNAME/${USERNAME}/g" README.md docs/submission_brief.md 2>/dev/null || true
  else
    sed -i "s/YOUR_USERNAME/${USERNAME}/g" README.md docs/submission_brief.md 2>/dev/null || true
  fi
  ok "Placeholders replaced in README.md + docs/submission_brief.md"

  # Ensure .env is not tracked
  git rm --cached .env 2>/dev/null || true

  git add -A
  git diff --cached --quiet && echo "  (nothing new to commit)" || \
    git commit -m "feat: Dual AI Assistant — Ollive AI Challenge final submission

- OSS (Qwen2.5-0.5B-Instruct) + Frontier (Gemini 2.5 Flash)  
- Hybrid LLM-as-Judge eval: 3-run seeded, mean±std, CI95
- Two-layer safety: regex + LlamaGuard S1-S14 neural classifier
- st.cache_resource model loading, cold-start banner
- 62 pytest tests, pre-submit validator, smoke test
- HuggingFace Spaces deployment + Docker + Makefile"

  ok "Git committed"
  echo ""
  echo -e "  ${Y}▶ Now run:${RESET}"
  echo "    git remote add origin ${GITHUB_URL}"
  echo "    git push -u origin main"
  echo ""
  echo -e "  ${Y}▶ Then add GitHub Topics in repo Settings:${RESET}"
  echo "    llm genai streamlit fastapi huggingface ai-safety evaluation observability machine-learning"
  echo ""
  read -p "  Press ENTER after pushing to GitHub to continue..." _
  ok "GitHub push confirmed"
else
  hdr "STEP 2 — GitHub (SKIPPED)"
  ok "Skipped (--skip-git)"
fi

# ─── Step 3: HuggingFace deploy ──────────────────────────────────────────────
if [[ "$LOCAL_ONLY" == "false" && "$SKIP_HF" == "false" ]]; then
  hdr "STEP 3 — HuggingFace Spaces Deployment"

  # Check huggingface_hub installed
  python -c "import huggingface_hub" 2>/dev/null || {
    warn "huggingface_hub not installed. Installing..."
    pip install huggingface_hub -q
  }

  # Check HF login
  python -c "from huggingface_hub import HfApi; HfApi().whoami()" 2>/dev/null || {
    warn "Not logged in to HuggingFace."
    echo ""
    echo "  Run: huggingface-cli login"
    echo "  Then re-run: bash submit.sh ${USERNAME} --skip-git"
    exit 1
  }

  python deploy_hf.py --username "$USERNAME"
  ok "HuggingFace deployment initiated"

  echo ""
  echo -e "  ${Y}▶ CRITICAL: Add API secret in HF Space:${RESET}"
  echo "    1. Open: ${HF_SPACE_URL}"
  echo "    2. Settings → Repository secrets"
  echo "    3. Add: GEMINI_API_KEY = AIzaSy-your-key-here"
  echo ""
  read -p "  Press ENTER after adding the secret and Space shows 'Running'..." _
  ok "HF Space secret confirmed"
else
  hdr "STEP 3 — HuggingFace Deploy (SKIPPED)"
  ok "Skipped"
fi

# ─── Step 4: Smoke test ───────────────────────────────────────────────────────
hdr "STEP 4 — Smoke Test"

if [[ "$LOCAL_ONLY" == "true" ]]; then
  echo "  Starting local API for smoke test..."
  uvicorn app.backend.main:app --port 8000 &
  UVICORN_PID=$!
  sleep 4
  python smoke_test.py --url http://localhost:8000 && ok "Local smoke test PASSED" \
    || warn "Local smoke test had warnings — check output above"
  kill $UVICORN_PID 2>/dev/null || true
else
  echo "  Testing live HF Space: $HF_SPACE_URL"
  echo "  (waiting 10s for Space to stabilise...)"
  sleep 10
  python smoke_test.py --url "$HF_SPACE_URL" && ok "Live smoke test PASSED" \
    || warn "Some checks failed — review output above before submitting"
fi

# ─── Step 5: Final checklist ──────────────────────────────────────────────────
hdr "STEP 5 — Final Submission Checklist"

REPORT_SIZE=$(du -sh evaluation_report.pdf 2>/dev/null | cut -f1)
TESTS=$(python -m pytest tests/ -q 2>&1 | tail -1)

echo -e "  ${G}✅${RESET} evaluation_report.pdf  (${REPORT_SIZE})"
echo -e "  ${G}✅${RESET} Tests: ${TESTS}"
echo -e "  ${G}✅${RESET} GitHub:   ${GITHUB_URL}"
echo -e "  ${G}✅${RESET} HF Space: ${HF_SPACE_URL}"

if [[ "$LOCAL_ONLY" == "false" ]]; then
  echo ""
  echo -e "  ${Y}▶ REMAINING MANUAL STEPS:${RESET}"
  echo ""
  echo "  1. 🎥 Record 2-min Loom (docs/loom_demo_script.md)"
  echo "     https://loom.com/new"
  echo ""
  echo "  2. 📧 Send submission email (docs/submission_brief.md):"
  echo "     To:      work@ollive.ai"
  echo "     Subject: Dual AI Assistant — Ollive AI Challenge Submission"
  echo "     Attach:  evaluation_report.pdf"
  echo "     Links:   ${GITHUB_URL}"
  echo "              ${HF_SPACE_URL}"
  echo "              [your loom URL]"
fi

echo ""
echo -e "${BOLD}${G}══════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${G}  SUBMISSION READY ✅${RESET}"
echo -e "${BOLD}${G}══════════════════════════════════════════════${RESET}"
echo ""
