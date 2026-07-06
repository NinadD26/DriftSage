terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

resource "local_file" "demo_config" {
  filename = "${path.module}/demo_config.txt"
  content  = "environment=production\nreplica_count=3\nfeature_flag=stable\n"
}
