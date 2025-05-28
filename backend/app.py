# backend/app.py
from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from services.api_service import api_bp
from services.report_generator import reports_bp
from utils.config import Config
from models.database import init_database

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app, origins=['http://localhost:3000'])
    cache = Cache(app)
    
    # Initialize database
    init_database()
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'music-analytics-api'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)