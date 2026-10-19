# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    base       = "ubuntu@24.04"
    channel    = "latest/edge"
    # renovate: depName="backup-integrator"
    revision = 12
  }

  assert {
    condition     = output.application.name == "backup-integrator"
    error_message = "backup-integrator application name did not match expected"
  }

  assert {
    condition     = output.requires.backup.endpoint == "backup"
    error_message = "backup-integrator module should provide 'requires.backup' output"
  }

  assert {
    condition     = output.requires.juju_info.endpoint == "juju-info"
    error_message = "backup-integrator module should provide 'requires.juju_info' output"
  }
}
