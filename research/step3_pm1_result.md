# Step 3 report: PM1 result (Kalshi Sports, favourites 24h before close)

Date: 12 Nov 2026. Idea number 1. Plan: `research/prereg/PM1.md` with Amendment 1 (section 17). Raw output: `research/step3/`.

## Verdict

**FAIL.** Buying the favourite at the ask 24 hours before the scheduled close loses about 5 cents per contract after fees. It isn't close.

## Order of work (as pre-registered)

1. Training quotes and results pulled. Training funnel written (`step3/step3_funnel_train.txt`).
2. Bucket picked on training only and committed before any holdout result was read (`step3/bucket_lock.json`, commit 34e24ce, 11:43 UTC). All three training buckets lost money; the least bad was 0.70 to 0.80 (-5.2 cents).
3. Holdout results pulled only after the lock (the script refuses otherwise). Holdout funnel written, then the one test run at 13:12 UTC.

## Holdout funnel (18 Jun to 9 Nov 2026)

| Step | Markets |
|---|---|
| Eligible sports markets | 622,181 |
| Dropped: empty book (bid 0 or ask 1.00) | 102,190 |
| Dropped: midpoint exactly 0.50 | 8,489 |
| Dropped: no quote at or before T | 13 |
| Dropped: mutually exclusive event with midpoints summing above 1.25 (1,194 events) | 4,261 |
| Tradeable | 507,228 |
| In the chosen bucket 0.70 to 0.80 | 84,848 |

Voided or non yes/no results in the bucket: 888, all counted at Kalshi's reported settlement value (none had to be dropped).

## Primary test (holdout, bucket 0.70 to 0.80)

| | Value |
|---|---|
| Markets / events / distinct games / days | 84,848 / 46,005 / 17,322 / 145 |
| Mean net profit per contract | -0.051 dollars |
| Day-clustered t | -24.2 |
| Bootstrap 95% interval (10,000 day resamples) | -0.055 to -0.047 |
| Random control mean | -0.066 |
| Rule minus control | +0.015 (interval +0.010 to +0.021) |

Pass rule: mean above 0 NO, t at least 3.0 NO, interval above 0 NO, beats control YES, sample size YES. Fails on three of five.

## Why it fails

On training data the favourites win almost exactly as often as their midpoint says (for example 71% wins at a 72 cent midpoint). The tiny favourite-longshot tilt, about 1 cent, is far smaller than half the spread, which averages 6 to 8 cents in this bucket and 20+ cents in the 0.90 to 0.97 bucket. Buying at the ask pays the spread, and the spread is the whole loss. Beating the random control just means favourites lose less than random picks; it doesn't make money.

## Exploratory (never a pass)

Other buckets on the holdout: 0.80 to 0.90 at -5.6 cents, 0.90 to 0.97 at -8.9 cents. Voids counted as total losses: -5.9 cents. Every holdout month is negative (-4.1 to -7.7 cents).

## Dollar check

At 10 contracts per trade and about 585 trades a day, the rule would lose about 300 dollars a day. Far below the $100 a month floor.

## Implementation notes (choices made before outcomes, not in the plan text)

- Quote = last hourly candle ending at or before T, looking back up to about 200 days (median age 0.2 hours, 99th percentile 16 hours).
- Fee multiplier at T from Kalshi's fee-change history; before a series' first recorded change, 1 was assumed.
- "Ladders far above 1.00" was set at midpoints summing above 1.25, only for events Kalshi flags as mutually exclusive.
- Clustering day = the event's earliest snapshot day. The control pool = tradeable markets with a snapshot on the same day, random side, at the ask.

## Limits

Depth isn't known, so even the fills assumed here may be optimistic. Kalshi has no public dispute flag. `expected_expiration_time` might be edited after a reschedule, with no history kept.

## What this suggests

Paying the spread kills a taker strategy here. The step 2 report already named a maker-side version (posting a bid on the favourite) as the natural PM2. Free data can't show whether such orders would fill, so it would need a forward logger. It goes in the queue only with Amit's OK, and its pass bar is t >= 3.2.
