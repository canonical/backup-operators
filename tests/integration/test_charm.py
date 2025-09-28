#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""


def test_list_jobs(baculum):
    assert len(baculum.list_job_names()) == 3
