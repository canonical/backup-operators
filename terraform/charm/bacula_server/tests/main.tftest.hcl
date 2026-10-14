# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variables {
  app_name    = "bacula-server"
  base        = "ubuntu@24.04"
  channel     = "latest/edge"
  config      = {}
  constraints = "arch=amd64"
  model_uuid  = "00000000-0000-0000-0000-000000000001"
  revision    = 54
  units       = 1
}

mock_provider "juju" {
  mock_resource "juju_application" {
    override_during = plan
    defaults = {
      id         = "bacula-server"
      model_type = "lxd"
    }
  }
}

run "deploys_application" {
  command = plan

  assert {
    condition     = output.application.name == "bacula-server"
    error_message = "application name did not match expected"
  }

  assert {
    condition     = output.application.model_uuid == var.model_uuid
    error_message = "application model_uuid did not match expected"
  }

  assert {
    condition     = output.application.units == 1
    error_message = "application units did not match expected"
  }

  assert {
    condition = output.provides == {
      bacula_dir = {
        kind     = "endpoint"
        name     = "bacula-server"
        endpoint = "bacula-dir"
      }
    }
    error_message = "provides outputs did not match expected structure"
  }

  assert {
    condition = output.requires == {
      postgresql = {
        kind     = "endpoint"
        name     = "bacula-server"
        endpoint = "postgresql"
      }
      s3 = {
        kind     = "endpoint"
        name     = "bacula-server"
        endpoint = "s3"
      }
    }
    error_message = "requires outputs did not match expected structure"
  }
}
