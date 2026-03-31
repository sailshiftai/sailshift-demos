#!/usr/bin/env python3
"""
Download 3 boat images per listing for all SailShift demo sites.
Creates: demo/images/{folder}/1.jpg  (card thumbnail + carousel 1)
         demo/images/{folder}/2.jpg  (carousel 2)
         demo/images/{folder}/3.jpg  (carousel 3)

Usage:
  python3 fetch_images.py --key YOUR_PEXELS_API_KEY

Get a free key at: https://www.pexels.com/api/
"""
import argparse, os, time, json, urllib.request, urllib.error, sys

# ── Listing definitions: (folder_prefix, query) ───────────────────────────────
# Each query is tuned for that exact boat's visual type and size.

LISTINGS = [
    # ── US Power — budget ────────────────────────────────────────────────────
    ('usp-1',  'Boston Whaler center console fishing boat offshore'),
    ('usp-2',  'Sea Ray bowrider sport boat'),
    ('usp-3',  'Grady-White walkaround fishing boat'),
    ('usp-4',  'Chris-Craft classic mahogany runabout boat'),
    ('usp-5',  'Chaparral bowrider speedboat'),
    ('usp-6',  'offshore fishing center console boat'),
    ('usp-7',  'outboard bowrider sport boat'),
    ('usp-8',  'Pursuit center console offshore fishing'),
    ('usp-9',  'large triple outboard center console boat'),
    ('usp-10', 'Sea Ray express cruiser cabin boat'),

    # ── US Power — mid ───────────────────────────────────────────────────────
    ('usp-21', 'Viking sportfishing convertible yacht'),
    ('usp-22', 'Hatteras express cruiser yacht'),
    ('usp-23', 'large center console offshore fishing boat'),
    ('usp-24', 'deep sea canyon fishing center console'),
    ('usp-25', 'sportfishing diesel convertible yacht'),
    ('usp-26', 'Sea Ray luxury sport cruiser'),
    ('usp-27', 'sport cruiser offshore fishing yacht'),
    ('usp-28', 'large flybridge motor yacht'),
    ('usp-29', 'Bertram sportfishing convertible yacht'),
    ('usp-30', 'tournament sportfishing Viking yacht'),

    # ── US Power — premium ───────────────────────────────────────────────────
    ('usp-41', 'luxury sportfishing superyacht'),
    ('usp-42', 'superyacht motor yacht luxury 100 foot'),
    ('usp-43', 'large sportfishing tournament yacht'),
    ('usp-44', 'mega sportfishing yacht luxury'),
    ('usp-45', 'premium sportfishing convertible yacht large'),

    # ── US Sail — budget ─────────────────────────────────────────────────────
    ('uss-1',  'Catalina sailing yacht marina'),
    ('uss-2',  'Hunter sailing yacht cockpit'),
    ('uss-3',  'Beneteau Oceanis sailing yacht'),
    ('uss-4',  'Jeanneau sailing yacht blue water'),
    ('uss-5',  'sailing yacht marina dock'),
    ('uss-6',  'performance racing sailboat offshore'),
    ('uss-7',  'cruising sailboat sailboat'),
    ('uss-8',  'small sailing yacht Beneteau'),
    ('uss-9',  'Island Packet offshore cruising sailboat'),
    ('uss-10', 'sailing yacht cockpit cruising'),
    ('uss-11', 'Jeanneau sailing yacht blue sky'),
    ('uss-12', 'Hunter cruising sailboat marina'),

    # ── US Sail — mid ────────────────────────────────────────────────────────
    ('uss-21', 'Beneteau Oceanis 46 sailing yacht'),
    ('uss-22', 'Jeanneau Sun Odyssey large sailing yacht'),
    ('uss-23', 'large sailing yacht offshore'),
    ('uss-24', 'Hallberg-Rassy bluewater sailing yacht'),
    ('uss-25', 'Hanse sailing yacht offshore'),
    ('uss-26', 'performance racing sailboat J-Boat'),
    ('uss-27', 'Pacific Seacraft offshore sailing'),
    ('uss-28', 'sailing yacht cabin cruiser'),
    ('uss-29', 'Jeanneau 54 large cruising yacht'),
    ('uss-30', 'sailing yacht open ocean'),
    ('uss-31', 'Oyster bluewater luxury sailing yacht'),
    ('uss-32', 'Beneteau Oceanis 48 sailing'),

    # ── US Sail — premium ────────────────────────────────────────────────────
    ('uss-41', 'Hallberg-Rassy 54 premium sailing yacht'),
    ('uss-42', 'Oyster 575 luxury sailing yacht'),
    ('uss-43', 'large luxury sailing yacht Beneteau'),
    ('uss-44', 'Nautor Swan luxury sailing yacht'),
    ('uss-45', 'Hinckley classic premium sailing yacht'),

    # ── UK Sail — budget ─────────────────────────────────────────────────────
    ('uk-1',   'Beneteau sailing yacht marina Solent'),
    ('uk-2',   'Jeanneau sailing yacht coastal cruising'),
    ('uk-3',   'Bavaria cruising sailboat'),
    ('uk-4',   'Hanse sailing yacht modern'),
    ('uk-5',   'Beneteau Oceanis 38 sailing'),
    ('uk-6',   'Jeanneau 349 sailing yacht'),
    ('uk-7',   'Bavaria 36 sailing cruiser'),
    ('uk-8',   'Hanse 348 sailing yacht'),
    ('uk-9',   'Jeanneau sailing offshore'),
    ('uk-10',  'Beneteau First racing sailboat'),
    ('uk-11',  'Bavaria 38 sailing yacht'),
    ('uk-12',  'Jeanneau Sun Odyssey 40 sailing'),

    # ── UK Sail — mid ────────────────────────────────────────────────────────
    ('uk-21',  'Beneteau Oceanis 46 sailing yacht'),
    ('uk-22',  'Jeanneau Sun Odyssey 490 sailing'),
    ('uk-23',  'Hallberg-Rassy sailing yacht Solent'),
    ('uk-24',  'Bavaria C45 sailing yacht'),
    ('uk-25',  'Oyster 435 bluewater sailing'),
    ('uk-26',  'Southerly lifting keel sailing yacht'),
    ('uk-27',  'Hanse 505 sailing yacht'),
    ('uk-28',  'Bavaria large sailing yacht'),
    ('uk-29',  'Jeanneau 54 sailing yacht'),
    ('uk-30',  'Hallberg-Rassy 43 sailing'),
    ('uk-31',  'Beneteau Oceanis 48 sailing'),
    ('uk-32',  'Bavaria C50 sailing yacht'),

    # ── UK Sail — premium ────────────────────────────────────────────────────
    ('uk-41',  'Oyster 575 luxury sailing yacht'),
    ('uk-42',  'Hallberg-Rassy 54 premium bluewater sailing'),
    ('uk-43',  'Nautor Swan 54 luxury sailing yacht'),
    ('uk-44',  'Beneteau Oceanis 60 large sailing'),
    ('uk-45',  'Oyster 625 luxury bluewater sailing yacht'),
]


def pexels_search(key, query, page=1):
    """Search Pexels; returns list of photo dicts."""
    url = 'https://api.pexels.com/v1/search?' + urllib.parse.urlencode({
        'query': query, 'per_page': 3, 'page': page,
        'orientation': 'landscape'
    })
    req = urllib.request.Request(url, headers={'Authorization': key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())['photos']
    except Exception as e:
        print(f'  ⚠  Search failed: {e}')
        return []


def download_file(url, dest):
    """Download url → dest, return True on success."""
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f'  ⚠  Download failed: {e}')
        return False


def main():
    ap = argparse.ArgumentParser(description='Download boat images for SailShift demos')
    ap.add_argument('--key', required=True, help='Pexels API key')
    ap.add_argument('--out', default=os.path.join(os.path.dirname(__file__), 'images'),
                    help='Output directory (default: demo/images/)')
    ap.add_argument('--skip-existing', action='store_true', default=True,
                    help='Skip folders that already have 3 images (default: on)')
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    total = len(LISTINGS)
    done = 0
    skipped = 0

    for i, (folder, query) in enumerate(LISTINGS, 1):
        dest_dir = os.path.join(args.out, folder)
        os.makedirs(dest_dir, exist_ok=True)

        # Check if already complete
        existing = [f for f in ['1.jpg', '2.jpg', '3.jpg']
                    if os.path.exists(os.path.join(dest_dir, f))]
        if args.skip_existing and len(existing) == 3:
            print(f'[{i:2}/{total}] ✓  {folder} (already complete)')
            skipped += 1
            continue

        print(f'[{i:2}/{total}] ↓  {folder}  "{query}"')

        # Fetch photos across 2 pages for variety
        photos = pexels_search(args.key, query, page=1)
        if len(photos) < 3:
            photos += pexels_search(args.key, query, page=2)

        if not photos:
            print(f'  ✗  No results — skipping {folder}')
            continue

        # Deduplicate by photo id and take up to 3
        seen = set()
        unique = []
        for p in photos:
            if p['id'] not in seen:
                seen.add(p['id'])
                unique.append(p)
            if len(unique) == 3:
                break

        for j, photo in enumerate(unique[:3], 1):
            dest = os.path.join(dest_dir, f'{j}.jpg')
            if os.path.exists(dest):
                continue
            url = photo['src'].get('large', photo['src']['original'])
            ok = download_file(url, dest)
            status = '✓' if ok else '✗'
            print(f'  {status} {j}.jpg  ({photo["id"]})')
            time.sleep(0.2)  # polite rate limit

        done += 1
        time.sleep(0.5)

    print(f'\nDone. {done} downloaded, {skipped} skipped.')
    print(f'Images saved to: {args.out}')


if __name__ == '__main__':
    import urllib.parse
    main()
