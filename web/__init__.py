from re import A
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, current_user
# from flask_caching import Cache


db = SQLAlchemy()
# cache = Cache()
# cache_config = {
#     "DEBUG": True,
#     "CACHE_TYPE": "SimpleCache",
#     "CACHE_DEFAULT_TIMEOUT": 300,
# }
db_name = "data.db"


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")
    app.static_folder = "static"
    db.init_app(app)

    from .models import User

    from .views import views
    from .auth import auth
    from .admin import admin

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/")

    app.register_error_handler(404, page_not_found_404)
    app.register_error_handler(500, internal_server_error_500)

    create_db(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # cache.init_app(app, cache_config)
    return app


def create_db(app):
    if not path.exists("FlaskProject/" + db_name):
        db.create_all(app=app)
        print("Database Created")


def page_not_found_404(e):
    return (render_template("404.html", user=current_user), 404)


def internal_server_error_500(e):
    return (render_template("404.html", user=current_user), 500)
