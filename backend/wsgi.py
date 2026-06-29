# Trigger redeployment with public MySQL credentials
import os
import sys

# Add the backend directory to sys.path to resolve imports correctly
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app

# PythonAnywhere looks for 'application'
application = create_app()
