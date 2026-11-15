# PM4 Step 3 result: FAILED

Date: 15 Nov 2026. Plan: `research/prereg/PM4.md` (PR #11). Data checks: `research/pm4_step2_data_checks.md` (PR #12). Idea number 4, pass bar t >= 3.4. Scripts: `scripts/pm4_prep.py`, `pm4_pull.py`, `pm4_pull_results.py`, `pm4_analyze.py`. Raw output: `research/pm4_step3/`. Pulled data in the project Library under `data/pm4/`.

**Verdict: fail.** Selling cheap YES on Kalshi Financials with a resting order lost 3.0 cents per contract after fees on the holdout (t = -4.0). It fails pass rules 1 to 3 and the dollar check. PM4 is closed.

## 1. Order of work

1. Pulled 1-minute quotes and trades for all 1,988,220 training markets (about 11 hours at Kalshi's ~50 calls a second), plus their results.
2. Chose the price cap C on training and pushed the lock (commit `7380ed5`, `research/pm4_step3/cap_lock.json`) before any holdout quote, trade or result was pulled.
3. Pulled the 559,717 holdout markets and their results, then ran the test once with C = 0.10.

## 2. Training and the lock

| C | Orders | Filled events | Mean net per contract | t |
|---|---|---|---|---|
| 0.10 | 416,373 | 1,726 | -1.32c | -2.2 |
| 0.15 | 421,756 | 2,166 | -1.66c | -2.7 |
| 0.20 | 426,604 | 2,527 | -2.24c | -3.5 |

Every cap lost money on training already. The plan's rule picks the highest mean, so C = 0.10. The holdout ran as written anyway.

## 3. Funnel (holdout, before returns)

| Step | Markets |
|---|---|
| Pulled | 559,717 |
| No 1-minute candle in the 30 min up to the snapshot | 186,878 |
| Quote can't carry an order (ask outside 3-97c or spread under 2c) | 197,861 |
| API failure after retries | 28 |
| Kept, order possible (rule and control pool) | 174,950 |
| Rule orders at C = 0.10 | 27,022 in 3,985 events |
| Filled at least partly | 2,662 orders (9.9%) in 1,503 events, 128 days |

## 4. Primary test (holdout 29 May to 13 Nov 2026)

| Check | Result | Needed | |
|---|---|---|---|
| Mean net per contract | **-3.02c** | above 0 | fail |
| Day-clustered t | **-4.01** | at least 3.4 | fail |
| Bootstrap 95% (whole days) | -4.60c to -1.64c | above 0 | fail |
| Rule minus random control | +5.05c (95%: +3.56 to +6.48) | above 0 | pass |
| Filled events / days | 1,503 / 128 | 300 / 60 | ok |
| Dollar check | **-$144 a month** | +$100 | fail |

We sold YES at 5.4 cents on average, but YES won on 11.5% of filled orders. That's the pick-off risk the plan named: our resting offer gets taken mostly when the index is moving toward the strike, so the fills are the ones we least want. The control lost even more (-8.1c) because a random side one cent inside the spread is a worse bet still; beating it doesn't rescue a losing rule. Kalshi's real per-series maker fees (lower than the flat fee we charged) would make it -2.6c, still a loss.

Dollar check: 159 filled contracts a day, 18 filled orders a day, about $920 tied up at peak, so about -$144 a month. Combined with PM3 (about +$84) it's about -$60 a month. That figure is for context only.

## 5. Exploratory (never counts)

| Cut | Filled events | Mean | t |
|---|---|---|---|
| 15-minute currency and rate markets (new since Sep, none in training) | 781 | -2.19c | -2.9 |
| Everything else | 722 | -3.92c | -2.8 |

Both halves lose, so the new 15-minute markets aren't what sank it. By month, only late May was positive (+1.2c, a few days). Every month from June to November lost 1 to 4.4 cents.

## 6. What this means

The maker edge PM3 found in weather does not carry over to Financials. In weather the price of a cheap strike barely moves before settlement; here it follows a live index, and takers who buy our cheap YES are mostly the ones who've just seen the index move. Kalshi's tape alone can't tell a fast trader from a slow one, so a fixed resting order is on the wrong side.

Fills were judged from the public trade tape at small size (10 contracts), with the same optimism and pessimism the plan lists. That doesn't change a loss this size.

Holdout days up to 13 Nov 2026 are now used for Financials. The next idea needs its own plan and Amit's OK, at bar t >= 3.5 (idea 5).
