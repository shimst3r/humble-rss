"""
Humble RSS works like this:

1. Request HTML data from the respective bundle category's landing page via
   requests.
2. Parse the actual bundle data using BeautifulSoup.
3. Transform the data to a sensible format.
4. Generate a feed using the feedgen library.
5. Serve the data using Flask.
"""
from flask import Flask, render_template

from . import rss
from .cache import cache


def create_app(cfg: dict):
    cfg.update(
        {
            "CACHE_TYPE": "SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": 60 * 60,
        }
    )

    app = Flask(__name__)
    app.config.from_mapping(cfg)
    app.register_blueprint(rss.bp)

    cache.init_app(app)

    @app.get("/")
    @cache.cached()
    def home():
        return render_template("index.html")

    return app
