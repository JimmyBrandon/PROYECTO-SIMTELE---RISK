"""Plantilla para copiar al archivo WSGI del panel PythonAnywhere."""
from pathlib import Path
import sys
project = Path.home() / 'simtele-risk'
if not (project / 'wsgi.py').is_file():
    raise RuntimeError(f'No se encontró {project}/wsgi.py. Revisa la ruta del proyecto.')
sys.path.insert(0, str(project))
from wsgi import application
