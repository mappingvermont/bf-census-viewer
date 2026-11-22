# Next steps: transcribe the remaining 85 pages with Claude batch mode on AWS

**Plan:** send the pages to **Claude Opus 5.5** through the **Message Batches API** on **Claude Platform on
AWS**. Billing goes to a **personal AWS account** through a separate AWS profile. No Anthropic account or API
key is involved.

Claude Platform on AWS isn't Amazon Bedrock. Anthropic runs it, and AWS provides sign-in (SigV4/IAM) and
billing (AWS Marketplace). Bedrock doesn't offer the Batches API, so it can't be used for this.

**Expected cost:** about **$0.17 a page, about $15 for 85 pages**. AWS bills Claude Platform usage at the same
per-token prices as the Claude API ($4 in / $20 out per million tokens for Opus 5.5). Batches are charged at 50%
of those prices ($2 / $10). Anthropic's docs don't say outright that the batch discount applies on AWS, so
step 2 checks it on a test page before the full run. **If the test doesn't show roughly half price, stop and
rethink.** Most batches finish within an hour; the maximum is 24 hours.

## 1. Set up the personal AWS account (once)
1. In the personal AWS account, subscribe to **Claude Platform on AWS** (AWS Marketplace) and create a Claude
   workspace. Note its workspace ID. Setup guide:
   https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws
2. Create an IAM user with the Claude Platform permissions for messages and batches (see the guide's IAM
   actions page) and an access key.
3. On this machine, run `aws configure --profile personal`. Then check that it shows the right account:
   `aws sts get-caller-identity --profile personal`

## 2. Write the batch script
`scripts/transcribe_batch.py` doesn't exist yet. Base it on `scripts/transcribe_bedrock.py` and reuse its
tiles, prompt and CSV parsing. The differences:
- **Client:** `anthropic.AnthropicAWS` (install `anthropic[aws]`). Pass a required `--profile`, so it never
  falls back to the machine's default (work) credentials. Region and workspace ID go in as arguments or
  `AWS_REGION` / `ANTHROPIC_AWS_WORKSPACE_ID`. The model ID is `claude-opus-5-5`, with no `anthropic.` prefix.
- **Two commands:**
  - `submit` builds one request per page, with `custom_id` = page stem, and saves the batch ID.
  - `collect` checks the batch and writes each finished page's CSV and `_usage.jsonl` line. Results come back
    in any order, so match them by `custom_id`.
- **Requests in a batch can't stream or use the `fallbacks` option.** Handle refusals and failures by listing
  the affected pages and resubmitting them, either in a new batch or through `transcribe_bedrock.py`.
- **Size:** a batch can hold at most 256 MB. Each page sends about 17 base64 images, so check the total and
  split into several batches if needed.
- **Cost estimate:** use batch prices ($2 in, $10 out, $0.20 cache read per million tokens).

## 3. Test on the two pages already done, and check the price
```
python3 -I scripts/transcribe_batch.py submit  --profile personal --out test_batch 259-42B 259-43A
python3 -I scripts/transcribe_batch.py collect --profile personal --out test_batch
python3 -I scripts/compare_csv.py transcribed/259-42B.csv test_batch/259-42B.csv
python3 -I scripts/compare_csv.py transcribed/259-43A.csv test_batch/259-43A.csv
```
Each page is given the other one as its example, so the test never sees its own answer. Look at:
- **The price.** After a day, compare the CCUs billed in AWS Cost Explorer (100 CCU = $1) with the token
  counts in `test_batch/_usage.jsonl`. Half price is about $0.17 a page; full price is about $0.33. **If it's
  full price, stop here and rethink.**
- **The match rate.** Which columns differ, and whether the differences are real misreads or rows already
  marked uncertain.

If accuracy is poor, adjust the tiles or prompt and re-test before spending more.

## 4. Run the rest
```
python3 -I scripts/transcribe_batch.py submit  --profile personal --out transcribed --all
python3 -I scripts/transcribe_batch.py collect --profile personal --out transcribed
python3 -I scripts/build_csv.py transcribed output
```
- `--all` skips pages that already have a CSV, so 42B and 43A are left alone. Resubmitting retries only the
  missing pages.
- Review the `CHECK` lines (ages that don't fit birth dates) and the `UNMAPPED` lines (add the birthplaces to
  `COUNTRIES`).
- Spot-check rows marked uncertain against the images. `scripts/crop.py` zooms into a region.

## Fallbacks
- **Bedrock, on demand:** `scripts/transcribe_bedrock.py` works as it is. It's faster (4 pages at a time,
  under an hour) but costs about twice as much (about $30). Bedrock sets its own prices, so its real cost may
  differ a little from that list-price estimate.
- **Interactive:** `PROMPT_transcribe_page.md` in a Claude Code session, about $1 a page.

## 5. After that
Join `output/addresses_1900.json` to the Sanborn building footprints. That needs the footprints with
street and house-number attributes, plus manual matching where numbering changed between 1896 and 1900.
