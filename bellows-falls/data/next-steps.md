# Next steps: transcribe the remaining 85 pages with Claude batch mode

**Plan:** send the pages to **Claude Opus 5.5** through the **Message Batches API** on a **personal Claude
Console account** (platform.claude.com), never the Mapbox one. Batches cost 50% of the list price
($2 in / $10 out per million tokens), so this comes to about **$0.17 a page, about $15 for 85 pages**. Most
batches finish within an hour; the maximum is 24 hours.

(Claude Platform on AWS was the first plan. Its sign-up failed on the personal AWS account with "AWS account
registration is incomplete or revoked", which is an AWS Marketplace problem.)

## Where things stand (2026-11-22)
- Setup is done (step 1). A one-request smoke batch on the personal key succeeded.
- **Steps 3 and 4 are done.** All 87 pages are in `transcribed/`. The full run cost about $15.38 at batch
  price, going by the token counts in `transcribed/_usage.jsonl`. `output/` and `../site/data/census_1900.geojson`
  have been rebuilt and geocoded: 4,337 people at 646 addresses, 95 of them without a location.
- **Still to review:** 66 `CHECK` lines from `build_csv.py` (ages that don't fit birth dates), 1,305 rows
  marked uncertain, whether `Lovell` (merged from `Lowell`)
  is the right spelling, and whether `Oak Hill` (17B) and `Oak Hill Terrace` (14A) are the same street.
  Neither name exists today, so check the 1896 Sanborn map.

## Notes for agents
- **Ask before anything that spends money.** That means any `submit`. `collect`, `retrieve` and listing
  models are free.
- **Never use a full-price path,** even for one page or a retry (see "No full-price runs" below). Retry
  failed pages with `submit`, which puts them in a new batch.
- **Use only the Keychain key.** Never read `ANTHROPIC_API_KEY`, a saved `ant` profile or the default
  (Mapbox) AWS profile, and never print the key.
- **The key starts with `sk-ant-usr`** and works anyway. Its organization ID is
  `923d38d1-ce0a-4ecb-9daa-501af0454021`, and the user has confirmed in the Console that it's their
  personal organization. To check the key, call `models.with_raw_response.list()` and read the
  `anthropic-organization-id` response header.
- **Spending shows up late.** The Console's spending page updates only after a batch ends, and sometimes
  later than that.

## 1. Setup (done)
- Personal Claude Console account, with prepaid credit and a monthly spend limit.
- Its API key is stored only in the macOS Keychain (service `bf-census-anthropic`, account `personal`).
  Don't put it in `ANTHROPIC_API_KEY`, a shell profile or the repo, so it can't mix with the work setup.
  To replace it: `security add-generic-password -U -s bf-census-anthropic -a personal -w`

## 2. The batch script
`scripts/transcribe_batch.py` reads the key from the Keychain and has two commands:
- `submit` sends one request per page (`custom_id` = page stem), splitting into several batches when the
  total is over 200 MB (each page is about 8 MB). Batch IDs are saved in `OUT/_batches.json`.
- `collect` writes each finished page's CSV and a `_usage.jsonl` line with the token counts and batch-price
  cost. Refused or failed pages are listed. Run `submit` again to retry them in a new batch.

## 3. Test on the two pages already done, and check the price
```
python3 -I scripts/transcribe_batch.py bellows-falls submit  --out bellows-falls/data/test_batch 259-42B 259-43A
python3 -I scripts/transcribe_batch.py bellows-falls collect --out bellows-falls/data/test_batch
python3 -I scripts/compare_csv.py bellows-falls/data/transcribed/259-42B.csv bellows-falls/data/test_batch/259-42B.csv
python3 -I scripts/compare_csv.py bellows-falls/data/transcribed/259-43A.csv bellows-falls/data/test_batch/259-43A.csv
```
Each page is given the other one as its example, so the test never sees its own answer. Look at:
- **The price.** Compare the Claude Console's Usage/Cost page with the token counts in
  `test_batch/_usage.jsonl`. Half price is about $0.17 a page; full price is about $0.33. **If it's full
  price, stop here and rethink.**
- **The match rate.** Which columns differ, and whether the differences are real misreads or rows already
  marked uncertain.

If accuracy is poor, adjust the tiles or prompt and re-test before spending more.

## 4. Run the rest
```
python3 -I scripts/transcribe_batch.py bellows-falls submit --all
python3 -I scripts/transcribe_batch.py bellows-falls collect
python3 -I scripts/build_csv.py bellows-falls
python3 -I scripts/geocode.py bellows-falls
python3 -I scripts/build_site_data.py bellows-falls
```
- `--all` skips pages that already have a CSV, so 42B and 43A are left alone. Resubmitting retries only the
  missing pages.
- Review the `CHECK` lines (ages that don't fit birth dates) and the `UNMAPPED` lines (add the birthplaces to
  `COUNTRIES`).
- Spot-check rows marked uncertain against the images. `scripts/crop.py` zooms into a region.

## No full-price runs
Every page must be billed at a discounted batch price. Don't use full-price options such as
Bedrock on-demand calls or an interactive Claude Code session, even for a single
page or a retry. If a batch doesn't come out at about half price, stop and rethink rather than switching to
an on-demand path.

## 5. After that
Join the houses in `site/data/census_1900.geojson` to the Sanborn building footprints, in place of today's
geocoded points. That needs the footprints with
street and house-number attributes, plus manual matching where numbering changed between 1896 and 1900.
