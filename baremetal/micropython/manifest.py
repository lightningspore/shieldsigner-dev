# SPDX-License-Identifier: MIT
# Only reviewed port code; no host filesystem or implicit third-party modules.
freeze("$(PORT_DIR)/../app", ("seedsigner_port/__init__.py", "seedsigner_port/buttons.py"))
