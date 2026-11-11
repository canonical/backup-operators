# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

locals {
  # The product owns each charm's track; `risk` selects the channel risk solution-wide.
  bacula_server_channel = coalesce(var.bacula_server.channel, "latest/${var.risk}")
  postgresql_channel    = coalesce(var.postgresql.channel, "16/${var.risk}")
  s3_integrator_channel = coalesce(var.s3_integrator.channel, "1/${var.risk}")

  deploy_postgresql    = var.postgresql_integration == null
  deploy_s3_integrator = var.s3_integration == null

  postgresql_target = local.deploy_postgresql ? {
    name      = one(juju_application.postgresql[*].name)
    offer_url = null
    endpoint  = "database"
  } : var.postgresql_integration
  s3_target = local.deploy_s3_integrator ? {
    name      = one(juju_application.s3_integrator[*].name)
    offer_url = null
    endpoint  = "s3-credentials"
  } : var.s3_integration
}
