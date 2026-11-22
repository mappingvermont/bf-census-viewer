"""Geocode output/addresses_1900.json with the Mapbox v6 forward geocoding API.

Usage: python3 -I scripts/geocode.py output/addresses_1900.json output/geocoded_1900.json

Needs MAPBOX_ACCESS_TOKEN. Results are cached in the output file: an address already
geocoded there is not requested again. Addresses with no house number are skipped
(they can't be placed). Each result keeps the match quality so weak matches can be
reviewed by hand: modern numbering may differ from 1900.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

PROXIMITY = "-72.4441,43.1338"  # Bellows Falls village centre
BBOX = "-72.47,43.12,-72.43,43.15"


def geocode(street_line, token):
    params = {
        "address_number": street_line[0],
        "street": street_line[1],
        "place": "Bellows Falls",
        "region": "Vermont",
        "country": "us",
        "types": "address",
        "proximity": PROXIMITY,
        "bbox": BBOX,
        "limit": 1,
        "access_token": token,
    }
    url = "https://api.mapbox.com/search/geocode/v6/forward?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        feats = json.load(r).get("features", [])
    if not feats:
        return None
    f = feats[0]
    p = f["properties"]
    return {
        "lon": f["geometry"]["coordinates"][0],
        "lat": f["geometry"]["coordinates"][1],
        "matched": p.get("full_address"),
        "match_code": p.get("match_code", {}),
    }


def main(src, dst):
    token = os.environ["MAPBOX_ACCESS_TOKEN"]
    cache = {}
    if os.path.exists(dst):
        for a in json.load(open(dst)):
            if a.get("geocode"):
                cache[a["address"]] = a["geocode"]
    out = []
    for a in json.load(open(src)):
        g = None
        if a["house_num"]:
            g = cache.get(a["address"]) or geocode((a["house_num"], a["street"] + " Street"), token)
        a = dict(a, geocode=g)
        out.append(a)
        mc = (g or {}).get("match_code", {})
        print(f'{a["address"]:<45} -> {(g or {}).get("matched", "SKIPPED" if not a["house_num"] else "NO MATCH")}'
              f'  [{mc.get("confidence", "")}; house {mc.get("address_number", "")}, street {mc.get("street", "")}]')
    json.dump(out, open(dst, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:3])
