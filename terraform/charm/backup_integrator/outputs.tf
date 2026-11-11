# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "application" {
  description = "The deployed application object."
  value       = juju_application.backup_integrator
}

output "provides" {
  description = "Map of the provided integration endpoints."
  value       = {}
}

output "requires" {
  description = "Map of the required integration endpoints."
  value = {
    backup = {
      kind     = "endpoint"
      name     = juju_application.backup_integrator.name
      endpoint = "backup"
    }
    juju_info = {
      kind     = "endpoint"
      name     = juju_application.backup_integrator.name
      endpoint = "juju-info"
    }
  }
}
