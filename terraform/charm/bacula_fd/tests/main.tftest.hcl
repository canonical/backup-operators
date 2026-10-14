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
    # renovate: depName="bacula-fd"
    revision = 24
  }

  assert {
    condition     = output.application.name == "bacula-fd"
    error_message = "bacula-fd application name did not match expected"
  }

  assert {
    condition     = output.provides.value.endpoint == "backup"
    error_message = "bacula-fd module should provide 'provides.value' output"
  }

  assert {
    condition     = output.requires.value.endpoint == "bacula-dir"
    error_message = "bacula-fd module should provide 'requires.value' output"
  }

  assert {
    condition     = output.requires.juju_info.endpoint == "juju-info"
    error_message = "bacula-fd module should provide 'requires.juju_info' output"
  }
}
