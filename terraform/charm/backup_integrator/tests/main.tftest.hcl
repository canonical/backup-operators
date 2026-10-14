# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variables {
  app_name    = "backup-integrator"
  base        = "ubuntu@24.04"
  channel     = "latest/edge"
  config      = {}
  constraints = "arch=amd64"
  model_uuid  = "00000000-0000-0000-0000-000000000001"
  revision    = 12
}

mock_provider "juju" {
  mock_resource "juju_application" {
    override_during = plan
    defaults = {
      id         = "backup-integrator"
      model_type = "lxd"
    }
  }
}

run "deploys_application" {
  command = plan

  assert {
    condition     = output.application.name == "backup-integrator"
    error_message = "application name did not match expected"
  }

  assert {
    condition     = output.application.model_uuid == var.model_uuid
    error_message = "application model_uuid did not match expected"
  }

  assert {
    condition     = output.application.charm[0].name == "backup-integrator"
    error_message = "application charm name did not match expected"
  }

  assert {
    condition = output.requires == {
      backup = {
        kind     = "endpoint"
        name     = "backup-integrator"
        endpoint = "backup"
      }
      juju_info = {
        kind     = "endpoint"
        name     = "backup-integrator"
        endpoint = "juju-info"
      }
    }
    error_message = "requires outputs did not match expected structure"
  }

  assert {
    condition     = output.provides == {}
    error_message = "provides output did not match expected structure"
  }
}
