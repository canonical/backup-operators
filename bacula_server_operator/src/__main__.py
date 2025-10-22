# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""bacula-server charm module entrypoint."""

# suppress pylint false positive no-member warning
# pylint: disable=no-member

import ops

from . import charm

ops.main.main(charm.BaculaServerCharm)
