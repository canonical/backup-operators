# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "external_integrations" {
  command = plan

  variables {
    model_uuid = run.setup_tests.model_uuid
    postgresql_integration = {
      offer_url = "admin/database.postgresql"
    }
    s3_integration = {
      name     = "object-storage"
      endpoint = "s3-credentials"
    }
  }

  assert {
    condition     = length(juju_application.postgresql) == 0 && length(juju_application.s3_integrator) == 0
    error_message = "the bundled postgresql and s3-integrator should not be deployed when their integrations are set"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    risk       = "edge"
    bacula_server = {
      # renovate: depName="bacula-server"
      revision = 54
    }
    postgresql = {
      # renovate: depName="postgresql"
      revision = 1236
    }
    s3_integrator = {
      # renovate: depName="s3-integrator"
      revision = 637
    }
  }

  assert {
    condition     = output.models.backup.model_uuid == run.setup_tests.model_uuid
    error_message = "the backup model UUID did not match the provided model_uuid"
  }

  assert {
    condition     = keys(output.models.backup.components) == ["bacula_server", "postgresql", "s3_integrator"]
    error_message = "the backup model should contain bacula-server, postgresql and s3-integrator"
  }

  assert {
    condition     = output.offers.bacula_dir != ""
    error_message = "the bacula-dir offer URL should be exposed"
  }

  assert {
    condition     = output.models.backup.components.bacula_server.charm[0].channel == "latest/edge"
    error_message = "the bacula-server channel should reflect the requested risk"
  }
}

run "invalid_risk" {
  command = plan

  variables {
    model_uuid = run.setup_tests.model_uuid
    risk       = "beta"
  }

  expect_failures = [
    var.risk,
  ]
}
