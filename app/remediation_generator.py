import json
import os
from pathlib import Path


class RemediationGenerator:

    @staticmethod
    def save(target_name, result_texts):
        """
        target_name: name of the Terraform target (from config)
        result_texts: list of JSON strings, one per analysis batch
        """

        sha = os.environ.get(
            "GIT_COMMIT_SHA",
            "local"
        )[:7]

        out_dir = Path("reports") / target_name
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n=== Drift Analysis Summary: {target_name} ===")
        print(f"Commit: {sha}")

        combined_scripts = ["#!/bin/bash"]
        all_data = []

        for i, result_text in enumerate(result_texts):

            data = json.loads(result_text)
            all_data.append(data)

            print(f"\n--- Batch {i + 1}/{len(result_texts)} ---")
            print(f"Severity:    {data['severity']}")
            print(f"Intent:      {data['intent']}")
            print(f"Risk:        {data['risk']}")
            print(f"Explanation: {data['explanation']}")
            print("Remediation:")
            print(data["remediation_script"])

            combined_scripts.append(
                data["remediation_script"].replace(
                    "#!/bin/bash", ""
                ).strip()
            )

        print(f"=== End of summary: {target_name} ===\n")

        remediation_text = "\n".join(combined_scripts) + "\n"

        with open(out_dir / "remediation.sh", "w") as f:
            f.write(remediation_text)
        with open(out_dir / f"remediation_{sha}.sh", "w") as f:
            f.write(remediation_text)

        with open(out_dir / "analysis.json", "w") as f:
            json.dump(all_data, f, indent=2)
        with open(out_dir / f"analysis_{sha}.json", "w") as f:
            json.dump(all_data, f, indent=2)
