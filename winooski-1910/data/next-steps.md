# Next steps: Winooski 1910

**Why 1910:** the 1900 Winooski census (`../../winooski`) has a house number for only 62 of 3,783 people (14
addresses, all in ED 76). The 1900 enumerators left the house-number column blank, so those households can't be
geocoded. The 1910 census has house numbers.

Billing, the API key and the no-full-price rule are the same as for Bellows Falls. Read "Notes for agents" and
"No full-price runs" in `../../bellows-falls/data/next-steps.md` first. In short: **ask before every `submit`**,
use only the Keychain key, and never use a full-price path.

## Where things stand (2026-11-23)
- All 97 page images are in `img/` and named (see `../README.md` for the quirks: missing 76-07B, back-to-front
  76-12).
- The scripts handle 1910 (`"year": 1910` in `town.json`, columns and prompt in `scripts/schedules.py`, tiling
  with `free_bands`). This hasn't been committed yet.
- **A 2-page test batch is in flight:** `msgbatch_01WRemQvc9aLZi6HkeRzGj8X`, pages 76-01B (an easy page
  with clear house numbers) and 77-07A (the lowest-placed scan, lines 45–50 blank), written to `test_batch/`.
  It was submitted 2026-11-23 with no worked example in the prompt.

## 1. Collect and check the test
```
python3 -I scripts/transcribe_batch.py winooski-1910 collect --out winooski-1910/data/test_batch
```
`collect` is free. Then check both CSVs against the images (`scripts/crop.py` zooms; `fs_tiles.py PAGE.jpg OUT
winooski-1910` shows the tiles the model saw). Look especially at:
- **House numbers and streets.** They're what puts people on the map.
- **Line alignment across bands.** The tiles don't start on fixed lines, so look for skipped or duplicated
  lines and rows shifted between the left and right tiles (e.g. an occupation on the wrong person).
- **The far-right columns 29–32.** They should be blank. The census office's coding numbers ("12 2 9 X") are
  written there and must not end up in `farm_schedule`, `veteran`, `blind` or `deaf_dumb`.
- **Birthplace and mother tongue.** "Can French" should become `Canada (Fr)` with `French` in `tongue`.
- **Cost per page** in `test_batch/_usage.jsonl`. It should be about half the list price.

If the bands or column splits miss text, adjust `layout` in `../town.json` and re-check the tiles before
spending more.

## 2. Make a worked example
Have the user correct one test page by hand, copy it into `transcribed/`, and list it in `examples` in
`../town.json` (ideally two pages, so the first can be transcribed with the second as its example).

## 3. Run the rest (ask first: about $17–20 for 95 pages)
```
python3 -I scripts/transcribe_batch.py winooski-1910 submit --all
python3 -I scripts/transcribe_batch.py winooski-1910 collect
python3 -I scripts/build_csv.py winooski-1910
python3 -I scripts/geocode.py winooski-1910        # needs MAPBOX_ACCESS_TOKEN
python3 -I scripts/build_site_data.py winooski-1910
```
- `--all` skips pages that already have a CSV in `transcribed/`.
- `build_csv.py` has no age check for 1910 (no birth date on the form). Add any `UNMAPPED` birthplaces to
  `COUNTRIES`.

## 4. The map
There's no `site/` yet. Copy `../../winooski/site/` or `../../bellows-falls/site/`, point it at
`data/census_1910.geojson`, and add the 1910-only fields (industry, employer class, mother tongue) to
`build_site_data.py` and the popup if they're wanted.

A later idea: link 1900 households to their 1910 addresses by name to place the 1900 Winooski map.
