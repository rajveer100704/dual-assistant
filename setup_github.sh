#!/usr/bin/env bash
# setup_github.sh — One-command GitHub repo setup
# Usage: bash setup_github.sh YOUR_GITHUB_USERNAME

set -e

USERNAME=${1:-"rajveer100704"}
REPO="dual-assistant"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Dual AI Assistant — GitHub Setup"
echo "  Repo: https://github.com/$USERNAME/$REPO"
echo "═══════════════════════════════════════════════"
echo ""

# Replace placeholders in README and docs
echo "Replacing rajveer100704 with: $USERNAME"
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  sed -i '' "s/rajveer100704/$USERNAME/g" README.md
  sed -i '' "s/rajveer100704/$USERNAME/g" docs/submission_brief.md
else
  # Linux
  sed -i "s/rajveer100704/$USERNAME/g" README.md
  sed -i "s/rajveer100704/$USERNAME/g" docs/submission_brief.md
fi
echo "✅ Placeholders replaced"

# Git setup
git init
git add .
git commit -m "feat: Dual AI Assistant — Ollive AI Challenge

- OSS (Qwen2.5-0.5B-Instruct) + Frontier (Claude Sonnet)
- Hybrid LLM-as-Judge evaluation (3-run seeded, CI95)
- Two-layer safety: regex + LlamaGuard S1-S14 taxonomy
- Full observability traces + engineering tradeoff analysis
- HuggingFace Spaces deployment + Docker
- 62 pytest tests, pre-submission validator"

echo "✅ Git initialized + committed"
echo ""
echo "Next steps:"
echo "  1. Create repo at: https://github.com/new"
echo "     Name: $REPO | Public | No README"
echo ""
echo "  2. Push:"
echo "     git remote add origin https://github.com/$USERNAME/$REPO"
echo "     git push -u origin main"
echo ""
echo "  3. Deploy HF Space:"
echo "     python deploy_hf.py --username $USERNAME"
echo ""
echo "  4. Run smoke test:"
echo "     python smoke_test.py --url http://localhost:8000"
echo ""
echo "  5. Send email — see: docs/submission_brief.md"
