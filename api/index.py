"""
========================================================================================
VERCEL SERVERLESS FUNCTION ENTRY POINT
========================================================================================
This file serves as the serverless entrypoint for Vercel deployment.
It exposes the Flask 'app' object so Vercel's Python runtime can handle incoming requests.
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

