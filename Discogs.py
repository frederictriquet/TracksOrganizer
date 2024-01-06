
import os
import requests
import urllib.parse
from Logger import logger

DISCOGS_URL="https://api.discogs.com/database/search?"
DISCOGS_KEY=os.environ['DISCOGS_KEY']
DISCOGS_SECRET=os.environ['DISCOGS_SECRET']

def ask(artist, title):
    headers = {'Accept': 'application/json', 'Authorization': f'Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}'}
    print(artist, title)
    query = urllib.parse.urlencode({'q': f'{artist} {title}'})
    url = DISCOGS_URL+query
    r = requests.get(url, headers=headers)
    response = r.json()
    try:
        for res in response['results']:
            year = res['year'] if 'year' in res else '????'
            title = res['title'] if 'title' in res else '?'
            print(f"{year} -- {title}")
    except KeyError as e:
        logger.error(e)
