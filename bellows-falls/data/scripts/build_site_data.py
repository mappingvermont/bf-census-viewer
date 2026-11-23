"""Build the map's GeoJSON from people_1900.csv and the geocoded addresses.

Usage: python3 -I scripts/build_site_data.py output ../site/data/census_1900.geojson

One feature per address. Addresses that couldn't be geocoded get a null geometry: the site
lists them but can't pin them. `birth_counts` counts residents over 16 by birth country,
most common first; the site shows every country tied for the top count as the house's flag.
Infants' fractional ages ("8/12") and blank ages count as not over 16.
"""
import csv
import json
import sys
from collections import Counter

ADULT_OVER = 16


def is_adult(age):
    try:
        return float(age) > ADULT_OVER
    except ValueError:
        return False  # blank, or an infant fraction like 8/12


def main(outdir, dst):
    people = list(csv.DictReader(open(f"{outdir}/people_1900.csv")))
    located = json.load(open(f"{outdir}/geocoded_1900.json"))

    by_addr = {}
    for p in people:
        by_addr.setdefault(p["address"], []).append(p)

    features = []
    for addr, residents in by_addr.items():
        g = located.get(addr)
        adults = [p for p in residents if is_adult(p["age"])]
        counts = Counter((p["birth_country"], p["birth_flag"])
                         for p in adults if p["birth_country"] != "Unknown")
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [g["lon"], g["lat"]]} if g else None,
            "properties": {
                "address": addr,
                "street": residents[0]["street"],
                "house_num": residents[0]["house_num"],
                "sheets": sorted({p["sheet"] for p in residents}),
                "people": len(residents),
                "adults": len(adults),
                "geocode_confidence": g["confidence"] if g else None,
                "birth_counts": [{"country": c, "flag": f, "n": n} for (c, f), n in
                                 sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0]))],
                "residents": [{
                    "name": p["name"],
                    "age": p["age"],
                    "sex": p["sex"],
                    "relation": p["relation"],
                    "birthplace": p["birthplace"],
                    "birth_flag": p["birth_flag"],
                    "father_bp": p["father_bp"],
                    "mother_bp": p["mother_bp"],
                    "occupation": p["occupation"],
                    "adult": is_adult(p["age"]),
                    "uncertain": p["uncertain"] == "1",
                } for p in residents],
            },
        })
    collection = {
        "type": "FeatureCollection",
        "sheets_transcribed": len({p["sheet"] for p in people}),
        "features": features,
    }
    json.dump(collection, open(dst, "w"), ensure_ascii=False, indent=1)
    unplaced = sum(1 for f in features if f["geometry"] is None)
    print(f"wrote {len(features)} houses ({unplaced} without a location) to {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
