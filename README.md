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

Two workflows are included in `.github/workflows/`:

- **`drift-scan-demo.yml`** — self-contained local demo (no cloud account needed). Establishes a baseline, simulates drift, runs the scan. Good for showing the pipeline works end-to-end without any setup.
- **`drift-scan.yml`** — generic scan for real Terraform projects configured in `config/config.yaml`'s `targets` list. No drift simulation — it just detects whatever's actually drifted. See "Bring your own Terraform project" below for setup.

Both require a `GROQ_API_KEY` repository secret (Settings → Secrets and variables → Actions), and upload `reports/` as a build artifact named with the commit SHA.

## Bring your own Terraform project

DriftSage's core engine is provider- and scale-agnostic: it doesn't care whether a target is a single local-file demo resource, a single-module AWS project, or a multi-module production setup spanning hundreds of resources across ECS, Lambda, ALBs, and DocumentDB. Terraform itself handles the provider/backend specifics — DriftSage just runs `terraform init` + `terraform plan -refresh-only` against whatever directory you point it at, and parses whatever comes back.

**To add any Terraform project, real or demo, with zero code changes:**

Add an entry to `config/config.yaml`:

```yaml
targets:
  - name: local-demo
    path: ./terraform

  - name: my-production-project
    path: ./projects/my-production-project
```

Each target is scanned independently, and results are saved to `reports/<target-name>/`.

### Scaling to large, multi-module infrastructure

For projects with many resources (e.g. 200+ CloudWatch alarms across multiple ECS services, Lambda functions, and ALBs via reusable Terraform modules with `for_each`), two things matter:

- **Module-qualified resource addresses** (e.g. `module.ecs_alarms["service-name"].aws_cloudwatch_metric_alarm.x`) are handled automatically — `drift_parser.py` reads whatever address Terraform reports, regardless of module nesting.
- **Batching**: large drift sets are automatically chunked (`batch_size` in `config.yaml`, default 15) before being sent to the LLM, so this scales without hitting context/token limits or excessive cost, whether there's 1 drifted resource or 500.

### Running against real cloud infrastructure

1. Ensure the target directory's own `backend.tf`/provider blocks are already configured (S3+DynamoDB, GCS, Azure Storage, etc.) — DriftSage doesn't modify or assume backend config
2. Add cloud credentials as GitHub repo secrets (see `.github/workflows/drift-scan.yml` for AWS examples; swap for GCP/Azure equivalents as needed)
3. Use the `drift-scan.yml` workflow (not `drift-scan-demo.yml`, which is local-only and simulates drift for demo purposes) — it runs on a schedule with no drift-simulation step, since real infrastructure already has whatever drift naturally occurred since the last apply



- The demo uses Terraform's `local_file` provider so anyone can run this without an AWS/cloud account.
- To point this at real infrastructure, update `config/config.yaml`'s `working_dir` to a real Terraform project — the drift-detection logic is provider-agnostic.
