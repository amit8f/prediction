# PM4 pre-registration: PM3's maker rule, rebuilt for Kalshi Financials

Status: DRAFT. Not approved. Waiting for Amit's approval (merge of this PR). No outcome data is pulled until then. Written 14 Nov 2026. Idea number 4, so the pass bar is t >= 3.4.

Where the idea came from: Amit, 14 Nov 2026: "go PM4 but keep the PM3 its a good result that we can use". PM3 is the only idea so far with a real edge (+1.14c per contract after fees, t = 3.56), and it stopped because it didn't fill enough contracts to make $100 a month. PM4 takes the same idea (rest small orders selling cheap YES, held to settlement) to the category that came second in PM3's count, Financials, with timing built for how Financials markets work. PM3 stays on file as its own result. Its holdout is not reused or counted here.

What had been read when this was written: the slim PM3 listing file (series, category, open, close and expiry times, no prices and no results), the PM1 to PM3 plans and reports, and the 13 Nov idea sweep. No Financials price, quote or trade has been read. One Financials result has been seen: during PM3 Step 2, one settlement value of one S&P 500 hourly market (`KXINXU`) was printed. Its ticker wasn't recorded. It is one market out of about 830,000 in that series and can't steer the rule, but it's disclosed here.

Items marked [VERIFY] are facts to confirm on the live API before the test. Fixing one is a bug fix. Anything else changed after outcomes are read is not allowed.

## 1. Question

In Kalshi's Financials category (stock index, currency and interest-rate range markets), does resting a small order that sells YES on cheap contracts, one cent better than the best offer, make money after fees when fills are judged strictly from the real trade tape and the position is held to settlement? And does it fill enough to make $100 a month on $5,000?

## 2. Why it might exist, and why it might not

For it: PM3 found the maker edge in weather on unseen data, and two large studies of Kalshi trades (Becker; Bürgi, Deng and Whelan) find makers earn about +1% across categories, mostly from takers overpaying for cheap YES. Financials markets trade a lot: the S&P 500 and Nasdaq-100 hourly range series alone list about 1.6 million markets since Jan 2025, against 96,000 for all of weather. If the edge exists here, fill volume, which is what stopped PM3, is much less likely to bind.

Against: (1) Getting picked off. These markets follow a live price (the index or exchange rate). When the index moves toward a strike, fast traders buy that strike's YES from anyone whose offer is stale. PM2 measured exactly this from the taker side: lag picks beat random by 1.5c before costs. A resting order that never moves is the one they hit. The test counts this cost because it uses real trades and real results. (2) Bots quote these series heavily, so the spread may already be 1 cent most of the time, leaving no room to step inside it. (3) PM3's edge faded to about zero in Oct and Nov 2026, which looks like more makers arriving. Financials may be further along that path.

My honest prior: more likely to fail than PM3 did. The pick-off risk is real and Financials is the most bot-heavy category left.

## 3. Venue

Kalshi. Amit has an account there. Polymarket is not used: it has no free history of bids and asks, so there's no way to know where a resting order would have sat.

## 4. Markets in scope

- Settled binary markets in Kalshi category "Financials", scheduled close from 1 Jan 2025 to the day of the listing pull. Universe frozen at that pull.
- Scheduled close = `expected_expiration_time` (PM1 bug fix). Trading end = `close_time`. Markets whose trading ended before the snapshot are dropped and counted (PM3 Step 2 fix).
- Excluded: combo (multivariate) markets. Results that aren't plain yes or no use Kalshi's settlement value if reported, else dropped and counted.
- Why Financials and not another category: counts only. In PM3's Step 2 count (listing fields, no outcomes) Financials was second with 11,090 events after Weather's 15,572. Weather is spent by PM3, Sports by PM1, Crypto by PM2. Commodities lists more raw events but almost all are 15-minute markets that PM3's filter removed; it can be a later idea.

## 5. The rule (Financials' own model)

PM3 placed its order 24 hours before close. That doesn't work here: most Financials markets trade for under 2 hours (15-minute currency and rate markets, hourly index ranges), some for a day, a few for a week. So the timing is set by each market's own life.

1. Snapshot: halfway between `open_time` and trading end (`close_time`), rounded down to the whole minute. For a market that trades longer than 48 hours, the snapshot is 24 hours before trading end instead (same as PM3).
2. Quote: `yes_bid` and `yes_ask` from the 1-minute candle ending at the snapshot. If there's no candle in the 30 minutes up to the snapshot, skip and count it. [VERIFY that 1-minute candles exist for settled historical markets; PM2 used them for crypto.]
3. Eligible if 0.03 <= yes_ask <= C and yes_ask - yes_bid >= 0.02.
4. Order: sell 10 YES at p = yes_ask - 0.01 (a NO bid at 1 - p). We are alone at the new best offer, so first in the queue.
5. The order rests from the snapshot to trading end. The price never changes.
6. One order per market. Every eligible market in an event can get one.

The model is Financials' own longshot curve, with one tuned number, the price ceiling C (section 7).

## 6. Fill model and costs (same as PM3)

- Source: Kalshi's trade tape (`/markets/trades`, `/historical/trades`).
- Our order fills from trades strictly after the snapshot minute and before trading end where the taker bought YES (`taker_side` = yes, which PM3 Step 3 confirmed means the taker bought YES) at a YES price >= p. Running total of their contract counts, capped at 10. Partial fills count as partial.
- Not fills: trades at or before the snapshot minute, taker sales of YES, block trades.
- Known optimism: our order would arrive 100+ ms late and might change what takers do. Known pessimism: a taker could have hit us where the tape shows no trade. Only a live logger can measure these.
- Maker fee on every fill, whatever the series' fee type: 0.0175 x contracts x p x (1 - p), rounded up to the next cent per order. The real per-series fee is reported alongside and can't change the verdict.
- No settlement fee. Liquidity rewards and rebates priced at zero.

## 7. Fitting on training (the only tuned choice)

C from {0.10, 0.15, 0.20}: the value with the highest event-level mean net profit per filled contract on training, among values with at least 300 filled events; ties go to the higher C (PM3 practice). Committed to the repo before any holdout quote, trade or result is pulled.

## 8. Holdout

The most recent 25% of distinct snapshot days (UTC). The split date is set from counts alone in the Step 2 report. Minimum 60 days. Used once, with the locked C.

## 9. Primary test (the only one)

- Per filled order: net per contract = p - (1 if YES won, else 0) - maker fee per contract.
- Per event: mean over the event's filled contracts. One number per event with a fill. Fill rate reported alongside.
- Primary metric: mean of event-level net profit on the holdout, dollars per contract.
- t-statistic with standard errors clustered by UTC day of scheduled close.
- Bootstrap: resample whole days 10,000 times, 95% interval.

Random control: for each rule order, a random Financials market with a snapshot on the same day and a quote between 0.03 and 0.97 with a spread of at least 2 cents, a random side (sell YES or sell NO) one cent inside the spread, same fill model, window, size and fees. 1,000 repeats, fixed seed.

## 10. Pass rule

All of these, on the holdout:
1. Mean net profit per contract above 0.
2. Day-clustered t at least 3.4 (idea number 4).
3. Bootstrap 95% interval above 0.
4. Rule beats the control, difference interval above 0.
5. At least 300 filled events and 60 distinct days, else "underpowered".
6. The dollar check (section 13) plausibly reaches $100 a month from PM4 alone. Below that, stop even on a pass. PM3 plus PM4 together is reported next to it and doesn't count.

A pass leads only to a forward logger (paper resting orders against the live order book; needs a Kalshi API key from Amit and the websocket host allowed). No real money until that confirms.

## 11. Correlated markets

- All strikes of one event (for example every range of one S&P hour) collapse to one event number.
- Events on the same day move together (the S&P, the Nasdaq-100 and the Dow share every market move; many hourly events share one day). Day clustering covers this, and the report gives distinct days as the plainest effective sample. The report also gives the number of distinct (series family, hour) slots.

## 12. Data and look-ahead risks

- Pull size is the main practical problem. About 2.5 million Financials markets, each needing one candle call (about 70 a second before Sep 2026), plus trades for eligible ones. Step 2 estimates the pull time from counts. If it's over 24 hours, a random sample of whole events is drawn with a fixed seed, at the same rate in training and holdout, decided from counts only and written in the Step 2 report. Most strikes in an hourly index event sit far from the price with no quote; markets without a candle in the window cost one call and are skipped.
- [VERIFY] trade `created_time` and candle times are UTC, and the candle ending at the snapshot minute only holds quotes from before it.
- The rule reads nothing after the snapshot except the trade tape for fills, and each fill uses only trades that already happened.
- Trade counts can be fractional (`count_fp`). Kept as they are.

## 13. Dollar check

Monthly net = filled contracts per month x net edge per contract. At 10 contracts per order and a 1-cent edge, $100 a month needs about 10,000 filled contracts a month. Each filled contract ties up 1 - p (80 to 97 cents) until settlement, but Financials markets mostly settle within hours, so the same cash turns over several times a day. The report gives observed filled contracts per day, peak cash tied up at once, and implied monthly net. Under $100 is a stop.

## 14. Exploratory list (never a pass)

Each series family alone (index hourly, index daily, currency, rates); fill rate and edge by time of day; the snapshot a quarter or three quarters of the way through a market's life; joining the best offer when the spread is 1 cent; selling cheap NO; real per-series fees; edge by month; how often our order was filled within a minute of a big index move (a direct measure of being picked off).

## 15. No LLM features

None are used.

## 16. Runner-up, not chosen

Late-day weather: buy at the ask only when the station's readings already show the day's high has passed a strike and the market hasn't caught up. It's a different mechanism from PM1-PM3 and doesn't depend on the maker edge, but weather data up to 13 Nov is spent by PM3, so it can only be tested on dates still to come (a forward logger running a couple of months first). If Amit prefers it, this plan is replaced by a weather plan before any data is pulled.
