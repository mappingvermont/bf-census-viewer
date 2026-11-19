"""Assemble per-sheet census transcriptions into per-person and per-address outputs.

Usage: python -I build_csv.py <transcribed_dir> <output_dir>

Input: one CSV per census page side (e.g. transcribed/259-43A.csv), exactly as written on
the page. A blank surname, street, house number, dwelling or family number means "same as
the row above" (a ditto). "^" means the value continues from the previous sheet.

Output:
  people_1900.csv     one row per person, dittos filled in, plus address key, birth
                      country, heritage country, flag emoji and validation warnings
  addresses_1900.csv  one row per address: head count, most common birth country + flag,
                      most common heritage country + flag
  addresses_1900.json the same addresses, each with its list of people (for map popups)
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

US_STATES = {
    "Alabama", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "District of Columbia", "Florida", "Georgia", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming", "United States", "At Sea",
}

# Birthplace as written -> (country label, flag). Historical places are mapped to the
# modern flag of the same place; French and English Canada are kept apart.
COUNTRIES = {
    "Canada (Fr)": ("French Canada", "🇨🇦"),
    "Canada (Eng)": ("English Canada", "🇨🇦"),
    "Canada": ("Canada", "🇨🇦"),
    "Ireland": ("Ireland", "🇮🇪"),
    "England": ("England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "Scotland": ("Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"),
    "Wales": ("Wales", "🏴󠁧󠁢󠁷󠁬󠁳󠁿"),
    "Germany": ("Germany", "🇩🇪"),
    "Prussia": ("Germany", "🇩🇪"),
    "Bavaria": ("Germany", "🇩🇪"),
    "France": ("France", "🇫🇷"),
    "Italy": ("Italy", "🇮🇹"),
    "Sweden": ("Sweden", "🇸🇪"),
    "Norway": ("Norway", "🇳🇴"),
    "Denmark": ("Denmark", "🇩🇰"),
    "Switzerland": ("Switzerland", "🇨🇭"),
    "Austria": ("Austria", "🇦🇹"),
    "Hungary": ("Hungary", "🇭🇺"),
    "Poland": ("Poland", "🇵🇱"),
    "Russia": ("Russia", "🇷🇺"),
    "Finland": ("Finland", "🇫🇮"),
    "Holland": ("Netherlands", "🇳🇱"),
    "Netherlands": ("Netherlands", "🇳🇱"),
    "Belgium": ("Belgium", "🇧🇪"),
    "Portugal": ("Portugal", "🇵🇹"),
    "Spain": ("Spain", "🇪🇸"),
    "Greece": ("Greece", "🇬🇷"),
    "Syria": ("Syria", "🇸🇾"),
    "Turkey": ("Turkey", "🇹🇷"),
    "China": ("China", "🇨🇳"),
    "Cuba": ("Cuba", "🇨🇺"),
    "Mexico": ("Mexico", "🇲🇽"),
    "Nova Scotia": ("English Canada", "🇨🇦"),
    "New Brunswick": ("English Canada", "🇨🇦"),
    "Quebec": ("French Canada", "🇨🇦"),
}
US = ("United States", "🇺🇸")
UNKNOWN = ("Unknown", "")

FILL_DOWN = ["street", "surname", "family", "family_renum"]
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"], 1)}


def country(bp):
    bp = (bp or "").strip()
    if not bp or bp.lower() == "unknown":
        return UNKNOWN
    if bp in US_STATES:
        return US
    if bp in COUNTRIES:
        return COUNTRIES[bp]
    return (bp, "")  # unmapped: keep the label, no flag; reported as a warning


def heritage(r):
    """First foreign country among self, father, mother; else United States."""
    for bp in (r["birthplace"], r["father_bp"], r["mother_bp"]):
        c = country(bp)
        if c not in (US, UNKNOWN):
            return c
    return US if country(r["birthplace"]) == US else UNKNOWN


def sheet_key(path):
    m = re.search(r"(\d+)-(\d+)([AB])", os.path.basename(path))
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, path)


def age_warning(r):
    """Census day was 1 June 1900; age = completed years on that day."""
    try:
        year = int(r["birth_year"])
    except ValueError:
        return ""
    age_txt = r["age"]
    if "/" in age_txt:  # infants: months/12
        expected_ok = year in (1899, 1900)
        return "" if expected_ok else f"infant age {age_txt} vs birth {year}"
    try:
        age = int(age_txt)
    except ValueError:
        return ""
    month = MONTHS.get(r["birth_month"])
    if month is None:
        ok = age in (1899 - year, 1900 - year)
    else:
        ok = age == (1900 - year if month <= 5 else 1899 - year)
    return "" if ok else f"age {age} inconsistent with {r['birth_month']} {year}"


def main(src, out):
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src, "*.csv")), key=sheet_key)
    rows, prev = [], {}
    for path in files:
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                for k in r:
                    r[k] = (r[k] or "").strip()
                new_dwelling = r["dwelling"] not in ("", "^")
                for k in FILL_DOWN:
                    if r[k] in ("", "^"):
                        r[k] = prev.get(k, "")
                # house number / dwelling belong to the dwelling: carry them only while
                # still in the same dwelling (a new dwelling with no number stays blank).
                if new_dwelling:
                    if r["house_num"] in ("", "^"):
                        r["house_num"] = ""
                else:
                    for k in ("dwelling", "dwelling_renum", "house_num"):
                        r[k] = prev.get(k, "")
                prev = r
                rows.append(r)

    people = []
    unmapped = Counter()
    for r in rows:
        bc_label, bc_flag = country(r["birthplace"])
        h_label, h_flag = heritage(r)
        for bp in (r["birthplace"], r["father_bp"], r["mother_bp"]):
            if bp and country(bp)[1] == "" and country(bp) != UNKNOWN:
                unmapped[bp] += 1
        street = "The Square" if r["street"] == "Square" else f"{r['street']} St"
        if r["house_num"]:
            addr = f"{r['house_num']} {street}"
        elif r["dwelling"]:
            addr = f"{street} (dwelling {r['dwelling']}, no house no.)"
        else:
            addr = f"{street} (household from sheet before {r['sheet']})"
        warn = age_warning(r)
        people.append({
            **r,
            "name": f"{r['given']} {r['surname']}".strip(),
            "address": addr,
            "birth_country": bc_label,
            "birth_flag": bc_flag,
            "heritage_country": h_label,
            "heritage_flag": h_flag,
            "check": warn,
        })

    fields = list(people[0].keys()) if people else []
    with open(os.path.join(out, "people_1900.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(people)

    by_addr = {}
    for p in people:
        by_addr.setdefault(p["address"], []).append(p)

    def top(counter):
        # most common; ties broken in favour of a foreign country, then alphabetically
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0] == "United States", kv[0]))[0][0]

    addr_rows, addr_json = [], []
    flag_of = {lbl: flg for lbl, flg in list(COUNTRIES.values()) + [US]}
    for addr, ps in by_addr.items():
        bc = top(Counter(p["birth_country"] for p in ps if p["birth_country"] != "Unknown") or Counter(["Unknown"]))
        hc = top(Counter(p["heritage_country"] for p in ps if p["heritage_country"] != "Unknown") or Counter(["Unknown"]))
        row = {
            "address": addr,
            "street": ps[0]["street"],
            "house_num": ps[0]["house_num"],
            "dwellings": " ".join(sorted({p["dwelling"] for p in ps})),
            "sheets": " ".join(sorted({p["sheet"] for p in ps})),
            "people": len(ps),
            "top_birth_country": bc,
            "top_birth_flag": flag_of.get(bc, ""),
            "top_heritage_country": hc,
            "top_heritage_flag": flag_of.get(hc, ""),
        }
        addr_rows.append(row)
        addr_json.append({**row, "residents": [
            {k: p[k] for k in ("name", "age", "sex", "relation", "birthplace", "birth_country",
                                "birth_flag", "father_bp", "mother_bp", "occupation")}
            for p in ps]})

    with open(os.path.join(out, "addresses_1900.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(addr_rows[0].keys()))
        w.writeheader()
        w.writerows(addr_rows)
    with open(os.path.join(out, "addresses_1900.json"), "w", encoding="utf-8") as f:
        json.dump(addr_json, f, ensure_ascii=False, indent=1)

    print(f"{len(files)} sheet(s), {len(people)} people, {len(addr_rows)} addresses")
    flagged = [p for p in people if p["uncertain"] == "1"]
    print(f"{len(flagged)} rows marked uncertain")
    for p in people:
        if p["check"]:
            print(f"  CHECK {p['sheet']} line {p['line']}: {p['name']}: {p['check']}")
    for bp, n in unmapped.items():
        print(f"  UNMAPPED birthplace '{bp}' x{n} - add it to COUNTRIES")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
