(changelog)=

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each revision is versioned by the date of the revision.

## 2026-10-15

* Added a `terraform/product` Terraform product module that deploys `bacula-server` with a bundled `postgresql` catalog database and a bundled `s3-integrator` into one machine model, and offers the `bacula-dir` endpoint for `bacula-fd` units deployed outside the product. The bundled `postgresql` and `s3-integrator` are skipped when `postgresql_integration` or `s3_integration` is set. The module is released with the `backup-server-tf-` tag prefix.

## 2026-10-14

* Replaced the generic, unbound Terraform placeholder module under `terraform/` with one real CC008-compliant Terraform charm module per charm, following the `canonical/haproxy-operator` multi-charm layout: `terraform/charm/backup_integrator`, `terraform/charm/bacula_fd`, and `terraform/charm/bacula_server`. Each module deploys its charm by its Charmhub name, declares `app_name`, `base`, `channel`, `config`, `constraints`, `model_uuid` and `revision` (plus `units` for the non-subordinate `bacula-server` module only), and outputs `application` plus `provides`/`requires` maps with one entry per relation endpoint declared in the charm's `charmcraft.yaml`. The three modules share a single `terraform/MAJOR_VERSION` (relative symlinks from each module directory) since they are released together. Added `tests/main.tftest.hcl` per module using `mock_provider "juju"` with `command = plan` (no live controller). Updated `test_terraform_modules.yaml` (now using `lxd-controller: true` for these machine charms), `terraform_modules_compliance.yaml`, `terraform_modules_release.yaml`, and `generate_terraform_docs.yaml` to list all three module directories.

## 2026-09-25

* Fixed the backup-integrator charm storing backup scripts only on the leader unit at a unit-specific path, causing backup and restore run scripts to fail with "No such file or directory"

## 2026-06-18

* Migrate the RTD documentation under the Canonical domain

## 2026-01-07

* Change the naming scheme for the bacula-fd charm

## 2025-12-17

* Moved charm architecture documentation from Explanation to Reference category.

## 2025-12-09

* Added upgrade documentation.
