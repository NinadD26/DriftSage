import os
import subprocess
import yaml
from dotenv import load_dotenv

load_dotenv()

from terraform_runner import TerraformRunner
from drift_parser import DriftParser
from groq_analyzer import GroqAnalyzer
from remediation_generator import (
    RemediationGenerator
)


def resolve_commit_sha():
    # In CI, GitHub Actions already sets GITHUB_SHA.
    # Locally, fall back to the current git commit.
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "local"


def main():

    config = yaml.safe_load(
        open("config/config.yaml")
    )

    os.environ["GIT_COMMIT_SHA"] = resolve_commit_sha()

    batch_size = config.get("batch_size", 15)
    targets = config["targets"]

    for target in targets:

        name = target["name"]
        path = target["path"]

        print(f"\n>>> Scanning target: {name} ({path})")

        tf = TerraformRunner(path)

        tf.init()
        plan = tf.generate_plan()

        drift = DriftParser.parse(plan)

        if not drift:
            print(f"No drift detected for {name}")
            continue

        analyzer = GroqAnalyzer(batch_size=batch_size)

        results = analyzer.analyze(
            [d.model_dump() for d in drift]
        )

        RemediationGenerator.save(name, results)

    print("\nAll targets scanned. Reports saved in reports/")


if __name__ == "__main__":
    main()
