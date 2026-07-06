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

    tf = TerraformRunner(
        config["terraform"]["working_dir"]
    )

    print("Running terraform scan")

    plan = tf.generate_plan()

    drift = DriftParser.parse(plan)

    if not drift:
        print("No drift detected")
        return

    analyzer = GroqAnalyzer()

    result = analyzer.analyze(
        [d.model_dump() for d in drift]
    )

    os.environ["GIT_COMMIT_SHA"] = resolve_commit_sha()

    RemediationGenerator.save(result)

    print(
        "Analysis saved in reports/"
    )


if __name__ == "__main__":
    main()
