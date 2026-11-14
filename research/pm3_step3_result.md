# PM3 Step 3 result: maker orders selling cheap weather YES on Kalshi

Date: 14 Nov 2026. Plan: `research/prereg/PM3.md` (PR #8). Data checks: `research/pm3_step2_data_checks.md` (PR #9). Idea number 3, bar t >= 3.3.

## Verdict: STOP. Clears the statistics, misses the $100 floor

On the holdout the rule makes **+1.14 cents per contract after fees, t = 3.56**, and beats the random control. But at the plan's 10 contracts per order it fills about 245 contracts a day, which works out to about **$84 a month**, under the $100 floor. Plan section 11, item 6, and CLAUDE.md say: below the floor, stop even on a pass. So PM3 does not pass and doesn't move to a forward logger without Amit's say-so.

| Pass item (section 11) | Holdout | OK? |
|---|---|---|
| 1. Mean net per contract > 0 | +1.144c | yes |
| 2. Day-clustered t >= 3.3 | 3.56 | yes |
| 3. Bootstrap 95% (10,000 day resamples) above 0 | +0.50c to +1.77c | yes |
| 4. Beats random control, difference interval above 0 | control -1.12c; difference +2.26c [+1.59, +2.91] | yes |
| 5. >= 300 filled events, >= 60 days | 3,448 events, 170 days | yes |
| 6. Dollar check reaches $100/month | about $84 | **no** |

## What was done, in order

1. Universe: the 96,138 Climate and Weather markets from Step 2 (`scripts/pm3_universe.py`).
2. Training only: hourly quote at the snapshot and trade tape from snapshot to cancel (`scripts/pm3_pull.py`), results for training markets only (`scripts/pm3_pull_results.py`).
3. Checked `taker_side`: in the 30 minutes after the snapshot, taker_side = yes trades sit mostly at or above the ask (25,379 of 40,062) and taker_side = no mostly at or below the bid (21,271 of 36,083). So yes means the taker bought YES, as the plan assumed.
4. Price cap fitted on training and **locked at 15c** in commit 9641463 (`research/pm3_step3/cap_lock.json`), pushed before any holdout data was pulled. Training: 10c +1.7366c, 15c +1.7372c, 20c +1.6617c per contract (t 5.3 to 6.3). 10c and 15c are a tie in practice; the plan's rule picks the higher number.
5. Holdout pulled and the test run once with C = 15c (`scripts/pm3_analyze.py`, output `research/pm3_step3/hold_output.txt`).

## Funnel (holdout, before any return)

| Step | Markets |
|---|---|
| Listed | 52,622 |
| Dropped: same market listed twice (live and historical lists) | 2,723 |
| Dropped: no quote in the 6 h before the snapshot | 941 |
| Dropped: quote can't carry an order (ask outside 3-97c or spread under 2c) | 34,242 |
| Quoted, order possible (control pool) | 14,716 |
| Rule orders (ask 3-15c, spread >= 2c) | 6,394 |
| Orders with any fill | 4,452 (70%) |
| Events with a fill | 3,448 of 4,376 |

The duplicate listings only occur in the holdout and don't change the event count from Step 2. One market had an API failure in training and was dropped.

## The numbers

- Filled contracts: 41,723. Mean sell price 6.1c; YES won on 5.1% of filled orders. That 1c gap is the edge.
- Effective sample: 170 distinct days (plainest count), 3,448 events.
- Real per-series maker fee instead of charging it on every fill (reported alongside, can't change the verdict): +1.34c.
- Cash tied up: about 94 cents per filled contract until settlement, about $230 a day at 245 contracts, freed next day. Capital isn't the limit; fills are.

## Exploratory, never counts

By month the edge is uneven and fades at the end: May -2.8c, Jun +0.8, Jul +1.0, Aug +1.7, Sep +2.7, Oct +0.2, Nov (to 12th) +0.0c per contract. The last six weeks are near zero, which is what you'd expect if other makers moved in. It argues against reading the $84 as "close enough".

## Caveats on the fill model

The fills are judged from the public trade tape at 10 contracts. The test can't see whether our order would actually have been first in line, or whether it would have changed what takers did. These two things can push either way, and only a live paper logger can measure them.

## What's left

PM3 stops here under the plan. If Amit wants, the options are (a) close PM3 and move to PM4 at bar t >= 3.4, or (b) treat it as a near-miss: same rule, untouched, on weather data after 13 Nov 2026, with his OK, counted as one more idea. A bigger order size would raise the dollar figure but is a rule change, so it can't be tested on this data.
