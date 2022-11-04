"""
Humble RSS works like this:

1. Request HTML data from the respective bundle category's landing page via
   requests.
2. Parse the actual bundle data using BeautifulSoup.
3. Transform the data to a sensible format.
4. Generate a feed using the feedgen library.
5. Serve the data using Flask.
"""
import json
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from flask import Flask
from flask_caching import Cache

config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 60 * 60,
}
app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)


@app.get("/rss")
@cache.cached()
def rss():
    resp = requests.get("https://humblebundle.com/books?hmb_source=navbar")
    if resp.status_code != 200:
        print(f"error: unexpected status code: {resp.status_code}")

    soup = BeautifulSoup(resp.content, "html5lib")
    raw_json = soup.find("script", {"id": "landingPage-json-data"}).contents[0]
    data = json.loads(raw_json)
    books = data["data"]["books"]["mosaic"][0]["products"]

    fg = FeedGenerator()
    fg.link(href="https://localhost/rss")
    fg.title("Humble RSS")
    fg.author({"name": "shimst3r", "email": "shimst3r+humble@gmail.com"})
    fg.subtitle("Humble RSS - Your humble RSS feed for HumbleBundle news.")
    fg.language("en")
    for book in books:
        fe = fg.add_entry()
        fe.title(book["tile_short_name"])
        fe.link(href=f"https://humblebundle.com/{book['product_url']}")
        fe.content(book["detailed_marketing_blurb"])
        dt = datetime.fromisoformat(book["start_date|datetime"])
        fe.pubDate(pytz.utc.localize(dt))

    feed = fg.rss_str(pretty=True)

    return feed
