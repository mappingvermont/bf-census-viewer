"""Assemble per-sheet census transcriptions into one per-person CSV.

Usage: python3 -I scripts/build_csv.py TOWN

Input: one CSV per census page side in TOWN/data/transcribed/ (e.g. 259-43A.csv), exactly as written on
the page. A blank surname, street, house number, dwelling or family number means "same as
the row above" (a ditto). "^" means the value continues from the previous sheet.

Output, in TOWN/data/output/:
  people_YEAR.csv  one row per person (YEAR is the town's census year), dittos filled in, plus address key, birth country,
                   flag emoji and validation warnings
"""
import csv
import glob
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import town  # noqa: E402

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
    "Canada (Irish)": ("English Canada", "🇨🇦"),
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
    "Austria Hungary": ("Austria-Hungary", "🇦🇹"),
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
    "Canada (Am. Cit.)": ("Canada", "🇨🇦"),
    "Poland (Russ)": ("Poland", "🇵🇱"),
    "Poland (Ger)": ("Poland", "🇵🇱"),
    "Poland (Aust)": ("Poland", "🇵🇱"),
    "England (Scotland)": ("Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"),
    "Bermuda (Eng)": ("Bermuda", "🇧🇲"),
    "India": ("India", "🇮🇳"),
    "America": ("United States", "🇺🇸"),
    "Washington D.C.": ("United States", "🇺🇸"),
    "At sea (Am. Cit.)": ("United States", "🇺🇸"),
}
US = ("United States", "🇺🇸")
UNKNOWN = ("Unknown", "")
NAMED_SUFFIXES = {"Avenue", "Terrace", "Place", "Court", "Ct", "Park", "Island", "Hill", "Lane"}

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


def sheet_key(path):
    m = re.search(r"(\d+)-(\d+)([AB])", os.path.basename(path))
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, path)


def age_warning(r):
    """Census day was 1 June 1900; age = completed years on that day. Only the 1900 form has a birth date."""
    try:
        year = int(r.get("birth_year", ""))
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


def main(src, out, aliases=None, year=1900):
    aliases = aliases or {}
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
                    if k in r and r[k] in ("", "^"):
                        r[k] = prev.get(k, "")
                r["street"] = aliases.get(r["street"], r["street"])
                # house number / dwelling belong to the dwelling: carry them only while
                # still in the same dwelling (a new dwelling with no number stays blank).
                if new_dwelling:
                    if r["house_num"] in ("", "^"):
                        r["house_num"] = ""
                else:
                    for k in ("dwelling", "dwelling_renum", "house_num"):
                        if k in r:
                            r[k] = prev.get(k, "")
                prev = r
                rows.append(r)

    people = []
    unmapped = Counter()
    for r in rows:
        bc_label, bc_flag = country(r["birthplace"])
        for bp in (r["birthplace"], r["father_bp"], r["mother_bp"]):
            if bp and country(bp)[1] == "" and country(bp) != UNKNOWN:
                unmapped[bp] += 1
        if r["street"] == "Square":
            street = "The Square"
        elif r["street"].split()[-1] in NAMED_SUFFIXES:  # "Butterfield Avenue", not "... Avenue St"
            street = r["street"]
        else:
            street = f"{r['street']} St"
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
            "street_name": street,
            "birth_country": bc_label,
            "birth_flag": bc_flag,
            "check": warn,
        })

    fields = list(people[0].keys()) if people else []
    with open(os.path.join(out, f"people_{year}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(people)

    print(f"{len(files)} sheet(s), {len(people)} people, {len({p['address'] for p in people})} addresses")
    flagged = [p for p in people if p["uncertain"] == "1"]
    print(f"{len(flagged)} rows marked uncertain")
    for p in people:
        if p["check"]:
            print(f"  CHECK {p['sheet']} line {p['line']}: {p['name']}: {p['check']}")
    for bp, n in unmapped.items():
        print(f"  UNMAPPED birthplace '{bp}' x{n} - add it to COUNTRIES")


if __name__ == "__main__":
    t = town.load(sys.argv[1])
    main(t.transcribed, t.output, getattr(t, "street_aliases", {}), t.year)
