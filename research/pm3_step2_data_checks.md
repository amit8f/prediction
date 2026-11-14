# PM3 Step 2 report: data checks and funnel counts

Date: 14 Nov 2026. Plan: `research/prereg/PM3.md`, approved by Amit (PR #8 merged). No Kalshi price, trade price or result direction in the chosen category was read. The only result field used is a type flag (plain yes/no, settlement value only, or neither). Scripts: `scripts/pm3_pull_listings.py`, `scripts/pm3_funnel.py`. Raw output: `research/pm3_step2_funnel_output.txt`.

One slip, for the record: while checking field names on one live record, I printed one settlement value of one S&P 500 hourly market (Financials, `KXINXU`). Financials was not picked, and nothing from Climate and Weather was seen.

## 1. Category pick (section 5): Climate and Weather

Listing pull: every settled market in every series outside Sports, Crypto and Exotics (11,596 series from the 11 Nov series list), live and historical endpoints, 3,843,748 markets, 22 minutes.

| Step | Markets |
|---|---|
| Pulled | 3,843,748 |
| Dropped: scheduled close (`expected_expiration_time`) outside 1 Jan 2025 to 13 Nov 2026 | 26,130 |
| Dropped: no time to rest an order (snapshot not before close minus 1 hour) | 2,379,583 |
| Dropped: trading already over at the snapshot (fix A below) | 178,046 |
| Dropped: city-pair weather combos, `KXCITIESWEATHER` (fix B below) | 9,324 |
| Dropped: combo (multivariate) markets | 13,697 |
| Dropped: not binary, or result neither yes/no nor a settlement value | 0 |
| Kept | 1,236,968 |

| Category | Events | Markets | Days |
|---|---|---|---|
| **Climate and Weather** | **15,572** | 96,138 | 682 |
| Financials | 11,090 | 931,558 | 550 |
| Economics | 3,810 | 64,022 | 485 |
| Entertainment | 3,795 | 42,923 | 656 |
| Mentions | 2,012 | 34,168 | 393 |
| Others | under 1,600 each | | |

Weather wins in every version I ran: without fixes A and B (18,027 vs 17,888 for Commodities), with them (15,572 vs 11,090), and with `close_time` as the close (15,710 vs 11,841). So the two fixes don't decide the pick.

As section 5 warned: PM3 now spends weather's data. The weather idea from the sweep would later need dates after 13 Nov 2026.

## 2. Two listing-only fixes (please confirm)

Both change who is in the universe, use listing fields only, and were made before any price or result was read.

A. Trading must still be open at the snapshot. Kalshi's 15-minute commodity and index markets trade for 15 minutes, but their `expected_expiration_time` is up to 6 hours later, so the plan's window test let them in even though no order could rest. 178,046 such markets dropped.

B. `KXCITIESWEATHER` dropped as a combo. Each event is a pair of cities' highs on one day (e.g. "(AUS)(CHI)"), so it repeats the single-city events. 2,382 events, Dec 2024 to Mar 2025 only.

## 3. Holdout split (fixed now)

Newest 25% of the 682 snapshot days in Climate and Weather.

| | From | Days | Events | Markets |
|---|---|---|---|---|
| Training | 31 Dec 2024 | 512 | 7,702 | 43,516 |
| Holdout | **27 May 2026** to 12 Nov 2026 | 170 | 7,870 | 52,622 |

No event has markets on both sides of the cut. Both sides clear 300 events and 60 days before fills; how many fill is unknown until Step 3. Growth is steep (about 250 events a month in 2025, about 1,500 a month since September 2026), so the holdout holds half the events.

## 4. Correlated markets

About 6 markets per event (a ladder of temperature ranges), collapsed to one event number as planned. Events are 57% daily highs, 36% daily lows, 5% rain, the rest snow, hurricanes and other. The daily high and low for one city on one day are separate events but share the weather, and cities often share a front. Day clustering covers this: the plainest effective sample size is 682 days (170 in the holdout), not 15,572 events.

## 5. One thing for Amit to note (no change proposed)

For weather, `expected_expiration_time` is 8 to 22 hours after `close_time` (trading ends in the evening, expiry is the next morning once the data is out). With the plan's scheduled close, the snapshot falls about 10 to 14 hours before trading ends, not 24, and the order effectively rests until trading stops. The plan says `expected_expiration_time`, so I've kept it. If you'd rather use `close_time - 24h`, it has to be decided now, before any price is read.

## 6. The [VERIFY] items

| Item | Finding |
|---|---|
| Trade `created_time` is UTC | Yes: ISO times ending in Z, live trades matched the current UTC clock. |
| Trade fields | `taker_side`, `yes_price_dollars`, `count_fp`, `is_block_trade` present on live and historical trades. Two newer fields also exist, `taker_book_side` and `taker_outcome_side`. Step 3 confirms what `taker_side` = yes means on a few known trades before any fill is computed (a bug-fix check). |
| Historical trades end | About 14 Sep 2026; later trades are on `/markets/trades`. |
| Maker fee formula | Can't confirm here (kalshi.com is blocked). The plan charges 0.0175 x p x (1 - p) on every fill anyway, the cautious side. |

## 7. Pull time for Step 3 (section 13)

About 96,000 markets: one hourly-candle call each for the ~44,000 settled before 12 Sep 2026 (about 10 minutes at 70 calls a second), batched calls for the rest, then the trade tape for eligible markets only. Roughly 1 to 3 hours in total, far under 24 hours, so no sampling.

## 8. Data saved

Project Library `data/pm3/pm3_listings_slim.jsonl.gz`: listing fields for all 3.8M pulled markets, no prices, no result direction.
