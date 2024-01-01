
import os
import requests
import urllib.parse

DISCOGS_URL="https://api.discogs.com/database/search?q="
DISCOGS_KEY=os.environ['DISCOGS_KEY']
DISCOGS_SECRET=os.environ['DISCOGS_SECRET']

def ask(artist, title):
    headers = {'Accept': 'application/json', 'Authorization': f'Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}'}
    print(artist, title)
    query = urllib.parse.quote(f'{artist} {title}')
    url = DISCOGS_URL+query
    r = requests.get(url, headers=headers)
    response = r.json()
    try:
        # if response['pagination']['items'] > 0:
        #     print(f"{response['results'][0]['year']} -- {response['results'][0]['title']}")
        for res in response['results']:
            print(f"{res['year']} -- {res['title']}")
    except:
        print(response)

