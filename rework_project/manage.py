#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
This file is part of the reworked version of the AI‑Need‑Job project for
Taller 01.  It simply delegates to Django's command‑line interface, loading
our custom settings from `AiNeedJob.settings`.
"""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AiNeedJob.settings")
    try:
        from django.core.management import execute_from_command_line  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()