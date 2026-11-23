"""Geocode each numbered address in people_YEAR.csv with the Mapbox v6 forward geocoding API.

Usage: python3 -I scripts/geocode.py TOWN

Reads TOWN/data/output/people_YEAR.csv and writes TOWN/data/output/geocoded_YEAR.json. The place name,
proximity point and bounding box come from the `geocode` settings in TOWN/town.json.

Needs MAPBOX_ACCESS_TOKEN. The output maps address -> {lon, lat, matched, confidence} and
doubles as a cache: addresses already in it aren't requested again. Addresses with no house
number can't be placed and are skipped. Confidence is the geocoder's (`exact`, `high`,
`medium`, `low`); modern numbering may differ from 1900, so review anything below exact.
"""
import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import town  # noqa: E402


def geocode(house_num, street, token, g):
    params = {
        "address_number": house_num,
        "street": street,
        "place": g["place"],
        "region": "Vermont",
        "country": "us",
        "types": "address",
        "proximity": ",".join(map(str, g["proximity"])),
        "bbox": ",".join(map(str, g["bbox"])),
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
    lon, lat = f["geometry"]["coordinates"]
    return {"lon": lon, "lat": lat, "matched": p.get("full_address"),
            "confidence": p.get("match_code", {}).get("confidence")}


def main(people_csv, dst, g):
    token = os.environ["MAPBOX_ACCESS_TOKEN"]
    cache = json.load(open(dst)) if os.path.exists(dst) else {}
    addresses = {}
    for p in csv.DictReader(open(people_csv)):
        if p["house_num"]:
            addresses.setdefault(p["address"], (p["house_num"], p["street_name"]))
    for addr, (num, street) in addresses.items():
        if addr not in cache:
            cache[addr] = geocode(num, street, token, g)
        whole = re.match(r"\d+", num)
        if cache[addr] is None and whole and whole.group() != num:
            # "23 1/2", "8½", "12 R": the geocoder rejects these, so place them at the whole number.
            hit = geocode(whole.group(), street, token, g)
            if hit:
                hit["note"] = f"placed at {whole.group()}"
            cache[addr] = hit
        hit = cache[addr] or {}
        print(f"{addr:<25} -> {hit.get('matched', 'NO MATCH')}  [{hit.get('confidence', '')}]")
    json.dump(cache, open(dst, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    t = town.load(sys.argv[1])
    main(os.path.join(t.output, f"people_{t.year}.csv"), os.path.join(t.output, f"geocoded_{t.year}.json"),
         t.geocode)
