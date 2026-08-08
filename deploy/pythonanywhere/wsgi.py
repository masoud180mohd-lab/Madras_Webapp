"""
WSGI for PythonAnywhere — copy/upload to:
  /var/www/rasulillahmadras_pythonanywhere_com_wsgi.py
"""

import os
import sys

project_home = "/home/rasulillahmadras/madrasa_sys"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "madrasa_sys.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
