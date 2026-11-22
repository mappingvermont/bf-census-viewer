# Next steps: transcribe the remaining 85 pages with Claude batch mode

**Plan:** send the pages to **Claude Opus 5.5** through the **Message Batches API** on a **personal Claude
Console account** (platform.claude.com), never the Mapbox one. Batches cost 50% of the list price
($2 in / $10 out per million tokens), so this comes to about **$0.17 a page, about $15 for 85 pages**. Most
batches finish within an hour; the maximum is 24 hours.

(Claude Platform on AWS was the first plan. Its sign-up failed on the personal AWS account with "AWS account
registration is incomplete or revoked", which is an AWS Marketplace problem.)

## Where things stand (2026-11-22)
- Setup is done (step 1). A one-request smoke batch on the personal key succeeded.
- **Step 3 is in progress.** The two-page test batch `msgbatch_0164wAHj6G8mjjyW2wvpR94G` was submitted at
  22:59 UTC and is recorded in `test_batch/_batches.json`. To pick it up, run from `data/`:
  `python3 -I scripts/transcribe_batch.py collect --out test_batch`. That's free and safe to repeat; it
  writes nothing until the batch has ended. Then run the two `compare_csv.py` commands in step 3 and
  report the match rate and the `_usage.jsonl` costs to the user.
- Step 4 (the full run, about $15) hasn't started. **Don't submit it until the user has reviewed the test
  results and said go.**

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
python3 -I scripts/transcribe_batch.py submit  --out test_batch 259-42B 259-43A
python3 -I scripts/transcribe_batch.py collect --out test_batch
python3 -I scripts/compare_csv.py transcribed/259-42B.csv test_batch/259-42B.csv
python3 -I scripts/compare_csv.py transcribed/259-43A.csv test_batch/259-43A.csv
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
python3 -I scripts/transcribe_batch.py submit  --out transcribed --all
python3 -I scripts/transcribe_batch.py collect --out transcribed
python3 -I scripts/build_csv.py transcribed output
python3 -I scripts/geocode.py output/people_1900.csv output/geocoded_1900.json
python3 -I scripts/build_site_data.py output ../site/data/census_1900.geojson
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
