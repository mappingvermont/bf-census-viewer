# Winooski 1910 census

The 1910 US census for Winooski village, Vermont, built with the shared scripts in `../scripts`. The 1900
census for Winooski (`../winooski`) has almost no house numbers. The 1910 one has them, so its households can
be placed at real addresses.

`town.json` sets `"year": 1910`, which picks the 1910 columns and prompt from `scripts/schedules.py`. The 1910
form has no birth month or year. For people born abroad it adds the mother tongue, plus industry, employer
class, school attendance and Civil War veteran columns. Outputs are `data/output/people_1910.csv`,
`geocoded_1910.json` and `site/data/census_1910.geojson`.

`examples` is empty until a 1910 page has been checked by hand. Until then the prompt has no worked example.

`layout` uses `free_bands` instead of fixed line positions. The FamilySearch images are the page inside a black
border of varying size, so line 1 sits anywhere from about 15% to 31% of the way down the image. Fitting the
printed rules automatically proved unreliable on skewed or half-empty pages. Instead each page is cut into 6
evenly spaced, overlapping bands from 14% to 99% of the height, and the model aligns them by the printed line
numbers. The column splits (`left_x1` 0.63, `right_x0` 0.52) put occupation and industry fully in the right
tiles. The line spacing is the same on every image (about 40 px), so the scans share one resolution.

`data/output/people_1910.csv` keeps every 1910 column, including industry, employer class and mother tongue.
`build_site_data.py` passes only the shared fields (name, age, relation, birthplaces, occupation) to the map, so
to show the 1910-only columns on the map, add them there and in the site's popup.

## Source

- **Collection:** FamilySearch, "United States, Census, 1910"
  (https://www.familysearch.org/en/search/collection/1727033), filed under Vermont → Chittenden → Colchester.
- **Enumeration districts** (NARA T624, roll 1614):
  - **ED 76**: Winooski village (part), East and South Wards: south of the Central Vermont Railroad track and
    east of the center of Main Street.
  - **ED 77**: Winooski village (part), West Ward: north of the railroad track and west of the center of Main
    Street.

  ED 75 (Colchester town outside the village) and ED 78 (Fort Ethan Allen) aren't included. ED numbers are from
  the [USGenWeb index for roll 1614](https://www.us-census.org/states/vermont/teams/Chittenden1910-T624-1614.htm).
  The 1910 ED numbers aren't the same as 1900's: 1900's ED 76 is East and South Wards too, but 1900's West Ward
  was ED 75.
- **Images:** not in this repo. Save one image per page side into `data/img/`, named by ED and sheet with
  sheets 1–9 zero-padded: `76-01A.jpg`, `76-01B.jpg` … `77-01A.jpg` …. An A side has lines 1–50, a B side
  lines 51–100. `data/img_sources.csv` maps each page to its FamilySearch image ID.
- **Pages:** 97 page sides, ED 76 sheets 1A–23A (44 sides) and ED 77 sheets 1A–27A (53 sides).
  - FamilySearch downloads are named by image ID, not page. Each page was identified from the ED and sheet in
    its top-right header. The handwritten number in the top corner (ED 77) or after "Enumerator" (ED 76) is a
    running count of people, about 50 more per side, which confirms the order.
  - **76-07B doesn't exist.** 7A ends at line 41 with a note that the section ends, and 8A continues the
    dwelling and family numbers. FamilySearch has one blank B side with no header, probably this one. It's
    listed in `img_sources.csv` but not saved as a page.
  - **76-12A and 76-12B were filled in back to front.** The enumerator corrected the A/B labels by hand, so
    12A shows printed lines 51–100 and 12B lines 1–50. The files follow the corrected labels, which the family
    numbers confirm (12A ends at family 215, 12B runs 216–224, 13A starts at 225). The `line` column keeps the
    printed numbers.
  - 77-07A and 77-07B also have hand-corrected labels. The files follow the printed line numbers: 7A has lines
    1–50.
