"""
========================================================================================
VERCEL SERVERLESS FUNCTION ENTRY POINT
========================================================================================
This file serves as the serverless entrypoint for Vercel deployment.
It applies a WSGI middleware to restore original request paths from Vercel rewrites
and exposes the Flask 'app' object so Vercel's Python runtime can handle incoming requests.
========================================================================================
"""
import sys
import os

# Add the project root directory to sys.path so app and ayurveda_engine can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the configured Flask application
from app import app


class VercelPathFixMiddleware:
    """
    WSGI Middleware to fix PATH_INFO on Vercel.
    When Vercel rewrites requests (/(.*) -> /api/index), WSGI environ['PATH_INFO']
    can mistakenly be set to '/api/index'. This middleware restores the
    actual client request path (e.g. '/', '/api/config', '/api/evaluate', '/static/...')
    from REQUEST_URI, RAW_URI, or HTTP_X_FORWARDED_URI.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        raw_path = (
            environ.get("REQUEST_URI") or 
            environ.get("RAW_URI") or 
            environ.get("HTTP_X_FORWARDED_URI") or 
            environ.get("HTTP_X_MATCHED_PATH")
        )
        if raw_path:
            path = raw_path.split("?")[0]
            if path:
                environ["PATH_INFO"] = path
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


# Apply middleware to Flask WSGI application
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
