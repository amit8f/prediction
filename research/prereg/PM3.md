# PM3 pre-registration: resting (maker) orders that sell cheap YES contracts on Kalshi

Status: DRAFT. Not approved. Waiting for Amit's approval (merge of this PR). No outcome data is pulled until then. Written 14 Nov 2026. Idea number 3, so the pass bar is t >= 3.3.

Where the idea came from: the top pick of the research sweep (`research/idea_sweep_2026-11-13.md`). Amit picked it over weather on a decision card on 14 Nov 2026, 08:19 UTC (option "Maker orders on Kalshi longshots"). Picking the idea is not approval of this plan.

What had been read when this was written: the series list from the 11 Nov pull (categories and fee types only), the field names of one record from Kalshi's `/historical/trades` endpoint (no prices looked at), and the PM1 and PM2 reports. No price, trade or result in the PM3 category has been read. The category isn't picked yet (section 5).

Items marked [VERIFY] are facts to confirm on the live API before the test. Fixing one is a bug fix. Anything else changed after outcomes are read is not allowed.

## 1. Question

In one Kalshi category, does posting a small resting order that sells YES on cheap contracts ("longshots"), one cent better than the best offer, make money after fees, when the fill is judged strictly from the real trade tape and the position is held to settlement?

Jargon. A "maker" posts an order and waits. A "taker" hits an order that's already there and pays the spread. PM1 and PM2 were both taker tests and both lost about the spread. Selling YES at 10 cents is the same as buying NO at 90 cents: we win 10 cents if the event doesn't happen and lose 90 if it does.

## 2. Why it might exist, and why it might not

For it: two large studies of Kalshi trades (Becker, 72 million trades, 2021-2025; Bürgi, Deng and Whelan, "Makers and Takers") find makers earn about +1% and takers about -1%, mostly because takers overpay for cheap YES contracts. PM1 saw the same thing from the other side: prices were fair at the midpoint and the taker lost the spread.

Against: (1) Adverse selection. A resting order fills most often when someone knows more than we do, for example a weather market where the high has already happened. The test uses real trades and real results, so this cost is counted, not assumed away. (2) Those studies average over years. Bots now quote many markets, and the maker edge may be gone in 2026. (3) Selling a 10-cent YES ties up 90 cents of cash until settlement, so a 1-cent edge is only about 1% on the money used. Section 15 checks whether that can reach $100 a month.

My honest prior: more likely to fail than pass.

## 3. Venue

Kalshi. Amit has an account there. Polymarket is not used: its liquidity rewards change often and its trade history needs a separate pull.

## 4. Markets in scope

- Settled binary markets in the chosen category, scheduled close from 1 Jan 2025 to the day of the listing pull. The universe is frozen at that pull.
- Scheduled close = `expected_expiration_time` (PM1 bug fix; `close_time` is overwritten by early closes).
- Excluded: categories Sports and Crypto (their holdouts were spent by PM1 and PM2), Exotics (parlays), and combo markets. Results that aren't plain yes or no use Kalshi's settlement value if reported, else they're dropped and counted.

## 5. Category choice (counts only)

Count distinct events per category from listing fields only (no prices, no trades, no results), among markets that meet section 4. Pick the category with the most distinct events. The counts table goes in the Step 2 report.

Note for Amit: if "Climate and Weather" wins, PM3 spends weather's data, and the weather idea would later need fresh dates.

## 6. The rule (the category's model)

The model is the category's own longshot curve: how often cheap YES contracts actually win compared with their price. It has one tuned number, the price ceiling C (section 8).

1. Snapshot time: the end of the hour 24 hours before scheduled close. If the market opened after that, the end of its first full hour of trading.
2. Quote: `yes_bid` and `yes_ask` from the hourly candle ending at the snapshot (`end_period_ts` = end of the hour, verified in PM1). If there's no candle in the 6 hours up to the snapshot, skip.
3. Eligible if 0.03 <= yes_ask <= C and yes_ask - yes_bid >= 0.02 (room to step inside the spread).
4. Order: sell 10 YES at p = yes_ask - 0.01. That makes us the only order at the new best offer, so we're first in the queue. On Kalshi this is a NO bid at 1 - p.
5. The order rests from the snapshot until 1 hour before scheduled close, then it's cancelled. The price never changes while it rests.
6. One order per market. Every eligible market in an event can get one.

## 7. Fill model and costs

The fill model is the weak point of any maker backtest, so it's strict and fixed now.

- Source: Kalshi's own trade tape (`/markets/trades` and `/historical/trades`, both reachable from here; each trade has `taker_side`, `yes_price_dollars`, `count_fp`, `created_time`, `is_block_trade`).
- Our order fills from trades after the snapshot and before the cancel time where the taker bought YES (`taker_side` = yes) at a YES price >= p. We'd have been first in line at p and better than anything above p, so each such trade would have hit us first.
- Filled amount = running total of those trades' contract counts, capped at 10. Partial fills count as partial.
- Not fills: any trade before the snapshot, any taker sale of YES, block trades.
- Known optimism: our order reaches the exchange 100+ ms late, and our quote might have changed what takers did. Known pessimism: a taker might have hit us at p even where the tape shows no trade at p. Both are small at 10 contracts. The forward logger after a pass measures the real fill rate.

Costs:

- Maker fee charged on every fill, even on series that list no maker fee: 0.0175 x contracts x p x (1 - p), rounded up to the next cent per order. This is the cautious choice. The version using each series' real fee type from `/series/fee_changes` is reported alongside and can't change the verdict. [VERIFY the maker fee formula.]
- No settlement fee. Liquidity rewards and rebates priced at zero.

## 8. Fitting on the training set (the only tuned choice)

Price ceiling C is chosen from {0.10, 0.15, 0.20} on training: the value with the highest event-level mean net profit per filled contract, among values with at least 300 filled events. The choice is committed to the repo before any holdout trade or result is pulled.

## 9. Holdout

The most recent 25% of distinct snapshot days (UTC) in the category. The split date is set from counts alone and written in the Step 2 report. If that gives fewer than 60 days, the split moves earlier until the holdout has 60 days (as PM1 Amendment 1 did). Used once, with the chosen C only.

## 10. Primary test (the only one)

- Per filled order: net profit per contract = p - (1 if the market resolved YES, else 0) - maker fee per contract. Results from Kalshi's reported result.
- Per event: the mean over that event's filled contracts. One number per event with at least one fill. Events with no fill don't enter the mean; the fill rate is reported next to it.
- Primary metric: mean of event-level net profit on the holdout, dollars per contract.
- t-statistic with standard errors clustered by UTC day of scheduled close.
- Bootstrap: resample whole days 10,000 times, 95% interval.

Random control: for each rule order, pick a random market from the same category with a snapshot on the same day and a quote between 0.03 and 0.97 with a spread of at least 2 cents, pick a random side (sell YES or sell NO) one cent inside the spread, and apply the same fill model, window, size and fees. Repeat 1,000 times with a fixed seed. This asks whether selling longshots beats posting orders at random.

## 11. Pass rule

All of these, on the holdout:
1. Mean net profit per contract above 0.
2. Day-clustered t at least 3.3 (the bar for idea number 3).
3. Bootstrap 95% interval entirely above 0.
4. Rule mean above the control mean, with the bootstrap interval of the difference above 0.
5. At least 300 filled events and 60 distinct days. Fewer means "underpowered", not a pass.
6. The dollar check in section 15 plausibly reaches $100 a month. Below that, stop even on a pass.

A pass leads only to a forward logger: paper resting orders tracked against the live order book (needs a Kalshi API key from Amit and the websocket host allowed), recording which would have filled. No real money until that confirms.

## 12. Correlated markets

- Markets in one event (for example a strike ladder on one day's high) collapse to one event number.
- Events on the same day in one category often share a cause (one weather front, one market move). Day clustering covers this. The report also gives the number of distinct days as the plainest effective sample size.

## 13. Data and look-ahead risks

- Data source: Kalshi's public API only. Becker's 36 GB dataset sits on s3.jbecker.dev, which this environment blocks (403), and it stops in 2025, so it isn't needed.
- Pull cost: one hourly-candle call per market before September 2026 (PM2 managed about 70 calls a second) plus the trade tape for each eligible market's window (paginated). Step 2 counts markets and estimates pull time. If the full pull would take over 24 hours, a random sample of whole events is drawn with a fixed seed, at the same rate in training and holdout, decided from counts only and written in the Step 2 report.
- [VERIFY] trade `created_time` is UTC, and no trade from inside the snapshot hour is counted.
- Trade counts can be fractional (`count_fp`). Kept as they are.
- The rule reads nothing after the snapshot except the trade tape for the fill check, and each fill uses only trades that had already happened.

## 14. Exploratory list (never a pass)

Joining the best offer when the spread is 1 cent (fill only on a trade above our price); selling cheap NO contracts; ceilings outside the grid; real per-series maker fees; snapshot 6 hours or 3 days before close; each series alone; time to fill; fill rate by price; the category's calibration curve on all markets.

## 15. Dollar check

Each filled contract ties up 1 - p (about 80 to 97 cents) until settlement. Monthly net = filled contracts per month x net edge per contract.

At 10 contracts per order and a 1-cent net edge, $100 a month needs 10,000 filled contracts a month, about 33 filled orders a day. The capital is rarely the limit (330 contracts a day at ~90 cents is ~$300 a day, freed at settlement). Fills are the limit. The report gives observed filled orders per day on the holdout, the average cash tied up, and the implied monthly net. If that is under $100, it's a stop.

## 16. No LLM features

None are used.
