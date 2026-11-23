# Winooski census viewer

A map of Winooski, Vermont, around 1900, with everyone recorded in each building in the 1900 US census. It's a
separate site from Bellows Falls, built the same way.

## Layout

```
town.json   settings used by the shared scripts in ../scripts
data/       1900 census page images, transcriptions and built outputs
site/       the map (static HTML/CSS/JS)
```

See [`data/README.md`](data/README.md) for the source and how to download the page images, and the
top-level README for the scripts.

Two settings in `town.json` differ from Bellows Falls:
- `examples` points at Bellows Falls pages until a Winooski page has been checked by hand.
- `layout.overlap` is 1.5 lines. In ED 75 the writing sits up to half a line lower than on the Bellows Falls
  scans, so the bands are padded more.

The `geocode` box roughly covers today's city of Winooski.
