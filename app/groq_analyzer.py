import json
import os
from openai import OpenAI


class GroqAnalyzer:

    def __init__(self, batch_size=15):
        self.client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = os.environ.get(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile"
        )
        self.batch_size = batch_size

    def _build_prompt(self, drift_batch):
        return f"""
You are a Senior Cloud/Terraform Engineer.

Analyze the following drift.

Return JSON ONLY, with exactly these keys:
severity, intent, risk, explanation, remediation_script

Rules for "remediation_script":
- It MUST be a valid, directly executable bash script.
- It MUST start with "#!/bin/bash".
- It MUST use real terraform CLI commands only
  (e.g. terraform apply -target=..., terraform import ...).
- NEVER put raw HCL/Terraform resource blocks in this field.
- If there are multiple drifted resources, include one
  targeted remediation command per resource.

Example of a correctly formatted remediation_script value:
"#!/bin/bash\\nterraform apply -target=local_file.demo_config -auto-approve\\n"

Drift:

{json.dumps(drift_batch, indent=2)}
"""

    def _chunk(self, drift):
        for i in range(0, len(drift), self.batch_size):
            yield drift[i:i + self.batch_size]

    def analyze(self, drift):
        """
        Returns a list of JSON-string results, one per batch.
        A single small drift set (<= batch_size) returns a
        list with exactly one result, so callers that expect
        one result can just take results[0].
        """

        results = []

        for batch in self._chunk(drift):

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": self._build_prompt(batch)
                    }
                ],
                response_format={"type": "json_object"},
            )

            results.append(
                response.choices[0].message.content
            )

        return results
