import json
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from flask import make_response
from flask.blueprints import Blueprint

from .cache import cache

bp = Blueprint("rss", __name__)


@bp.get("/")
@cache.cached()
def rss():
    books = _get_books()
    feed = _generate_feed(books)
    response = _make_response(feed)

    return response, 200


def _generate_feed(books):
    fg = FeedGenerator()
    fg.link(href="https://humblerss.herokuapp.com")
    fg.title("Humble RSS")
    fg.author({"name": "shimst3r", "email": "@shimst3r@chaos.social"})
    fg.subtitle("Humble RSS - Your humble RSS feed for HumbleBundle news.")
    fg.language("en")
    for book in books:
        fe = fg.add_entry()
        fe.title(book["tile_short_name"])
        fe.link(href=f"https://humblebundle.com/{book['product_url']}")
        fe.content(book["detailed_marketing_blurb"])
        dt = datetime.fromisoformat(book["start_date|datetime"])
        fe.pubDate(pytz.utc.localize(dt))

    return fg


def _get_books():
    resp = requests.get("https://humblebundle.com/books")
    if resp.status_code != 200:
        return (
            f"Error: unexpected status code: {resp.status_code}",
            503,
        )

    soup = BeautifulSoup(resp.content, "html5lib")
    raw_json = soup.find("script", {"id": "landingPage-json-data"}).contents[0]
    data = json.loads(raw_json)
    books = data["data"]["books"]["mosaic"][0]["products"]
    sorted_books = sorted(
        books,
        key=lambda b: datetime.fromisoformat(b["start_date|datetime"]),
        reverse=False,
    )

    return sorted_books


def _make_response(feed):
    response = make_response(feed.rss_str(pretty=True))
    response.headers.set("Content-Type", "application/rss+xml")

    return response
