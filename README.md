# DriftSage

AI-powered Terraform drift detection. Runs a refresh-only Terraform plan, detects any changes made outside Terraform, sends the drift to an LLM (Groq) for severity/risk analysis, and generates a ready-to-review remediation script — all wired into a CI/CD pipeline.

## Problem

Infrastructure drifts from its Terraform-defined state all the time — a manual console tweak, an emergency hotfix, an out-of-band script. Left unnoticed, drift causes the next `terraform apply` to behave unpredictably, and nobody remembers *why* a resource looks different from code.

## What it does

1. Runs `terraform plan -refresh-only` against a working directory
2. Parses Terraform's `resource_drift` output (the actual out-of-band changes — not the plan's proposed actions)
3. Sends the drift to an LLM for analysis: severity, likely intent, risk, plain-language explanation, and a suggested Terraform remediation script
4. Saves the analysis + remediation script to `reports/`, tagged with the commit SHA, and prints a plain-language summary straight to the console/CI log
5. Runs on a schedule (or on demand) via GitHub Actions, uploading each run's report as a downloadable artifact

## Architecture

```
terraform plan -refresh-only
        │
        ▼
terraform_runner.py  ──►  drift.json (resource_drift)
        │
        ▼
drift_parser.py  ──►  structured DriftChange objects
        │
        ▼
groq_analyzer.py  ──►  LLM analysis (severity, risk, remediation)
        │
        ▼
remediation_generator.py  ──►  reports/analysis_<sha>.json
                               reports/remediation_<sha>.sh
                               + console summary
```

## Tech stack

- Python 3.12, Pydantic (data modeling)
- Terraform (refresh-only plans, JSON output)
- Groq API (Llama 3.3 70B) for drift analysis — OpenAI-compatible client
- GitHub Actions for scheduled/on-demand CI
- Docker for containerized runs

## Local setup

```bash
python -m venv venv
source venv/bin/activate      # or venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

cp .env.example .env           # add your GROQ_API_KEY

cd terraform
terraform init
terraform apply -auto-approve  # establishes baseline (local-only demo resource, no cloud account needed)
cd ..
```

Simulate drift and run a scan:

```bash
echo "changed_outside_terraform=true" >> terraform/demo_config.txt
python app/main.py
```

Check `reports/analysis.json` and `reports/remediation.sh` for the result, or just read the console output — it's printed there too.

## Docker

```bash
docker build -t driftsage .
docker run --rm --env-file .env -v $(pwd)/terraform:/app/terraform driftsage
```

## CI/CD

The included GitHub Actions workflow (`.github/workflows/drift-scan.yml`):
- Triggers manually (`workflow_dispatch`) or daily on a schedule
- Spins up Terraform + Python, applies the baseline, simulates drift, runs the scan
- Uploads `reports/` as a build artifact named with the commit SHA, so every run's results are traceable

Requires a `GROQ_API_KEY` repository secret (Settings → Secrets and variables → Actions).

## Notes

- The demo uses Terraform's `local_file` provider so anyone can run this without an AWS/cloud account.
- To point this at real infrastructure, update `config/config.yaml`'s `working_dir` to a real Terraform project — the drift-detection logic is provider-agnostic.
