from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from .config import config
import os


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    
    # Register blueprints
    try:
        from app.routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except ImportError:
        print("Auth routes not ready yet")
    
    # Register user routes
    try:
        from app.routes.user_routes import user_bp
        app.register_blueprint(user_bp, url_prefix='/api')
        print("✅ User routes registered")
    except ImportError as e:
        print(f"User routes not ready yet: {e}")
    
    # Register donation routes
    try:
        from app.routes.donation_routes import donation_bp
        app.register_blueprint(donation_bp, url_prefix='/api')
        print("✅ Donation routes registered")
    except ImportError as e:
        print(f"Donation routes not ready yet: {e}")
    
    # 👇 ADD THIS BLOCK - Register donor routes
    try:
        from app.routes.donor_routes import donor_bp
        app.register_blueprint(donor_bp, url_prefix='/api')
        print("✅ Donor routes registered")
    except ImportError as e:
        print(f"Donor routes not ready yet: {e}")
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return {'status': 'healthy', 'message': 'RAKTASMRITI API is running'}, 200
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app