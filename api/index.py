"""
Vercel serverless function entry point.
This file is used by Vercel to serve the Flask application.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import create_app

# Create the application instance
app = create_app()

# This is used by Vercel
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080))) 