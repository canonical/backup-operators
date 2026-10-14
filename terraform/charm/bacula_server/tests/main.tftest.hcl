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
    # renovate: depName="bacula-server"
    revision = 54
  }

  assert {
    condition     = output.application.name == "bacula-server"
    error_message = "bacula-server application name did not match expected"
  }

  assert {
    condition     = output.provides.value.endpoint == "bacula-dir"
    error_message = "bacula-server module should provide 'provides.value' output"
  }

  assert {
    condition     = output.requires.value.endpoint == "postgresql"
    error_message = "bacula-server module should provide 'requires.value' output"
  }

  assert {
    condition     = output.requires.s3.endpoint == "s3"
    error_message = "bacula-server module should provide 'requires.s3' output"
  }
}
