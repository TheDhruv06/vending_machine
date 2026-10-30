"""
========================================================================================
VERCEL SERVERLESS FUNCTION ENTRY POINT
========================================================================================
This file serves as the serverless entrypoint for Vercel deployment.
It extracts the captured path from the '__path' query parameter supplied by
vercel.json rewrites, accurately setting WSGI PATH_INFO so Flask's internal routes
(/, /api/config, /api/evaluate, /static/...) execute perfectly.
========================================================================================
"""
import sys
import os
import urllib.parse

# Add project root directory to sys.path so app and ayurveda_engine can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app


class VercelPathFixMiddleware:
    """
    WSGI Middleware to restore PATH_INFO from Vercel's rewrite query parameter '__path'.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        parsed = urllib.parse.parse_qs(qs)

        if "__path" in parsed and parsed["__path"][0]:
            # Restore the real route that the client requested
            target_path = "/" + parsed["__path"][0].lstrip("/")
            environ["PATH_INFO"] = target_path

            # Remove __path from query string so request.args stays clean
            cleaned_args = {k: v for k, v in parsed.items() if k != "__path"}
            environ["QUERY_STRING"] = urllib.parse.urlencode(cleaned_args, doseq=True)
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


# Attach middleware to the Flask WSGI handler
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
