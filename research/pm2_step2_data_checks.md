# PM2 Step 2 report: data checks and funnel counts

Date: 13 Nov 2026. Plan: `research/prereg/PM2.md` with Amendment 1 (zero delay), both approved by Amit. No Kalshi price, no Kalshi result direction and no spot price was read. The only result field used is a yes/no flag (was the result a plain yes or no). Spot files were read for timestamps only. Scripts: `scripts/pm2_pull_listings.py`, `scripts/pm2_pull_spot.py`, `scripts/pm2_funnel.py`. Raw output: `research/pm2_step2_funnel_output.txt`.

Order of events, for the record: the listing and spot pulls started at about 07:56 UTC, just before PR #5 was merged (07:57). The amendment doesn't touch the universe, the data or the funnel, and nothing was read until after the merge.

## 1. The [VERIFY] items

| Item | Finding | Effect |
|---|---|---|
| `close_time` equals the rules-text time on settled markets | Yes on all 5,037,940 markets in the period. 879 looked off by an hour, all on the night clocks went back (1 AM happens twice; the rules say "1 AM EST", the second one). That was my parser, not Kalshi. | None. Settlement time = `close_time`. `expected_expiration_time` is 5 minutes later, as seen on open markets. |
| Fee schedule | All eight series: quadratic, multiplier 1. No crypto series appears in the fee-change history. | None |
| Coinbase candle time = START of the minute | Yes. 59 of 60 candles matched the first and last real trade in [t, t+60). 0 of 60 matched the other way round. | "Spot at m" = close of the candle that starts at m minus 1 minute. |
| Kalshi 1-minute `end_period_ts` = END of the minute | Yes. Volume matched real trades in (t-60, t] for 168 of 168 candles on three live markets. 0 matched the other way. | None |
| Minute boundaries line up (Amendment 1) | Both sources stamp whole minutes (every timestamp is a multiple of 60 seconds). The spot candle used at m holds trades before m; the Kalshi candle ending at m holds quotes up to m. | No shift needed. Caveat: I can only check to the whole second, not below. |

## 2. Funnel (listing fields only)

| Step | Markets |
|---|---|
| Pulled (eight series, live and historical endpoints) | 5,086,298 |
| Dropped: scheduled close outside 1 Jan 2025 to 12 Nov 2026 | 48,358 |
| Dropped: result not a plain yes/no | 0 |
| Dropped: hourly market with no strike | 6,544 |
| Dropped: no signal minute with a full 60 minutes of Coinbase spot | 7,251 |
| Kept | 5,024,145 |
| of which kept with a few spot gaps (those minutes get skipped) | 35,271 |

Coinbase coverage: 980,318 to 980,403 of 981,237 minutes per coin (99.9%). Binance backup not needed.

| Series | Kept markets | Events | Days | First day |
|---|---|---|---|---|
| KXBTCD (hourly) | 1,569,731 | 13,020 | 682 | 31 Dec 2024 |
| KXETHD | 1,546,819 | 13,016 | 682 | 31 Dec 2024 |
| KXSOLD | 1,161,310 | 7,608 | 339 | 9 Dec 2025 |
| KXXRPD | 628,978 | 8,564 | 403 | 6 Oct 2025 |
| KXBTC15M (15-minute) | 31,371 | 31,371 | 338 | 10 Dec 2025 |
| KXETH15M | 31,348 | 31,348 | 338 | 10 Dec 2025 |
| KXSOL15M | 28,957 | 28,957 | 308 | 9 Jan 2026 |
| KXXRP15M | 25,631 | 25,631 | 275 | 11 Feb 2026 |
| Total | 5,024,145 | 159,515 | 682 | |

Hourly events have about 120 strikes each, which is why markets far outnumber events. Distinct close hours across all coins: 13,311 (the second effective sample size from section 12). Growth is steep: about 1,000 events a month in 2025, 14,000 a month since March 2026.

## 3. Holdout split (fixed now)

Newest 25% of the 682 snapshot days, pooled over all eight series.

| | From | Days | Events |
|---|---|---|---|
| Training | 31 Dec 2024 | 512 | 79,545 |
| Holdout | **27 May 2026** to 12 Nov 2026 | 170 | 79,970 |

Both sides clear the 300-event and 60-day minimums. Because of the growth, the holdout holds half the events, and all four 15-minute series are mostly in it (they started Dec 2025 to Feb 2026), so training for the 15-minute markets is thin.

## 4. One thing for Amit to note (no change proposed)

The hourly series also hold some daily and weekly events (markets that open 25 hours or 7 days before close): 2,100 of 42,208 hourly events, 681 in the holdout. PM2 says "every market in the eight series" and uses only the last 55 minutes, so I kept them, as written. Section 3's exclusion of "daily, weekly and longer series" reads as being about other series. If you'd rather drop them, it has to be decided now, before any price is read.

## 5. Small definition, for the record

Section 5 sets the 15-minute strike as "the mean of Coinbase spot over the minute before open". A 1-minute candle has no true mean, so the test will use (open + high + low + close) / 4 of that one candle. Kalshi's own `floor_strike` for these markets is the official reference value, but I can't prove when it was published, so it stays exploratory.

## 6. Data saved

Project Library `data/pm2/`: the four Coinbase 1-minute files (start_ts, low, high, open, close, volume) and a slim listing file with no prices or results. The full raw listing (2 GB) is not kept.
