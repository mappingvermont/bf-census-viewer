# Bellows Falls 1900 census

Per-person records from the 1900 US census for Bellows Falls village, Vermont. They're meant to be joined to
georeferenced 1896 Sanborn fire-insurance maps of the village. On the map, each building will show an emoji
flag for the most common nationality of the people living there. Clicking a building footprint will list the
name, age, sex and birthplace of everyone in it.

The 1890 census was almost entirely destroyed, so 1900 is the closest per-address source to the 1896 maps. In
towns, the 1900 enumerators wrote the street and house number on each line, which is what makes the join to
buildings possible.

## Source

- **Collection:** FamilySearch, "United States, Census, 1900"
  (https://www.familysearch.org/en/search/collection/1325221). It's free with an account, and has no bulk
  download.
- **Coverage:** Vermont → Windham Co. → Rockingham town → **Enumeration District 259**, Bellows Falls village.
  ED 258 is rural Rockingham and isn't included.
- **Pages:** 87 page images, sheets 1A to 44A. Sheet 44B is a blank form. Each sheet has an A side
  (lines 1–50) and a B side (lines 51–100).
- **Images:** about 3700×3600 px, saved as `img/259-01A.jpg` … `img/259-44A.jpg`. They
  aren't in this repo. Download them from FamilySearch's image viewer (ED 259, one image per page side) and
  name each file by its ED and sheet, with sheets 1–9 zero-padded (`259-01A`).

## Layout

```
img/            page images, one per census page side (259-SSX.jpg); not committed
transcribed/    one CSV per page, exactly as written on the page (dittos left blank)
output/         built outputs, regenerated from transcribed/ by build_csv.py
scripts/
  fs_tiles.py           cuts a page into readable strips (left/right halves in 5 line bands, street column, overview)
  crop.py               zooms into one region of a page (used for manual checks)
  transcribe_bedrock.py transcribes pages with Claude Opus 5.5 on Bedrock, one request per page
  compare_csv.py        compares two transcriptions of the same page, cell by cell
  build_csv.py          fills dittos, checks ages, maps birthplaces to flags, writes output/
PROMPT_transcribe_page.md  prompt for transcribing one page in an interactive Claude Code session
```

The scripts run with plain `python3`. They need `pillow` and `anthropic[bedrock]`.

## Transcription format (`transcribed/PAGE.csv`)

There are 40 columns, one row per person, matching every column on the 1900 form:
`image, ed, sheet, line, street, house_num, dwelling, dwelling_renum, family, family_renum, surname, given,
relation, race, sex, birth_month, birth_year, age, marital, years_married, children_born, children_living,
birthplace, father_bp, mother_bp, immig_year, years_in_us, naturalization, occupation, months_unemployed,
school_months, can_read, can_write, speaks_english, home_owned_rented, home_free_mortgaged, farm_or_house,
farm_schedule, uncertain, notes`

Conventions. `transcribed/259-43A.csv` is the reference example.
- **Street:** the bare name (`Atkinson`, `Westminster`, `Hapgood`, `Square`), written on every row.
- **Dittos are left blank** as on the page: blank surname under a dash, and blank dwelling/house number when a
  new family shares the dwelling above. `^` on a page's first line means the value carries over from the
  previous sheet.
- **Two sets of numbers.** `dwelling`/`family` are the enumerator's dark-ink numbers. The `_renum` columns
  are the lighter renumbering written above them.
- **Ignored:** the grey tally marks the census office wrote over names and relations.
- **Birthplaces:** full names. `Canada (Fr)` and `Canada (Eng)` are kept as written.
- **Uncertainty:** `uncertain` = 1 when any cell in the row is a guess. `notes` says which cell and gives the
  alternative reading. Unreadable cells are left blank, never guessed.

## Building the outputs

```
python3 -I scripts/build_csv.py transcribed output
```

This writes:
- `output/people_1900.csv`: one row per person, with dittos filled in. It adds `name`, `address`,
  `birth_country`/`birth_flag`, `heritage_country`/`heritage_flag` and an age `check`.
- `output/addresses_1900.csv`: one row per address, with head count and the most common birth and heritage
  country and flag.
- `output/addresses_1900.json`: the same addresses, each with its residents. This is the shape the map popups
  will read.

It also prints:
- `CHECK` lines where an age doesn't fit the birth month and year (census day was 1 June 1900),
- `UNMAPPED` lines for birthplaces missing from `COUNTRIES` in `build_csv.py`. Add them there with a flag.

**Birth vs heritage country.** Most people in Bellows Falls were born in New England, including many children
of immigrants, so nearly every address comes out 🇺🇸 by birthplace. "Heritage" is the person's own birthplace
if it's foreign, otherwise the father's, otherwise the mother's. It surfaces the Irish, French-Canadian and
German households. Both are kept, and the map can use either.

Addresses are `"<house_num> <Street> St"` (`The Square` for Square). A dwelling with no house number written
gets a placeholder that includes its dwelling number.

## Transcribing a page

- **Several pages at once, on Bedrock (on demand, not Claude batch mode):**
  `python3 -I scripts/transcribe_bedrock.py --profile <aws-profile> --out transcribed PAGE ...`
  (or `--all`). This sends one request per page to Claude Opus 5.5 and needs no API key; it bills the AWS
  account of `--profile`. Pages that already have a CSV in `--out` are skipped. Token use and estimated cost
  per page go to `_usage.jsonl` in the `--out` folder.
- **Interactive, one page at a time:** open a fresh Claude Code session in this folder and paste in
  `PROMPT_transcribe_page.md` with `PAGE` set.

To check a transcription against another one, run
`python3 -I scripts/compare_csv.py REFERENCE.csv TEST.csv`.

Either way, run `build_csv.py` afterwards and review the `CHECK` and `UNMAPPED` lines and the rows marked
uncertain.

## Caveats

- **Street names change.** They and the house numbering may differ between 1896 and 1900, and from today's,
  so some addresses need matching to buildings by hand.
- **Handwriting is hard.** Rows marked uncertain are common, mostly hard-to-read names and overwritten numbers.
  Spot-check them against the images before relying on them.
