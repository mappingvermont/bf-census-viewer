# Next steps: transcribe the remaining 85 pages on Bedrock

**Plan:** run `scripts/transcribe_bedrock.py` with **Claude Opus 5.5** on Amazon Bedrock, billed to a
**personal AWS account** through a separate AWS profile. No Anthropic account or API key is involved. The
script requires `--profile`, so it never falls back to the machine's default AWS credentials.

**Expected cost:** about $0.33 a page, **about $30 for 85 pages** (estimated at list prices; the real figure
comes from the test run). Opus 5.5 isn't available for Bedrock batch inference, so these are normal on-demand
requests, 4 pages at a time, and should finish in under an hour.

## 1. Set up the personal AWS account (once)
1. In the AWS console, go to **Bedrock → Model access** in `us-east-1` and enable **Claude Opus 5.5** and
   **Claude Opus 5**. Opus 5 is used only if Opus 5.5 refuses a page.
2. Create an IAM user with Bedrock access and an access key.
3. On this machine, run `aws configure --profile personal`. Then check that it shows the right account:
   `aws sts get-caller-identity --profile personal`

## 2. Test on the two pages already done (under $1)
```
python3 -I scripts/transcribe_bedrock.py --profile personal --out test_bedrock 259-42B 259-43A
python3 -I scripts/compare_csv.py transcribed/259-42B.csv test_bedrock/259-42B.csv
python3 -I scripts/compare_csv.py transcribed/259-43A.csv test_bedrock/259-43A.csv
```
Each page is given the other one as its example, so the test never sees its own answer. Look at:
- **The match rate.** Which columns differ, and whether the differences are real misreads or rows already
  marked uncertain.
- **Cost per page.** It's in `test_bedrock/_usage.jsonl`. Multiply by 85.

If accuracy is poor, adjust the tiles or prompt and re-test before spending more. The fallback is the
interactive Claude Code route (`PROMPT_transcribe_page.md`), at about $1 a page.

## 3. Run the rest
```
python3 -I scripts/transcribe_bedrock.py --profile personal --out transcribed --all
python3 -I scripts/build_csv.py transcribed output
```
- `--all` skips pages that already have a CSV, so 42B and 43A are left alone. Re-running retries only the
  failed pages.
- Review the `CHECK` lines (ages that don't fit birth dates) and the `UNMAPPED` lines (add the birthplaces to
  `COUNTRIES`).
- Spot-check rows marked uncertain against the images. `scripts/crop.py` zooms into a region.

## 4. After that
Join `output/addresses_1900.json` to the Sanborn building footprints. That needs the footprints with
street and house-number attributes, plus manual matching where numbering changed between 1896 and 1900.
