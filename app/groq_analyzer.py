import json
import os
from openai import OpenAI


class GroqAnalyzer:

    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = os.environ.get(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile"
        )

    def analyze(self, drift):

        prompt = f"""
You are a Senior AWS Terraform Engineer.

Analyze the following drift.

Return JSON ONLY, with exactly these keys:
severity, intent, risk, explanation, remediation_script

Rules for "remediation_script":
- It MUST be a valid, directly executable bash script.
- It MUST start with "#!/bin/bash".
- It MUST use real terraform CLI commands only
  (e.g. terraform apply -target=..., terraform import ...).
- NEVER put raw HCL/Terraform resource blocks in this field.

Example of a correctly formatted remediation_script value:
"#!/bin/bash\\nterraform apply -target=local_file.demo_config -auto-approve\\n"

Drift:

{json.dumps(drift, indent=2)}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )

        return response.choices[0].message.content
