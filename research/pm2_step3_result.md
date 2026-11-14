# PM2 test report: Kalshi crypto contracts vs spot lag

Date: 14 Nov 2026. Idea number 2, bar t >= 3.2. Plan: `research/prereg/PM2.md` with Amendment 1 (zero delay primary). Raw output: `research/pm2_step3/`. Scripts: `scripts/pm2_pull_quotes.py`, `scripts/pm2_pull_results.py`, `scripts/pm2_analyze.py`.

## Verdict

**FAIL.** Buying when the spot model says a contract is cheap loses about 0.9 cents per contract after fees on the holdout, t = -3.9. Not a near miss: the sign is wrong.

## Order of work (as pre-registered)

1. Training quotes (1-minute bid/ask, 2.2M markets) and training results pulled.
2. Margin picked on training only and committed before any holdout result was pulled: M = 0.06 (`pm2_step3/margin_lock.json`, commit 13c07be, 19:40 UTC 13 Nov). Training at zero delay: M 0.02 -0.77c, M 0.04 -0.11c, M 0.06 +0.39c (t 1.55).
3. Holdout quotes pulled, holdout funnel committed (commit 6b0bf7b), then holdout results pulled (the script refuses without the lock) and the one test run.

## Holdout funnel (27 May to 12 Nov 2026)

| Step | Markets |
|---|---|
| Markets in holdout | 2,866,025 |
| Dropped: no usable quote in any signal minute (empty book at 0/1, or no candle in 5 minutes) | 2,671,548 |
| Dropped: quote but no spot, volatility or strike | 488 |
| Dropped: quote pull failed | 31 |
| Tradeable | 193,958 |
| Traded at M = 0.06, zero delay | 76,881 markets, 48,704 events, 170 days |

Results: every traded market settled plain yes or no; none dropped. Most markets drop because far strikes sit at 0.99/1.00 or 0/0.01 with no quote changes.

## Primary test (holdout, M = 0.06, zero delay)

| | Value |
|---|---|
| Markets / events / days | 76,881 / 48,704 / 170 |
| Distinct close hours across coins (second sample size) | 4,042 |
| Mean net profit per contract (event level) | -0.0091 dollars |
| Day-clustered t | -3.94 |
| Bootstrap 95% interval (10,000 day resamples) | -0.0135 to -0.0045 |
| Random control mean | -0.0236 |
| Rule minus control | +0.0146 (interval +0.0099 to +0.0192) |

Pass rule: mean above 0 NO, t >= 3.2 NO, interval above 0 NO, beats control YES, sample size YES. Fails on three of five, same pattern as PM1.

## Exploratory (never a pass)

- One-minute delay (the old primary): -2.3 cents, t -11.4. Waiting a minute makes it much worse, so whatever signal exists is gone within a minute.
- 15-minute markets -0.97c (t -3.7), hourly -0.70c (t -2.0).
- By coin: BTC -1.1c, ETH -1.9c, SOL -0.1c, XRP -0.5c. None positive.
- 57% of trades bought NO. Median entry price 22 cents, median 13 minutes before close.

## Dollar check

About 450 trades a day at 10 contracts and -1 cent each: roughly -1,400 dollars a month. Far below the $100 a month floor.

## Why it fails

The simple normal-curve model finds "cheap" contracts, and they are less bad than random ones (beats the control by 1.5 cents), but not by enough to pay the spread and fee. On training the best margin was barely positive (t 1.55), and it didn't hold up on new data. At one minute's delay the gap closes completely, which fits the prior: bots reprice these markets within seconds, and 1-minute free data can't see faster than that.

## Implementation notes (choices made before outcomes, not in the plan text)

- Quote at minute m = close of the latest Kalshi 1-minute candle ending in the 5 minutes up to m (candles only exist when the book changes).
- Volatility uses the sample standard deviation (ddof 1) of 60 one-minute log returns.
- Day = UTC day of the event's first signal minute, as in Step 2. About 417 training markets near the split (closing 00:00 UTC on 27 May) were pulled with the holdout file and so were missing from training; holdout had none missing.
- Random control: for each rule trade, 1,000 draws (seed 12345) from a reservoir sample of all valid (market, minute, side) entries with entry price 0.05 to 0.95 in the same series and close hour, at zero delay, at the ask, with fees.

## Limits

Depth isn't known. Coinbase is not the settlement index. The finest free step is one minute, so a sub-second edge can't be tested with this data.
