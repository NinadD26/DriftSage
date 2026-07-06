import json
import os
from pathlib import Path


class RemediationGenerator:

    @staticmethod
    def save(result_text):

        data = json.loads(result_text)

        Path("reports").mkdir(
            exist_ok=True
        )

        # Short commit SHA, so each CI run's report is
        # traceable back to the exact code + drift snapshot.
        sha = os.environ.get(
            "GIT_COMMIT_SHA",
            "local"
        )[:7]

        # Print a plain-language summary to the console/CI log,
        # so results are visible without opening any file.
        print("\n=== Drift Analysis Summary ===")
        print(f"Commit:      {sha}")
        print(f"Severity:    {data['severity']}")
        print(f"Intent:      {data['intent']}")
        print(f"Risk:        {data['risk']}")
        print(f"Explanation: {data['explanation']}")
        print("\n--- Suggested remediation ---")
        print(data["remediation_script"])
        print("=== End of summary ===\n")

        # Always overwrite "latest" for convenience...
        with open(
            "reports/remediation.sh",
            "w"
        ) as f:
            f.write(data["remediation_script"])

        with open(
            "reports/analysis.json",
            "w"
        ) as f:
            json.dump(data, f, indent=2)

        # ...and also keep a commit-tagged copy for history.
        with open(
            f"reports/remediation_{sha}.sh",
            "w"
        ) as f:
            f.write(data["remediation_script"])

        with open(
            f"reports/analysis_{sha}.json",
            "w"
        ) as f:
            json.dump(data, f, indent=2)
