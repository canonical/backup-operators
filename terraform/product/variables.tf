# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variable "bacula_dir_offer_consumers" {
  description = "Juju users allowed to consume the `bacula-dir` offer, for example to integrate bacula-fd units from other models."
  type        = list(string)
  default     = []
}

variable "bacula_server" {
  description = "Configuration of the bacula-server charm. When `channel` is null it defaults to `latest/<risk>`."
  type = object({
    app_name    = optional(string, "bacula-server")
    base        = optional(string, "ubuntu@24.04")
    channel     = optional(string)
    config      = optional(map(string), {})
    constraints = optional(string)
    revision    = optional(number)
    units       = optional(number, 1)
  })
  default = {}
}

variable "metadata_version" {
  description = "Version string reported in the product module `metadata` output."
  type        = string
  default     = "1.0.0"
}

variable "model_uuid" {
  description = "UUID of the machine Juju model to deploy the backup server solution into."
  type        = string
  nullable    = false
}

variable "postgresql" {
  description = "Configuration of the bundled postgresql charm, deployed unless `postgresql_integration` is set. When `channel` is null it defaults to `16/<risk>`."
  type = object({
    app_name    = optional(string, "postgresql")
    base        = optional(string, "ubuntu@24.04")
    channel     = optional(string)
    config      = optional(map(string), {})
    constraints = optional(string)
    revision    = optional(number)
    units       = optional(number, 1)
  })
  default = {}
}

variable "postgresql_integration" {
  description = "Existing `postgresql_client` provider to integrate bacula-server with, given as an application `name` in `model_uuid` or an `offer_url`. When set, the bundled postgresql is not deployed."
  type = object({
    name      = optional(string)
    offer_url = optional(string)
    endpoint  = optional(string)
  })
  default = null

  validation {
    condition     = var.postgresql_integration == null || ((try(var.postgresql_integration.name, null) == null) != (try(var.postgresql_integration.offer_url, null) == null))
    error_message = "Set exactly one of name or offer_url in postgresql_integration."
  }
}

variable "risk" {
  description = "Risk level controlling the channel risk of the charms in the solution. Every charm `channel` left unset defaults to `<track>/<risk>`."
  type        = string
  default     = "stable"

  validation {
    condition     = contains(["stable", "edge"], var.risk)
    error_message = "risk must be one of: stable, edge."
  }
}

variable "s3_integration" {
  description = "Existing `s3` provider to integrate bacula-server with, given as an application `name` in `model_uuid` or an `offer_url`. When set, the bundled s3-integrator is not deployed."
  type = object({
    name      = optional(string)
    offer_url = optional(string)
    endpoint  = optional(string)
  })
  default = null

  validation {
    condition     = var.s3_integration == null || ((try(var.s3_integration.name, null) == null) != (try(var.s3_integration.offer_url, null) == null))
    error_message = "Set exactly one of name or offer_url in s3_integration."
  }
}

variable "s3_integrator" {
  description = "Configuration of the bundled s3-integrator charm, deployed unless `s3_integration` is set. When `channel` is null it defaults to `1/<risk>`. Set the S3 credentials with the `sync-s3-credentials` action after deployment."
  type = object({
    app_name    = optional(string, "s3-integrator")
    base        = optional(string, "ubuntu@22.04")
    channel     = optional(string)
    config      = optional(map(string), {})
    constraints = optional(string)
    revision    = optional(number)
    units       = optional(number, 1)
  })
  default = {}
}
