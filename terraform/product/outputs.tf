# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "metadata" {
  description = "Metadata of the product module deployment."
  value = {
    version     = var.metadata_version
    risk        = var.risk
    deployed_at = terraform_data.deployed_at.output
    updated_at  = timestamp()
  }
}

output "models" {
  description = "Map of the model key to its model UUID and the components deployed in it."
  value = {
    backup = {
      model_uuid = var.model_uuid
      components = merge(
        { bacula_server = module.bacula_server.application },
        { for app in juju_application.postgresql : "postgresql" => app },
        { for app in juju_application.s3_integrator : "s3_integrator" => app },
      )
    }
  }
}

output "offers" {
  description = "Map of the offers exposed by the product module with their URLs."
  value = {
    bacula_dir = juju_offer.bacula_dir.url
  }
}
