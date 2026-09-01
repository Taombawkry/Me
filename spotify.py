#!/usr/bin/env python3
"""
spotify.py — resolves Spotify URLs into cover art + metadata at build time.

Two sources, tried in order:
  1. Web API (client credentials) — rich metadata, needs SPOTIFY_CLIENTID/SECRET.
  2. oEmbed (no auth) — title + cover art only, but works for editorial
     playlists (37i9dQZF...) which the Web API returns 404 for. Verified:
     that 404 is the Nov-2024 deprecation for new apps, not a missing
     `market` — it persists with market=US/GB/ZM alike.

Results are cached in content/playlists/_cache.json so builds are offline-safe
and don't re-hit the API on every deploy.
"""
import base64
import json
import os
import re
import time
from pathlib import Path

import requests

CACHE_PATH = Path('content/playlists/_cache.json')
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API = 'https://api.spotify.com/v1'
OEMBED = 'https://open.spotify.com/oembed'

# Sent because the docs advise it for catalogue availability. Measured: it
# makes no difference to the name/image fields we actually read, and it does
# not rescue the editorial-playlist 404.
MARKET = 'US'

# Your own Spotify user id (from the profile link in content/social.md).
# Playlists you own don't need "by Thomas.gondwe" printed under them.
SELF_USER_ID = 'ugf8e1kb3nrk1zw1ejlgehw3q'

# https://open.spotify.com/playlist/ID  |  /intl-pt/album/ID  |  spotify:track:ID
_URL_RE = re.compile(
    r'(?:open\.spotify\.com/(?:intl-[a-z-]+/)?|spotify:)'
    r'(playlist|album|track)[:/]([A-Za-z0-9]+)'
)

_token = {'value': None, 'expires': 0}


def load_dotenv(path='.env'):
    """Minimal .env reader. Netlify supplies real env vars, so this is local-only."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def parse_url(url):
    """('playlist', '3cEYpjA9oz9GiPac4AsH4n') or (None, None)."""
    m = _URL_RE.search(url or '')
    return (m.group(1), m.group(2)) if m else (None, None)


def _get_token():
    """Cached client-credentials token. Returns None if creds are absent/bad."""
    if _token['value'] and time.time() < _token['expires']:
        return _token['value']

    cid = os.environ.get('SPOTIFY_CLIENTID')
    secret = os.environ.get('SPOTIFY_CLIENTSECRET')
    if not (cid and secret):
        return None

    auth = base64.b64encode(f'{cid}:{secret}'.encode()).decode()
    try:
        r = requests.post(
            TOKEN_URL,
            data={'grant_type': 'client_credentials'},
            headers={'Authorization': f'Basic {auth}'},
            timeout=20,
        )
    except requests.RequestException as e:
        print(f'  ! spotify token request failed: {e}')
        return None

    if r.status_code != 200:
        print(f'  ! spotify token rejected ({r.status_code}) — falling back to oEmbed')
        return None

    payload = r.json()
    _token['value'] = payload['access_token']
    _token['expires'] = time.time() + payload.get('expires_in', 3600) - 60
    return _token['value']


def _pick_images(images):
    """Spotify returns images largest-first. Give back (large, small)."""
    urls = [img['url'] for img in (images or []) if img.get('url')]
    if not urls:
        return None, None
    return urls[0], urls[-1]


def _from_api(kind, spotify_id):
    token = _get_token()
    if not token:
        return None
    try:
        r = requests.get(
            f'{API}/{kind}s/{spotify_id}',
            headers={'Authorization': f'Bearer {token}'},
            params={'market': MARKET},
            timeout=20,
        )
    except requests.RequestException as e:
        print(f'  ! spotify api request failed for {kind}/{spotify_id}: {e}')
        return None

    if r.status_code != 200:
        # 404 here is normal for editorial playlists — oEmbed picks them up.
        return None

    data = r.json()
    if kind == 'album':
        art, art_small = _pick_images(data.get('images'))
        artists = ', '.join(a['name'] for a in data.get('artists', []))
        year = (data.get('release_date') or '')[:4]
        subtitle = f'{artists} · {year}' if year else artists
    elif kind == 'playlist':
        art, art_small = _pick_images(data.get('images'))
        owner = data.get('owner') or {}
        # `tracks` comes back null under client credentials — track data needs
        # user auth — so a track count isn't available to a static build.
        if owner.get('id') == SELF_USER_ID:
            subtitle = ''
        else:
            name = owner.get('display_name') or ''
            subtitle = f'by {name}' if name else ''
    else:  # track
        album = data.get('album') or {}
        art, art_small = _pick_images(album.get('images'))
        subtitle = ', '.join(a['name'] for a in data.get('artists', []))

    return {
        'kind': kind,
        'id': spotify_id,
        'name': data.get('name') or '',
        'subtitle': subtitle,
        'art': art,
        'art_small': art_small or art,
        'url': (data.get('external_urls') or {}).get(
            'spotify', f'https://open.spotify.com/{kind}/{spotify_id}'
        ),
        'source': 'api',
    }


def _from_oembed(kind, spotify_id):
    url = f'https://open.spotify.com/{kind}/{spotify_id}'
    try:
        r = requests.get(OEMBED, params={'url': url}, timeout=20)
    except requests.RequestException as e:
        print(f'  ! oembed request failed for {kind}/{spotify_id}: {e}')
        return None
    if r.status_code != 200:
        return None

    data = r.json()
    art = data.get('thumbnail_url')
    return {
        'kind': kind,
        'id': spotify_id,
        'name': data.get('title') or '',
        'subtitle': '',
        'art': art,
        'art_small': art,
        'url': url,
        'source': 'oembed',
    }


def load_cache():
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            print('  ! playlist cache was corrupt — rebuilding it')
    return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def resolve(url, cache, refresh=False):
    """URL -> metadata dict (mutates cache). Returns None if unresolvable."""
    kind, spotify_id = parse_url(url)
    if not kind:
        print(f'  ! not a Spotify playlist/album/track URL: {url}')
        return None

    key = f'{kind}:{spotify_id}'
    if not refresh and key in cache:
        return cache[key]

    entry = _from_api(kind, spotify_id) or _from_oembed(kind, spotify_id)
    if not entry:
        if key in cache:
            print(f'  ! could not refresh {key} — keeping cached copy')
            return cache[key]
        print(f'  ! could not resolve {key} — rendering a placeholder tile')
        return None

    entry['fetched'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    cache[key] = entry
    print(f'  + {key} via {entry["source"]}: {entry["name"]}')
    return entry
