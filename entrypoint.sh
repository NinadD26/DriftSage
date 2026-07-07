#!/bin/bash
set -e

cd /app/terraform
terraform init
terraform apply -auto-approve
echo "changed_outside_terraform=true" >> demo_config.txt
cd /app

python app/main.py
