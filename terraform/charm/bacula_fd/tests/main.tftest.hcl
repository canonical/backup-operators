# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variables {
  app_name    = "bacula-fd"
  base        = "ubuntu@24.04"
  channel     = "latest/edge"
  config      = {}
  constraints = "arch=amd64"
  model_uuid  = "00000000-0000-0000-0000-000000000001"
  revision    = 24
}

mock_provider "juju" {
  mock_resource "juju_application" {
    override_during = plan
    defaults = {
      id         = "bacula-fd"
      model_type = "lxd"
    }
  }
}

run "deploys_application" {
  command = plan

  assert {
    condition     = output.application.name == "bacula-fd"
    error_message = "application name did not match expected"
  }

  assert {
    condition     = output.application.model_uuid == var.model_uuid
    error_message = "application model_uuid did not match expected"
  }

  assert {
    condition     = output.application.charm[0].name == "bacula-fd"
    error_message = "application charm name did not match expected"
  }

  assert {
    condition = output.provides == {
      backup = {
        kind     = "endpoint"
        name     = "bacula-fd"
        endpoint = "backup"
      }
    }
    error_message = "provides outputs did not match expected structure"
  }

  assert {
    condition = output.requires == {
      bacula_dir = {
        kind     = "endpoint"
        name     = "bacula-fd"
        endpoint = "bacula-dir"
      }
      juju_info = {
        kind     = "endpoint"
        name     = "bacula-fd"
        endpoint = "juju-info"
      }
    }
    error_message = "requires outputs did not match expected structure"
  }
}
