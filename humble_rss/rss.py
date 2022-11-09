import json
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from flask import make_response
from flask.blueprints import Blueprint
from werkzeug.exceptions import InternalServerError

from .cache import cache

bp = Blueprint("rss", __name__)


@bp.get("/books")
@cache.cached()
def books():
    try:
        books = _get_items_by_category("books")
    except InternalServerError as err:
        return err, 500
    feed = _generate_feed(books)
    response = _make_response(feed)

    return response, 200


@bp.get("/games")
@cache.cached()
def games():
    try:
        games = _get_items_by_category("games")
    except InternalServerError as err:
        return err, 500
    feed = _generate_feed(games)
    response = _make_response(feed)

    return response, 200


def _generate_feed(items):
    fg = FeedGenerator()
    fg.link(href="https://humblerss.herokuapp.com")
    fg.title("Humble RSS")
    fg.author({"name": "shimst3r", "email": "@shimst3r@chaos.social"})
    fg.subtitle("Humble RSS - Your humble RSS feed for HumbleBundle news.")
    fg.language("en")
    for item in items:
        fe = fg.add_entry()
        fe.title(item["tile_short_name"])
        fe.link(href="https://humblebundle.com" + item["product_url"])
        fe.content(item["detailed_marketing_blurb"])
        dt = datetime.fromisoformat(item["start_date|datetime"])
        fe.pubDate(pytz.utc.localize(dt))

    return fg


def _get_items_by_category(category):
    resp = requests.get(f"https://humblebundle.com/{category}")
    if resp.status_code != 200:
        err = f"Error: unexpected status code: {resp.status_code}"
        raise InternalServerError(err)

    soup = BeautifulSoup(resp.content, "html5lib")
    raw_json = soup.find("script", {"id": "landingPage-json-data"}).contents[0]
    data = json.loads(raw_json)
    items = data["data"][category]["mosaic"][0]["products"]
    sorted_items = sorted(
        items,
        key=lambda item: datetime.fromisoformat(item["start_date|datetime"]),
        reverse=False,
    )

    return sorted_items


def _make_response(feed):
    response = make_response(feed.rss_str(pretty=True))
    response.headers.set("Content-Type", "application/rss+xml")

    return response
