# Winooski 1900 census

Per-person records from the 1900 US census for Winooski village, Vermont.

In 1900 Winooski was a village in the town of Colchester, not a town of its own. It became a city in 1922. On
FamilySearch it's filed under Colchester.

## Source

- **Collection:** FamilySearch, "United States, Census, 1900"
  (https://www.familysearch.org/en/search/collection/1325221). It's free with an account, and has no bulk
  download.
- **Coverage:** Vermont → Chittenden Co. → Colchester town → two enumeration districts:
  - **ED 75**: Winooski village (part), West Ward. NARA microfilm T623, reel 1690.
  - **ED 76**: Winooski village (part), East and South Wards. NARA microfilm T623, reel 1691.

  These aren't included: ED 74 (the rest of Colchester town, outside the village) and ED 296 (Fort Ethan Allen).
- **Images:** they aren't in this repo. Download them from FamilySearch's image viewer, one image per page side,
  into `img/`. Name each file by its ED and sheet, with sheets 1–9 zero-padded: `75-01A.jpg`, `75-01B.jpg` …
  `76-01A.jpg` …. Each sheet has an A side (lines 1–50) and a B side (lines 51–100).
- **Pages:** 76 page images, sheets 1A to 19B in each ED. `img_sources.csv` maps each page to its
  FamilySearch image ID.

Check the place name written at the top of each ED's first page. The ED numbers come from the USGenWeb
transcription index
([reel 1690](https://www.us-census.org/states/vermont/teams/Chittenden1900-T623-1690.htm),
[reel 1691](https://us-census.org/states/vermont/teams/Chittenden1900-T623-1691.htm)).

The same reels are also on archive.org
([1690](https://archive.org/details/12thcensusofpopu1690unit),
[1691](https://archive.org/details/12thcensusofpopu1691unit)), but the FamilySearch images are the source for
this project.
