# Bellows Falls census viewer

A map of Bellows Falls, Vermont, around 1900. The base layer is georeferenced 1896 Sanborn fire-insurance
maps. Each building shows an emoji flag for the most common nationality of the people living there. Clicking a
building lists everyone recorded there in the 1900 US census: name, age, sex and birthplace.

## Layout

```
data/   1900 census transcriptions, scripts, and built per-person / per-address outputs
site/   the map: static HTML/CSS/JS (MapLibre) plus data/census_1900.geojson built from data/
```

## Running the site

It's a static site with no build step. Serve `site/` with any web server and open it:

```
cd site && python3 -m http.server 8000
```

The basemap is a Protomaps extract of just the village, `site/data/bellows_falls.pmtiles` (about 1 MB),
served with the site. The overlay is the 1896 Sanborn raster tileset from the `mapping-vt-tiles` S3 bucket
used by mappingvermont.org. The statewide `vermont.pmtiles` there stops at zoom 14, which has almost no
building footprints; this extract goes to zoom 15. The page loads the whole file at once, so it works on servers
without HTTP range requests. The map can't pan outside the extract (`MAX_BOUNDS` in `site/script.js`).
Regenerate the extract from a recent daily build (dates are listed at
https://build-metadata.protomaps.dev/builds.json):

```
pmtiles extract https://build.protomaps.com/<DATE>.pmtiles site/data/bellows_falls.pmtiles \
  --bbox=-72.50,43.10,-72.40,43.17 --maxzoom=15
``` Each house's flag is the plurality birth
country among residents over 16. Ties show every tied flag.

To refresh the map data after new pages are transcribed, see "Geocoding and the map data" in
[`data/README.md`](data/README.md).

See [`data/README.md`](data/README.md) for the source, the transcription format and how to build the
outputs.

The census page images come from FamilySearch and aren't included in this repo. `data/README.md` explains how
to download them.
