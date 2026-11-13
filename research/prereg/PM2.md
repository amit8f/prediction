# PM2 pre-registration: buying Kalshi crypto contracts when they lag the spot price

Status: APPROVED by Amit on 13 Nov 2026 (merge of PR #4, 07:54 UTC). Amendment 1 (section 17) APPROVED by Amit on 13 Nov 2026 (merge of PR #5, 07:57 UTC). Written 13 Nov 2026. Idea number 2, so the pass bar is t >= 3.2.

What had been read when this was written: series listings (from the 11 Nov pull), the rules text of a few open crypto markets, the field names of one settled market's 1-minute candles (no prices printed), and two live minutes of one open market's quotes. No settled crypto price, no crypto result, and no historical spot price had been read.

Items marked [VERIFY] are facts to confirm on the live API before the test. Fixing one of them is a bug fix. Anything else changed after outcomes are read is not allowed.

## 1. Question

On Kalshi's short-term crypto "above/below" markets, does buying a side at the ask, only when a simple spot-price model says it's worth more than the ask plus the fee, make money after costs when held to settlement?

Jargon: "spot" is the price of the coin itself on an exchange right now. A "lag" is when the Kalshi price hasn't caught up with a move in spot yet.

## 2. Why it might exist, and why it probably doesn't

These markets settle on a formula of the coin's price at a known minute. If spot jumps and the Kalshi quote takes a while to move, the quote is stale and a buyer at the ask could be getting a good price. Retail traders on Kalshi set many of these quotes by hand.

Reasons to doubt it: professional market makers quote these markets with bots that read spot every second, so most lags probably last seconds, not minutes. Our free data is 1-minute candles, so we can only catch lags that last over a minute. The fee is largest near 50 cents (about 1.75 cents per contract). My honest prior is that this fails. A fail is a useful answer.

## 3. Venue and markets

Kalshi. Series (all settle on CF Benchmarks real-time indexes, fee type quadratic, multiplier 1 in the 11 Nov listing):

- Hourly above/below: KXBTCD, KXETHD, KXSOLD, KXXRPD.
- 15-minute up/down: KXBTC15M, KXETH15M, KXSOL15M, KXXRP15M. These pay YES if the 60-second average at close is at least the 60-second average at open.

Range series (KXBTC, KXETH, ...) and daily, weekly and longer series are excluded from the primary test.

## 4. Data and period

- Kalshi: settled-market listings for the eight series (regular and historical endpoints), and 1-minute candles with yes_bid and yes_ask. Verified on 13 Nov 2026 that historical 1-minute candles exist with bid and ask fields.
- Spot: Coinbase public 1-minute candles for BTC-USD, ETH-USD, SOL-USD, XRP-USD (Coinbase is one of the exchanges in the CF index). Binance's free bulk files are a backup only if Coinbase has gaps; any use is counted in the funnel.
- Period: every market in the eight series with a scheduled close from 1 Jan 2025 (or the series' first market, if later) to the day of the listing pull. The universe is frozen at that pull. Later markets are new data, saved for the forward logger.
- Count of events and days per series goes in the funnel report before any price after a market's open is read.

## 5. The model (crypto-specific, fixed in advance, nothing fitted)

At signal minute m, with spot S (Coinbase close of the minute ending at m), strike K, and minutes left to settlement tau:

    fair YES price = N( ln(S / K) / (sigma x sqrt(tau)) )

- N is the standard normal curve. No drift.
- sigma = standard deviation of the 60 one-minute log returns of spot ending at m. Only data up to m is used.
- tau = minutes from m to the scheduled close, minus 0.5 (the settlement price is a 60-second average, so its centre is 30 seconds before close).
- Hourly markets: K = the market's strike (floor_strike). "Above" and "at least" are treated the same.
- 15-minute markets: K = the opening reference, taken as the mean of Coinbase spot over the minute before the market's open. Signals start only after that minute is complete.
- Skip if sigma is 0 or any of the 60 spot minutes is missing.

## 6. Entry rule

- Signal minutes: every minute from (scheduled close minus 55 minutes) to (scheduled close minus 2 minutes) for hourly markets, and from (open plus 1 minute) to (close minus 2 minutes) for 15-minute markets. Settlement time = the time in the rules text ("before 3 AM EST"). On the open markets checked it matched `close_time`, while `expected_expiration_time` was 5 minutes later. [VERIFY that `close_time` equals the rules-text time on settled markets; if not, parse the rules text. A bug fix either way.]
- Execution delay of one minute: the model uses spot at minute m, and we buy at the Kalshi ask from the candle ending at m + 1. This assumes we can't act faster than the data we have.
- Kalshi quote = the close of yes_bid and yes_ask in the 1-minute candle ending at m + 1. If there is no candle in the 5 minutes up to m + 1, or bid is 0, or ask is 1.00, skip that minute.
- YES edge = fair - yes_ask - fee per contract. NO edge = (1 - fair) - (1 - yes_bid) - fee per contract.
- Buy the side whose edge is larger, if that edge is above the margin M (section 8) and the entry price is between 0.05 and 0.95.
- One trade per market: the first minute that fires. Size 10 contracts. Hold to settlement.

## 7. Costs

- Taker fee: 0.07 x fee multiplier x contracts x P x (1 - P), rounded up to the next cent, where P is the entry price. Multiplier in force at the entry time from `/series/fee_changes` [VERIFY no crypto-specific schedule].
- No settlement fee. Spread paid in full (buy at the ask).
- Depth unknown. Ten contracts at the best quote is assumed fillable.

## 8. Fitting on the training set (the only tuned choice)

Margin M is chosen from {0.02, 0.04, 0.06} on training: the value with the highest event-level mean net profit, among values with at least 300 traded events. Nothing else is tuned. The choice is committed before the holdout is read.

## 9. Holdout

The most recent 25% of distinct snapshot days (UTC days on which the market's first signal minute falls), pooled over the eight series. The split date is fixed from counts alone and written in the funnel report before any price after a market's open is read. Used once, with the chosen M only. Crypto data has not been used by PM1, so none of it is spent.

## 10. Primary test (the only one)

- Per market: net profit per contract = payout (1 if our side wins, else 0) - entry price - fee per contract. Payout from Kalshi's reported result, not from our spot.
- Per event: the mean over that event's traded markets (an hourly event is one coin and one hour, with many strikes). One number per event.
- Primary metric: mean of event-level net profit on the holdout, in dollars per contract.
- t-statistic with standard errors clustered by UTC calendar day.
- Bootstrap: resample whole days, 10,000 times, 95% interval.

Random control: for each rule trade, take a random eligible market from the same series and same close hour, a random signal minute in its window, and a random side, bought at the ask with the same delay and fees. Repeat 1,000 times with a fixed seed.

## 11. Pass rule

All of these, on the holdout:
1. Mean net profit per contract above 0.
2. Day-clustered t at least 3.2 (the bar for idea number 2).
3. Bootstrap 95% interval entirely above 0.
4. Rule mean above the control mean, with the bootstrap interval of the difference above 0.
5. At least 300 events and 60 distinct days. Fewer means "underpowered", which is not a pass.

A pass leads only to a forward logger (recording live quotes and spot every few seconds) and the dollar check in section 15. No real money until the logger confirms.

## 12. Correlated markets

- Strikes in one hourly event collapse into one event number.
- BTC, ETH, SOL and XRP move together, so the same hour across coins is correlated. Day clustering covers this. The report also gives the count of distinct close hours across coins as a second effective sample size.
- 15-minute markets and the hourly market closing at the same time are separate events but share a day cluster.

## 13. Resolution and data risks

- Our spot (Coinbase) isn't the settlement index (CF Benchmarks average of several exchanges). The model may be slightly off near the strike. That only hurts the rule, it can't fake a profit, because payouts come from Kalshi's results.
- Voided or non-yes/no results: settlement value if Kalshi reports one, else dropped. Counted in the funnel.
- Coinbase candle timestamps mark the START of the minute [VERIFY]. If so, "spot at m" is the close of the candle starting at m - 1 minute. Getting this wrong would be look-ahead, so it is checked first.
- Kalshi candle `end_period_ts` marks the end of the minute (verified for hourly candles in PM1; [VERIFY] for 1-minute).

## 14. Exploratory list (never a pass)

Zero delay (spot and quote from the same minute); two-minute delay; each coin and each series type alone; range series; margins outside the grid; Binance spot instead of Coinbase; time of day; the model's calibration on all minutes (not just trades).

## 15. Scale check

Fees near 50 cents are about 1.75 cents per contract, so an edge has to beat that first. If the net edge were 2 cents per contract, $100 a month needs 5,000 contracts a month, about 170 a day, for example 17 markets a day at 10 contracts. Each coin has 24 hourly events (each with many strikes) and 96 fifteen-minute markets a day, so trade count isn't the limit. Depth at the best quote is the limit and it's unknown. The forward logger would record it.

## 16. No LLM features

None are used.

## 17. Amendment 1 (13 Nov 2026, asked for by Amit, before any outcome data was read)

Amit asked for all four coins (no change) and for the smallest delay possible. At this point no settled crypto price, no crypto result and no historical spot price had been read. Where this section differs from the text above, this section wins.

1. Delay (section 6): the primary test uses zero delay. The model uses spot up to minute m, and we buy at the Kalshi quote from the 1-minute candle ending at the same minute m. One minute is the finest step in the free history, so this is the smallest delay that can be tested.
2. What zero delay means: it assumes an order placed the instant the minute ends. A real bot needs about 0.2 to 1 second, so the result is a best case. It is not look-ahead, because the spot price and the quote are both known at minute m. [VERIFY that Coinbase and Kalshi minute boundaries line up to the second. If a spot candle can include any trade after m, shift spot back one minute. That is a bug fix.]
3. The one-minute-delay version (the old primary) moves to the exploratory list and is always reported next to the primary. It cannot produce a pass or a fail. If zero delay passes and one minute does not, the report says plainly that the edge needs a fast bot.
4. Forward logger (section 11): after a pass, the logger records Kalshi quotes and spot at least once a second, and replays the rule with delays of 0.5, 1, 2 and 5 seconds. Real money is discussed only if the edge survives a delay we can really achieve.
5. Random control (section 10): uses zero delay too.
6. Nothing else changes: same markets, model, margin grid, holdout, bar (t >= 3.2) and pass rule.

