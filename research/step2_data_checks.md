# Step 2 report: data checks and funnel counts (PM1)

Date: 11 Nov 2026. Venue: Kalshi. No result field and no price after the snapshot time was read or saved. Scripts are in `scripts/`. Raw console output is in `research/step2_funnel_output.txt`.

## 1. Access

All four data hosts answer from the `prediction` environment. `kalshi.com` (the website with the fee PDF) and academic paper sites are not reachable.

## 2. The [VERIFY] items in PM1

| Item | Finding | Effect on PM1 |
|---|---|---|
| Candles carry bid and ask | Yes, `yes_bid` and `yes_ask` per hour, on both the live and the "historical" endpoint (field names differ slightly). | None |
| Candle timestamp marks the END of the hour | Yes. Checked one market against its real trades hour by hour. | None |
| Which field is the scheduled close | `close_time` is overwritten when a market closes early. `expected_expiration_time` holds the scheduled time (for sports, the expected end of the game). | Bug fix: T = `expected_expiration_time` minus 24h. Markets that ended before T are skipped, as PM1 already says. |
| Taker fee 0.07 x C x P x (1-P), rounded up | Confirmed by the API fee type ("quadratic") and secondary fee guides. The rate has a per-series multiplier: 1 for 98.6% of sports markets, 0.5 for 1.4%. | Bug fix: multiply by the series multiplier in force at T (the API has the change history). |
| No settlement fee | Confirmed by secondary guides only. | None |

Open caveat: I can't prove `expected_expiration_time` is never edited after a game is rescheduled. Kalshi keeps no history of that field.

## 3. Funnel (listing fields only)

Pulled series by series. 118 hourly and 15-minute series were skipped (their markets live under 48 hours; none are Sports). Three parlay series in "Exotics" failed at the end of the pull, so Exotics is undercounted.

| Step | Markets |
|---|---|
| Pulled, close on or after 1 Jan 2025 | 16,575,915 |
| Dropped: open less than 48h before scheduled close | 12,176,385 |
| Dropped: closed before the snapshot time T | 1,878,574 |
| Dropped: scheduled close outside 1 Jan 2025 to pull day | 144,473 |
| Kept | 2,376,483 |

## 4. Category counts (distinct events that pass section 4)

| Category | Events | Markets |
|---|---|---|
| Exotics (parlays) | 501,706+ | 1,313,253+ |
| Sports | 164,063 | 855,328 |
| Climate and Weather | 15,211 | 90,250 |
| Entertainment | 3,145 | 32,904 |
| Financials | 1,494 | 26,746 |
| Politics | 1,192 | 5,190 |
| All others | under 1,000 each | |

**Decision needed.** Read literally, PM1 section 5 picks Exotics. Exotics are parlays: each one is a bundle of several sports markets that a user asked to combine (for example "Josh Allen over X AND Joe Burrow over Y"). Each bundle gets its own event ticker, so the count is inflated, the bundles overlap heavily with each other, they only exist since Oct 2025 (99 days), and most have no real order book. I recommend Sports. This is a change to how section 5 is read, made before any result exists, and it needs Amit's OK.

## 5. Sports in detail

- 164,063 events, 855,328 markets, 1,877 series, 578 distinct snapshot days (25 Jan 2025 to 9 Nov 2026).
- Same game under several series (winner, spread, totals, player props): 74,355 distinct games. That is the honest count of independent events. PM1's day-clustered error bars already allow for this, and the report will show both numbers.
- Hidden ladders across event tickers on the same day: none found. The 197 title matches are different games that share a title template (for example "# overtime periods"), each with its own event ticker.
- Growth is steep: about 300 events in Jun 2025, 7,000 a month in early 2026, 34,600 in Oct 2026.

## 6. Holdout problem (decision needed)

PM1 says holdout = newest 25% of events. Because of the growth, that is only 38 days (from 3 Oct 2026), and PM1's pass rule needs 60 distinct days. As written, PM1 cannot pass.

Proposed fix, before any result is read: holdout = newest 25% of snapshot DAYS.

| Split | Holdout starts | Holdout events | Holdout days | Training events | Training days |
|---|---|---|---|---|---|
| PM1 as written (25% of events) | 3 Oct 2026 | 41,042 | 38 | 123,021 | 540 |
| Proposed (25% of days) | 18 Jun 2026 | 107,966 (36,861 games) | 145 | 56,097 | 433 |

## 7. Quote coverage (sample, older markets only)

600 random sports markets with a snapshot before 5 Oct 2026, fixed seed, last candle in the 6 hours before T:

- 478 (80%) had a tradeable quote. 79 had an empty book (bid 0 or ask 1.00), 38 had no candle, 5 sat exactly at 0.50.
- Spread at T: median 3 cents, 75th percentile 8 cents, 90th percentile 29 cents.
- Favourite's entry price: 88 in 0.70-0.80, 81 in 0.80-0.90, 108 in 0.90-0.97, 201 outside the buckets. So roughly 46% of markets would trade.

## 8. Published evidence

Bürgi, Deng and Whelan ("Makers and Takers: The Economics of the Kalshi Prediction Market", 2025) find a favourite-longshot bias on Kalshi: cheap contracts lose badly, expensive ones earn small positive returns. Takers (who buy at the ask, like PM1) do worse than makers (who post a price and wait). I could only read summaries, not the paper's tables.

## 9. My read

The data is good enough to run PM1 honestly. My prior that PM1 fails is stronger than before: a 3 cent typical spread plus about half a cent of fee is a lot to overcome when a 90 cent favourite can earn at most 10 cents. A maker-side version (posting a bid on the favourite instead of paying the ask) is the natural PM2, but free data can't tell us whether a posted order would have filled, so it would need the forward logger. It goes in the queue only with Amit's OK.

## 10. From Amit, 11 Nov 2026

Amit says he has an account and has been told not to worry about tax. Both are recorded as closed on his side.

## Sign-off needed before Step 3

1. Category: Sports (recommended) or Exotics (literal reading).
2. Holdout: newest 25% of days (recommended) or as written.
3. The two bug fixes in section 2.
