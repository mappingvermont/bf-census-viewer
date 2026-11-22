"""Build the map's GeoJSON from people_1900.csv and the geocoded addresses.

Usage: python3 -I scripts/build_site_data.py output ../site/data/census_1900.geojson

One point per geocoded address. Each house gets the flag(s) of the plurality birth country
among its residents over 16. Ties keep every tied country, so a house can show more than one
flag. Infants' fractional ages ("8/12") and blank ages count as not over 16. Addresses that couldn't be geocoded are
listed on stderr and left out.
"""
import csv
import json
import sys
from collections import Counter

ADULT_OVER = 16


def age_num(age):
    try:
        return float(age)
    except ValueError:
        return None  # blank, or an infant fraction like 8/12


def plurality(people, country_key, flag_key):
    counts = Counter((p[country_key], p[flag_key]) for p in people if p[country_key])
    if not counts:
        return []
    top = max(counts.values())
    return [{"country": c, "flag": f, "count": n} for (c, f), n in counts.most_common() if n == top]


def main(outdir, dst):
    people = list(csv.DictReader(open(f"{outdir}/people_1900.csv")))
    places = {a["address"]: a for a in json.load(open(f"{outdir}/geocoded_1900.json"))}

    by_addr = {}
    for p in people:
        by_addr.setdefault(p["address"], []).append(p)

    features = []
    for addr, residents in by_addr.items():
        g = (places.get(addr) or {}).get("geocode")
        if not g:
            print(f"not geocoded, left off the map: {addr} ({len(residents)} people)", file=sys.stderr)
            continue
        adults = [p for p in residents if (age_num(p["age"]) or 0) > ADULT_OVER]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [g["lon"], g["lat"]]},
            "properties": {
                "address": addr,
                "street": residents[0]["street"],
                "house_num": residents[0]["house_num"],
                "sheets": sorted({p["sheet"] for p in residents}),
                "people": len(residents),
                "adults": len(adults),
                "geocode_match": g.get("matched"),
                "geocode_confidence": g.get("match_code", {}).get("confidence"),
                "top_birth": plurality(adults, "birth_country", "birth_flag"),
                "residents": [{
                    "name": p["name"],
                    "age": p["age"],
                    "sex": p["sex"],
                    "relation": p["relation"],
                    "birthplace": p["birthplace"],
                    "father_bp": p["father_bp"],
                    "mother_bp": p["mother_bp"],
                    "birth_country": p["birth_country"],
                    "birth_flag": p["birth_flag"],
                    "occupation": p["occupation"],
                    "adult": (age_num(p["age"]) or 0) > ADULT_OVER,
                    "uncertain": p["uncertain"] == "1",
                } for p in residents],
            },
        })
    json.dump({"type": "FeatureCollection", "features": features},
              open(dst, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {len(features)} houses to {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
