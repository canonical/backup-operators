# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Captures the initial deployment timestamp once and keeps it stable across
# subsequent applies, for the "metadata.deployed_at" output.
resource "terraform_data" "deployed_at" {
  input = timestamp()

  lifecycle {
    ignore_changes = [input]
  }
}

module "bacula_server" {
  source = "../charm/bacula_server"

  app_name    = var.bacula_server.app_name
  base        = var.bacula_server.base
  channel     = local.bacula_server_channel
  config      = var.bacula_server.config
  constraints = var.bacula_server.constraints
  model_uuid  = var.model_uuid
  revision    = var.bacula_server.revision
  units       = var.bacula_server.units
}

resource "juju_application" "postgresql" {
  count = local.deploy_postgresql ? 1 : 0

  name       = var.postgresql.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "postgresql"
    channel  = local.postgresql_channel
    revision = var.postgresql.revision
    base     = var.postgresql.base
  }

  config      = var.postgresql.config
  constraints = var.postgresql.constraints
  units       = var.postgresql.units
}

resource "juju_application" "s3_integrator" {
  count = local.deploy_s3_integrator ? 1 : 0

  name       = var.s3_integrator.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "s3-integrator"
    channel  = local.s3_integrator_channel
    revision = var.s3_integrator.revision
    base     = var.s3_integrator.base
  }

  config      = var.s3_integrator.config
  constraints = var.s3_integrator.constraints
  units       = var.s3_integrator.units
}

resource "juju_integration" "bacula_server_postgresql" {
  model_uuid = var.model_uuid

  application {
    name     = module.bacula_server.application.name
    endpoint = module.bacula_server.requires.postgresql.endpoint
  }

  application {
    name      = local.postgresql_target.name
    offer_url = local.postgresql_target.offer_url
    endpoint  = local.postgresql_target.endpoint
  }
}

resource "juju_integration" "bacula_server_s3" {
  model_uuid = var.model_uuid

  application {
    name     = module.bacula_server.application.name
    endpoint = module.bacula_server.requires.s3.endpoint
  }

  application {
    name      = local.s3_target.name
    offer_url = local.s3_target.offer_url
    endpoint  = local.s3_target.endpoint
  }
}

# bacula-fd is deployed next to each backed-up workload, outside this product,
# and consumes the bacula-dir endpoint through this offer.
resource "juju_offer" "bacula_dir" {
  model_uuid       = var.model_uuid
  application_name = module.bacula_server.application.name
  endpoints        = [module.bacula_server.provides.bacula_dir.endpoint]
}

resource "juju_access_offer" "bacula_dir" {
  count = length(var.bacula_dir_offer_consumers) > 0 ? 1 : 0

  offer_url = juju_offer.bacula_dir.url
  consume   = var.bacula_dir_offer_consumers
}
