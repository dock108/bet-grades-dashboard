"""
Application package initialization.
This module initializes the Flask application and registers blueprints.
"""

from flask import Flask
from flask_caching import Cache
from app.core.config import get_config
from app.core.supabase import get_supabase_client
from flask_cors import CORS
from app.api.bet_routes import bet_routes

# Initialize extensions
cache = Cache()

def create_app(config_class=None):
    """Application factory function."""
    app = Flask(__name__)
    
    # Use provided config_class or get config based on environment
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)

    # Initialize Flask extensions
    cache.init_app(app)

    with app.app_context():
        # Initialize Supabase connection
        get_supabase_client()

        # Register blueprints
        from app.main import bp as main_bp
        app.register_blueprint(main_bp)

        from app.admin import bp as admin_bp
        app.register_blueprint(admin_bp)
        
        app.register_blueprint(bet_routes, url_prefix='/api')

        # Register error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return {'error': 'Resource not found'}, 404

        @app.errorhandler(500)
        def internal_error(error):
            return {'error': 'Internal server error'}, 500

    return app

# Create the application instance
app = create_app()

