# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "application" {
  description = "The deployed application object."
  value       = juju_application.bacula_fd
}

output "provides" {
  description = "Map of the provided integration endpoints."
  value = {
    backup = {
      kind     = "endpoint"
      name     = juju_application.bacula_fd.name
      endpoint = "backup"
    }
  }
}

output "requires" {
  description = "Map of the required integration endpoints."
  value = {
    bacula_dir = {
      kind     = "endpoint"
      name     = juju_application.bacula_fd.name
      endpoint = "bacula-dir"
    }
    juju_info = {
      kind     = "endpoint"
      name     = juju_application.bacula_fd.name
      endpoint = "juju-info"
    }
  }
}
