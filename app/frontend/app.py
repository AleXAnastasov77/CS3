from flask import Flask, render_template, redirect, url_for
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    @app.context_processor
    def inject_globals():
        return dict(backend_api_url=app.config["BACKEND_API_URL"])
    @app.route("/")
    def index():
        # Employees page
        return render_template("employees.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/new")
    def new_employee():
        return render_template("employee_form.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
