# Vermont census viewers

Maps of Vermont villages around 1900 and 1910. Each building lists the people living there in the census.
Each town and census year has its own folder with its data, settings and static site. The scripts are shared:

```
scripts/         the pipeline, shared by every town (run from the repo root, town name first)
bellows-falls/   Bellows Falls village (Rockingham, Windham Co.), ED 259, with 1896 Sanborn maps
winooski/        Winooski village (Colchester, Chittenden Co.), 1900, EDs 75 and 76
winooski-1910/   Winooski village, 1910, EDs 76 and 77
```

Each town folder holds:

```
town.json        the town's settings (below)
data/img/        FamilySearch page images, named ED-SHEET.jpg (e.g. 75-01A.jpg); not committed
data/transcribed/  one CSV per page
data/output/     built per-person CSV and geocoded addresses
site/            the town's map
```

## Scripts

```
fs_tiles.py           cuts a page into readable strips (left/right halves in 5 line bands, street column, overview)
crop.py               zooms into one region of a page (used for manual checks)
transcribe_batch.py   transcribes pages with Claude Opus 5.5 through the Message Batches API (batch price only)
compare_csv.py        compares two transcriptions of the same page, cell by cell
build_csv.py          fills dittos, checks ages, maps birthplaces to flags, writes data/output/
geocode.py            geocodes each numbered address with the Mapbox v6 API
build_site_data.py    builds site/data/census_1900.geojson for the map
town.py               loads a town's town.json and its paths
schedules.py          what differs between census years: columns, census day, prompt text for each column
```

For example:

```
python3 -I scripts/transcribe_batch.py winooski submit --all
python3 -I scripts/transcribe_batch.py winooski collect
python3 -I scripts/build_csv.py winooski
python3 -I scripts/geocode.py winooski
python3 -I scripts/build_site_data.py winooski
```

The scripts run with plain `python3`. They need `pillow`; `transcribe_batch.py` also needs `anthropic`.
`bellows-falls/data/README.md` covers the transcription format, the build outputs and their caveats.

## `town.json`

- `year` (optional, default 1900): the census year, 1900 or 1910. It picks the columns and prompt in
  `scripts/schedules.py` and names the outputs (`people_1910.csv`, `census_1910.geojson`).
- `name`, `place`: the town's name and a description of the place, used in the transcription prompt.
- `eds`: each enumeration district number and what it covers.
- `street_examples`: a few street names as written on the pages, shown to the model as examples.
- `examples`: finished page CSVs (paths from the repo root) given to the model as the worked example. The
  second is used when transcribing the first. It can be empty, and the prompt then has no worked example.
- `layout` (optional): where lines 1 and 50 sit on the page (`line1`, `line50`, as fractions of page
  height), how many extra lines each tile band includes above and below (`overlap`), and the columns as
  fractions of page width: where the left tiles end (`left_x1`) and the right tiles start (`right_x0`), the
  street column (`street_x`) and the number and name columns (`names_x`). For scans where the form sits at a
  different height on each image (Winooski 1910), `free_bands` (`top`, `bottom`, `n`, `pad`, as fractions of
  page height) replaces the line positions: the page is cut into `n` evenly spaced, overlapping bands, and the
  model lines them up by the printed line numbers. Defaults are in
  `scripts/town.py`. Check a few pages' tiles with `fs_tiles.py PAGE.jpg OUT_DIR TOWN` before a batch run.
- `street_aliases` (optional): maps a street as transcribed to the name to use for addresses and geocoding,
  for spelling variants (`"Leclare": "Leclair"`). Without a suffix, " St" is added; a name ending in a
  suffix such as Avenue is kept as is.
- `geocode`: the place name, proximity point and bounding box sent to the geocoder.

The census page images come from FamilySearch and aren't included in this repo. Each town's
`data/README.md` explains how to download them.
