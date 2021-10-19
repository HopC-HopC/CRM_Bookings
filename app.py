from jinja2.utils import clear_caches
from web import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
