# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "application" {
  description = "The deployed application object."
  value       = juju_application.bacula_server
}

output "provides" {
  description = "Map of the provided integration endpoints."
  value = {
    bacula_dir = {
      kind     = "endpoint"
      name     = juju_application.bacula_server.name
      endpoint = "bacula-dir"
    }
  }
}

output "requires" {
  description = "Map of the required integration endpoints."
  value = {
    postgresql = {
      kind     = "endpoint"
      name     = juju_application.bacula_server.name
      endpoint = "postgresql"
    }
    s3 = {
      kind     = "endpoint"
      name     = juju_application.bacula_server.name
      endpoint = "s3"
    }
  }
}
