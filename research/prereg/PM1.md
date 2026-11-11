# PM1 pre-registration: buying favourites 24 hours before close

Status: APPROVED by Amit on 11 Nov 2026 (18:05 UTC), including Kalshi as the venue. Written 11 Nov 2026. Idea number 1. No market data of any kind had been pulled when this was written.

Items marked [VERIFY] are facts to confirm against the live API before approval. Fixing one of them is a bug fix. Changing anything else after outcomes are read is not allowed.

## 1. Question

On Kalshi, in one category, does buying the favourite side at the ask about 24 hours before the scheduled close, and holding to settlement, make money after fees?

Jargon: the "favourite" is the side the market thinks is more likely. The "ask" is the price you pay to buy right now. The "bid" is the price you get if you sell right now.

## 2. Why it might exist, and why it probably doesn't

The favourite-longshot bias is an old finding in betting: people overpay for cheap long shots, so the likely side is slightly underpriced. Retail traders like lottery-style payoffs, and tying up 90 cents for a day to make 1 or 2 cents is dull work.

Reasons to doubt it: market makers know this bias, the spread near 90 to 97 cents can be as large as the edge, and fees take the rest. My honest prior is that this fails. A fail is a useful answer.

## 3. Venue

Kalshi. This is a change from "Polymarket first" and needs Amit's OK. Reason: Kalshi's free candle data carries the bid and the ask [VERIFY on a live sample]. Polymarket's free price history is last-trade or midpoint, which our fill rule bans, and Amit's own data-QA notes say Polymarket backtests are unproven until checked against live books. Step 1 found Israel on neither platform's restricted list. Kalshi signup with an Israeli ID is still untested.

Fees are similar on both now. Polymarket's docs give a taker fee of shares x rate x p x (1 - p), with rate 0.04 to 0.07 by category.

## 4. Universe and period

- All Kalshi binary markets whose scheduled close is between 1 Jan 2025 and the day of the data pull, taken from the settled-market listings (the regular and the "historical" endpoints), including voided markets.
- The market must have been open at least 48 hours before its scheduled close.
- One category only, chosen in section 5.

## 5. Category choice (counts only)

Count distinct events per category, using only listing fields (no prices, no results). Pick the category with the most distinct events that pass section 4. Record the counts table in the funnel report. My guess is sports.

## 6. Entry rule

- Snapshot time T = scheduled close minus 24 hours. Use the scheduled close field, not the actual settlement time [VERIFY which API field holds the schedule and that it isn't overwritten on early close].
- Use the last hourly candle that ends at or before T [VERIFY candle timestamps mark the END of the period].
- Skip the market if it had already closed by T, if either the bid or the ask is missing, if the bid is 0, or if the ask is 1.00.
- Favourite side: YES if the midpoint is above 0.50, NO if below, skip if exactly 0.50.
- Entry price = the ask for that side. For NO, that is 1 minus the YES bid.
- Trade only if the entry price falls inside the chosen bucket (section 8).
- Size: 10 contracts per market. Hold to settlement. No exit before that.

## 7. Costs

- Kalshi taker fee for the order: 0.07 x contracts x P x (1 - P), rounded up to the next cent, where P is the entry price [VERIFY against the current fee schedule, including any series with a different rate]. Per-contract fee = that amount divided by 10.
- No settlement fee assumed [VERIFY].
- The spread is paid in full because we buy at the ask.
- Depth is unknown. Ten contracts at the best quote is assumed fillable. Capacity beyond that is an open question.

## 8. Fitting on the training set

The training set is the oldest 75% of events by scheduled close. On it, compute the primary metric for three buckets of entry price: 0.70 to 0.80, 0.80 to 0.90, 0.90 to 0.97. Pick the bucket with the highest mean. Nothing else is tuned.

## 9. Holdout

The most recent 25% of events by scheduled close. The split date is fixed from counts alone and written in the funnel report before any result field is read. The holdout is used once, for the chosen bucket only.

## 10. Primary test (the only one)

- Per market: net profit per contract = payout (1 if the favourite side wins, else 0) minus entry price minus fee per contract.
- Per event: the mean over that event's traded markets. One number per event.
- Primary metric: the mean of event-level net profit on the holdout, in dollars per contract.
- t-statistic with standard errors clustered by calendar day of the snapshot (UTC).
- Bootstrap: resample whole days, 10,000 times, 95% interval.

Random control: for each rule trade, draw one random eligible market from the same category with a snapshot on the same day (any price), buy a random side at its ask, same fees. Repeat 1,000 times with a fixed seed. The control mean is the average over draws.

## 11. Pass rule

All of these, on the holdout:
1. Mean net profit per contract is above 0.
2. Day-clustered t is at least 3.0 (the bar for idea number 1).
3. The bootstrap 95% interval is entirely above 0.
4. The rule's mean is above the control's mean, and the bootstrap interval of the difference is above 0.
5. At least 300 independent events and 60 distinct days. Fewer means "underpowered", which is not a pass.

A pass leads only to a proposal for a forward logger. Then the dollar floor is checked (section 15).

## 12. Correlated markets

- Markets sharing a Kalshi event are collapsed into one event-level number.
- Title fingerprint sweep from the data-QA skill: replace numeric thresholds with '#', group, and treat any ladder that spans several event tickers as one event.
- For ladders, check that the bucket prices at the snapshot sum to about 1.00. Ladders far above that are dropped as bad quotes and counted in the funnel.
- Report: markets, events, days, and the effective sample size (events, and days as the cluster count).

## 13. Resolution risk

- Markets that settled before T: no trade.
- Markets that settle between T and the scheduled close: held and counted normally.
- Voided markets or results other than yes/no: counted at the settlement value Kalshi reports if there is one, otherwise dropped. Both counts go in the funnel. Exploratory line: the same test with those markets counted as total losses.
- Kalshi has no public dispute flag that I know of. That limitation is stated in the result.

## 14. Exploratory list (never a pass)

The other two buckets; the longshot side; snapshots at 1, 6 and 72 hours; splits by series and by spread size; the same rule on Polymarket prices.

## 15. Scale check

If the edge were 1 cent per contract, $100 a month needs about 10,000 contracts a month. That is roughly 330 a day, or about $300 staked a day, for example 30 markets at 10 contracts each. Capital is not the limit, because stakes come back within a day or two. Depth is the limit and it's unknown, so a pass would still need the forward logger to record how many contracts sit at the best quote. Israeli tax treatment (see the Step 1 report) could turn a small edge into a loss and needs a professional before real money.

## 16. No LLM features

None are used, so the model-cutoff rule doesn't apply to PM1.
