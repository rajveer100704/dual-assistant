# ─── Dual AI Assistant — Makefile ────────────────────────────────────────────
# Usage:
#   make setup       Install dependencies + create .env
#   make run         Launch Streamlit UI
#   make api         Launch FastAPI backend
#   make eval        Run evaluation suite (offline/cached, 3 runs, seed 42)
#   make eval-real   Run real evaluation (requires ANTHROPIC_API_KEY)
#   make report      Generate PDF report
#   make charts      Regenerate all charts
#   make docker      Build Docker image
#   make clean       Remove generated artifacts
#   make test        Run unit tests
#   make all         setup + eval + report (full pipeline)

.PHONY: setup run api eval eval-real report charts docker clean test all

PYTHON  := python3
PIP     := pip3
APP     := app/frontend/streamlit_app.py
PORT    := 8501

# ─── Setup ────────────────────────────────────────────────────────────────────
setup:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from template — add your ANTHROPIC_API_KEY"; fi
	@mkdir -p logs charts reports screenshots
	@echo "✅ Setup complete"

# ─── Run ──────────────────────────────────────────────────────────────────────
run:
	streamlit run $(APP) --server.port=$(PORT)

api:
	uvicorn app.backend.main:app --reload --port 8000

# ─── Evaluation ───────────────────────────────────────────────────────────────
eval:
	$(PYTHON) run_evals.py --offline --runs 3 --seed 42 --assistants oss frontier

eval-real:
	$(PYTHON) run_evals.py --runs 3 --seed 42 --assistants frontier

eval-oss:
	$(PYTHON) run_evals.py --runs 1 --seed 42 --assistants oss

# ─── Report & Charts ──────────────────────────────────────────────────────────
report:
	$(PYTHON) generate_report.py

charts:
	$(PYTHON) app/evals/architecture_diagram.py
	$(PYTHON) app/evals/tradeoff_diagram.py
	$(PYTHON) app/evals/observability_chart.py

# ─── Full pipeline ────────────────────────────────────────────────────────────
all: setup eval report
	@echo "✅ Full pipeline complete — open reports/evaluation_report.pdf"

# ─── Tests ────────────────────────────────────────────────────────────────────
test:
	$(PYTHON) -m pytest tests/ -v

# ─── Docker ───────────────────────────────────────────────────────────────────
docker:
	docker build -t dual-assistant:latest .

docker-run:
	docker run -p $(PORT):$(PORT) \
		-e ANTHROPIC_API_KEY=$${ANTHROPIC_API_KEY} \
		dual-assistant:latest

# ─── Clean ────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f logs/*.log
	@echo "✅ Cleaned"

clean-all: clean
	rm -f charts/*.png reports/*.pdf reports/*.json
	@echo "✅ Deep cleaned (charts + reports removed)"

# ─── Submission ───────────────────────────────────────────────────────────────
check:
	$(PYTHON) pre_submit_check.py

deploy:
	$(PYTHON) deploy_hf.py --username $(HF_USERNAME)

interview:
	@cat docs/interview_prep.md | head -80
	@echo "..."
	@echo "(full guide in docs/interview_prep.md)"

submit: check
	@echo ""
	@echo "✅ Pre-submission check passed."
	@echo "📧 Submission template in: docs/submission_brief.md"
	@echo "🎥 Loom script in: docs/loom_demo_script.md"
	@echo ""
	@echo "Final steps:"
	@echo "  1. make deploy HF_USERNAME=your_username"
	@echo "  2. Record Loom (docs/loom_demo_script.md)"
	@echo "  3. git push origin main"
	@echo "  4. Send email per docs/submission_brief.md"

smoke:
	$(PYTHON) smoke_test.py --url http://localhost:8000

github:
	@echo "Usage: bash setup_github.sh YOUR_GITHUB_USERNAME"
	@bash setup_github.sh $(USERNAME)

submit-full:
	@bash submit.sh $(USERNAME)

submit-local:
	@bash submit.sh $(USERNAME) --local-only

verify:
	$(PYTHON) local_verify.py
