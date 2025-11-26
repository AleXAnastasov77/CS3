from flask import Flask
from flask_cors import CORS
from config import Config
from api.auth import auth_bp
from api.employees import employees_bp
from api.departments import departments_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Allow CORS for development / separate frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(departments_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
