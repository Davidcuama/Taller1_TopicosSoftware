"""
WSGI config for the AiNeedJob project.

This exposes the WSGI callable as a module-level variable named ``application``.
It enables deployment on WSGI-compatible web servers such as Gunicorn.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AiNeedJob.settings")

application = get_wsgi_application()