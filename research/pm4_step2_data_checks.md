# PM4 Step 2 report: data checks and funnel counts

Date: 14 Nov 2026. Plan: `research/prereg/PM4.md`, approved by Amit (PR #11 merged). No Financials result and no bid, ask or trade price was read in this step. Scripts: `scripts/pm4_funnel.py`, `scripts/pm4_counts.py`. Raw output: `research/pm4_step2/`. Universe (listing fields only) saved to the project Library at `data/pm4/pm4_universe.jsonl.gz`.

Disclosures. (1) As the plan says, one settlement value of one S&P 500 hourly market (`KXINXU`) was seen in PM3 Step 2. Nothing more was seen here. (2) To check that 1-minute candles exist (a [VERIFY] item), I fetched candles for two markets and printed only the number of candles, field names and time spacing, no prices: one training `KXINXU` market and one holdout `KXEURUSD15M` market. 140 more candle calls were timed for the pull estimate; their contents weren't printed.

## 1. Funnel (section 4)

Source: the listing pull made this morning for PM3 Step 2 (every settled market in every non-Sports, non-Crypto series on the 11 Nov series list, live and historical endpoints). It has no prices and no result direction. I reused it rather than pull again; the universe is frozen at that pull.

| Step | Markets |
|---|---|
| Financials markets pulled | 2,574,826 |
| Dropped: same ticker listed twice (live and historical) | 22,766 |
| Dropped: scheduled close (`expected_expiration_time`) outside 1 Jan 2025 to 13 Nov 2026 | 3,703 |
| Dropped: combo (multivariate) markets | 0 |
| Dropped: not binary, or result neither yes/no nor a settlement value | 0 |
| Dropped: missing or reversed open/close times | 420 |
| Dropped: trading already over at the snapshot | 0 |
| Dropped: under 2 minutes between snapshot and trading end | 0 |
| Kept | **2,547,937** |

## 2. Trading life and the "trading already over" check

PM3 found weather trading stops hours before the official close. Here the plan sets the snapshot from `close_time` (trading end) directly, so no market can be closed at its snapshot, and none was.

I also checked whether `close_time` could be an early close, which would leak the future into the snapshot time. It doesn't look like it. 93% of markets have `close_time` equal to the scheduled close. Where they differ, the gap is a fixed number per series (3 hours for S&P and Nasdaq ranges, 5 hours for Treasury-rate hourlies, about a week for one Elon Musk net-worth series), which is how the series is set up, not markets stopping early. 143 markets have trading end after the scheduled close; left in.

| Trading life | Markets |
|---|---|
| 15 minutes (currency and rate 15-min series) | 20,281 |
| 15 to 60 minutes (mostly S&P and Nasdaq hourly ranges) | 1,591,493 |
| 1 to 2 hours | 11,700 |
| 2 to 24 hours | 822,171 |
| 1 to 2 days | 4,685 |
| Over 2 days (snapshot 24 h before trading end) | 97,607 |

## 3. Independent events (section 11)

38,457 events (an event = one index or rate at one expiry, all its strikes counted once), 525 series, 593 snapshot days. The median event has 1 market (the 15-min series); the S&P and Nasdaq hourlies have about 270 to 340 strikes per event. 24,466 distinct (series, close hour) slots. 243 events have strikes whose snapshots fall on two days; each event is dated by its earliest snapshot, so it sits on one side of the cut.

Same-day events move together (S&P, Nasdaq and Dow share every move; four currency pairs settle every 15 minutes). The plainest effective sample is 593 days, 148 in the holdout.

Biggest series by events: EUR/USD, GBP/USD and USD/JPY 15-min (3,476 each), S&P and Nasdaq hourly ranges (3,117 each), AUD/USD and USD/CAD 15-min (2,537 each), EUR/USD and USD/JPY hourly (about 2,300 each), four Treasury-rate 15-min series (981 each).

## 4. Holdout split (section 8, fixed now)

Newest 25% of the 593 snapshot days.

| | Days | Events | Markets |
|---|---|---|---|
| Training, to 28 May 2026 | 445 | 11,249 | 1,988,220 |
| Holdout, **29 May 2026** to 13 Nov 2026 | 148 | 27,208 | 559,717 |

Both sides clear 300 events and 60 days before fills. 23 events have strikes on both sides of the cut; they go to the side of their earliest snapshot, as above.

## 5. For Amit to note: the holdout holds a market type training never saw

The 15-minute currency and rate series only started in Sep 2026, and events jumped from about 1,000 a month to 13,643 in October. So:

| Family | Training events | Holdout events |
|---|---|---|
| Currency and rate 15-min | 0 | 19,587 |
| Rates hourly and daily | 0 | 1,610 |
| Index hourly (S&P, Nasdaq) | 4,584 | 3,020 |
| Currency hourly and daily | 5,331 | 845 |
| Index daily and other index | 727 | 748 |
| Other Financials | 584 | 1,421 |

(This table dates each event by its first-listed strike, so it is off by the 23 straddling events.) About 72% of holdout events are 15-minute markets. Since the primary test averages one number per event, the holdout result will mostly be about those, and the price cap C is chosen on training without them. The plan doesn't treat this as a problem and I haven't changed anything. If you'd rather, for example, weight by day instead of by event, it must be decided now, before any price is read. My suggestion is to keep the plan as written; the family split is already on the exploratory list.

## 6. The [VERIFY] items

| Item | Finding |
|---|---|
| 1-minute candles exist for settled markets | Yes on both endpoints, with `yes_bid` and `yes_ask` (open/high/low/close) on each candle, ending on whole minutes. Live candles came every minute. **Historical candles are sparse**: the training market had 2 candles 10 minutes apart in the 30-minute window. So the quote is the last candle ending at or before the snapshot within the 30 minutes, which is what the plan's skip rule implies. Item 2 below. |
| Candle and trade times are UTC; candle at the snapshot holds only earlier quotes | `end_period_ts` is a Unix time on the minute; PM1 showed it marks the end of the period. Step 3 uses only candles with `end_period_ts` at or before the snapshot. Trade times end in Z (PM3). |
| Batch candle endpoint | Returned an error; Step 3 uses one call per market. |

## 7. Pull time for Step 3 (section 12)

Candles: 2,299,986 markets settled before 12 Sep 2026 (historical, one call each) and 247,951 newer ones. One thread measured 7.2 calls a second; at the known rate of about 70 a second with parallel threads, that is about 10 hours for all 2.55 million. Trades only for eligible markets (most strikes sit far from the price and won't qualify): likely 1 to 2 hours more. **Total about 11 to 13 hours, under the plan's 24-hour line, so no sampling.** Step 3 runs the pull in the background; if it runs past 24 hours the plan's sampling rule (whole events, fixed seed, same rate both sides) applies.

## 8. What the merge accepts

1. Reusing this morning's PM3 listing pull as PM4's frozen universe (series list of 11 Nov; any Financials series created after that is missing).
2. Quote = latest 1-minute candle ending at or before the snapshot, within 30 minutes (needed because historical candles are sparse).
3. No sampling, since the pull fits in 24 hours.
4. Holdout from 29 May 2026, with the plan's event-level average kept despite section 5.
